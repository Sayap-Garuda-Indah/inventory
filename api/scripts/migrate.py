import argparse
import hashlib
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config import settings  # noqa: E402
from db.pool import init_pool, get_conn  # noqa: E402


MIGRATION_FILENAME_RE = re.compile(r"^(?P<version>\\d{4})_(?P<name>[A-Za-z0-9._-]+)\\.sql$")


@dataclass(frozen=True)
class MigrationFile:
    version: int
    name: str
    path: Path
    checksum: str


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_migrations(migrations_dir: Path) -> list[MigrationFile]:
    if not migrations_dir.exists():
        raise FileNotFoundError(f"Migrations directory not found: {migrations_dir}")

    migrations: list[MigrationFile] = []
    for child in sorted(migrations_dir.iterdir(), key=lambda p: p.name):
        if not child.is_file() or child.suffix.lower() != ".sql":
            continue
        match = MIGRATION_FILENAME_RE.match(child.name)
        if not match:
            raise ValueError(
                f"Invalid migration filename: {child.name}. Expected: 0001_description.sql"
            )
        version = int(match.group("version"))
        name = match.group("name")
        sql = child.read_text(encoding="utf-8")
        checksum = _sha256(sql)
        migrations.append(MigrationFile(version=version, name=name, path=child, checksum=checksum))

    versions = [m.version for m in migrations]
    if len(versions) != len(set(versions)):
        raise ValueError("Duplicate migration versions detected.")

    return migrations


def _connect():
    init_pool()
    # Returns a PyMySQL connection via our existing pool implementation.
    conn = get_conn()
    conn.autocommit(False)
    return conn


def _wait_for_db(timeout_seconds: int, poll_seconds: float) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            conn = _connect()
            conn.close()
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(poll_seconds)

    raise RuntimeError(f"Database not reachable after {timeout_seconds}s: {last_error}")


def _ensure_migrations_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
          version INT NOT NULL PRIMARY KEY,
          name VARCHAR(200) NOT NULL,
          checksum CHAR(64) NOT NULL,
          applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """
    )


def _get_applied(cursor) -> dict[int, str]:
    cursor.execute("SELECT version, checksum FROM schema_migrations ORDER BY version")
    rows = cursor.fetchall()
    applied: dict[int, str] = {}
    for row in rows:
        applied[int(row["version"])] = str(row["checksum"])
    return applied


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
        """,
        (settings.DB_NAME, table_name),
    )
    row = cursor.fetchone()
    return bool(row and int(row["cnt"]) > 0)


def _execute_sql_script(cursor, sql: str) -> None:
    cursor.execute(sql)
    while cursor.nextset():
        pass


def _apply_migration(cursor, migration: MigrationFile) -> None:
    sql = migration.path.read_text(encoding="utf-8")
    _execute_sql_script(cursor, sql)
    cursor.execute(
        """
        INSERT INTO schema_migrations (version, name, checksum)
        VALUES (%s, %s, %s)
        """,
        (migration.version, migration.name, migration.checksum),
    )


def cmd_upgrade(args: argparse.Namespace) -> int:
    migrations_dir = Path(args.dir).resolve()
    migrations = _load_migrations(migrations_dir)

    _wait_for_db(timeout_seconds=args.wait, poll_seconds=args.poll)

    conn = _connect()
    try:
        with conn.cursor() as cursor:
            _ensure_migrations_table(cursor)
            applied = _get_applied(cursor)

            # Adoption path: existing DB created from legacy `schema.sql` has tables
            # but no `schema_migrations` entries. If so, mark the baseline migration
            # as applied so we can start versioned migrations without re-creating tables.
            if not applied and migrations and migrations[0].version == 1:
                if _table_exists(cursor, "users"):
                    cursor.execute(
                        """
                        INSERT INTO schema_migrations (version, name, checksum)
                        VALUES (%s, %s, %s)
                        """,
                        (migrations[0].version, migrations[0].name, migrations[0].checksum),
                    )
                    conn.commit()
                    applied = _get_applied(cursor)

            pending = [m for m in migrations if m.version not in applied]

            for m in migrations:
                if m.version in applied and applied[m.version] != m.checksum:
                    raise RuntimeError(
                        f"Checksum mismatch for migration {m.path.name}. "
                        f"DB has {applied[m.version]}, file has {m.checksum}."
                    )

            if args.dry_run:
                for m in pending:
                    print(f"[dry-run] would apply {m.path.name}")
                return 0

            for m in pending:
                print(f"Applying {m.path.name}...")
                _apply_migration(cursor, m)
                conn.commit()

            print(f"Done. Applied {len(pending)} migration(s).")
            return 0
    except Exception:  # noqa: BLE001
        conn.rollback()
        raise
    finally:
        conn.close()


def cmd_status(args: argparse.Namespace) -> int:
    migrations_dir = Path(args.dir).resolve()
    migrations = _load_migrations(migrations_dir)

    _wait_for_db(timeout_seconds=args.wait, poll_seconds=args.poll)

    conn = _connect()
    try:
        with conn.cursor() as cursor:
            _ensure_migrations_table(cursor)
            applied = _get_applied(cursor)

        for m in migrations:
            state = "APPLIED" if m.version in applied else "PENDING"
            print(f"{state}\t{m.path.name}")
        return 0
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Database migration runner (SQL files)")
    parser.add_argument(
        "--dir",
        default=str(PROJECT_ROOT / "db" / "migrations"),
        help="Migrations directory (default: api/db/migrations)",
    )
    parser.add_argument("--wait", type=int, default=int(os.getenv("DB_WAIT_SECONDS", "60")))
    parser.add_argument("--poll", type=float, default=float(os.getenv("DB_POLL_SECONDS", "1.0")))

    sub = parser.add_subparsers(dest="command", required=True)

    p_upgrade = sub.add_parser("upgrade", help="Apply pending migrations")
    p_upgrade.add_argument("--dry-run", action="store_true", help="Print pending migrations without applying")
    p_upgrade.set_defaults(func=cmd_upgrade)

    p_status = sub.add_parser("status", help="Show migration status")
    p_status.set_defaults(func=cmd_status)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

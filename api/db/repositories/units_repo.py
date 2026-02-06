from typing import Optional, List, Dict, Any
import pymysql as MySQLdb
from db.pool import fetch_all, fetch_one, execute, get_db_transaction
from db.base import QueryBuilder, DatabaseUtils
from schemas.units import UnitCreate, UnitUpdate


class UnitsRepository:
    DELETED_NAME_PREFIX = "__deleted__"
    FALLBACK_UNIT_NAME = "-"
    FALLBACK_UNIT_SYMBOL = "-"
    FALLBACK_UNIT_MULTIPLIER = 1

    @staticmethod
    def get_all(
        limit: int = 100,
        offset: int = 0,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            conditions = ["name NOT LIKE %s"]
            params = [f"{UnitsRepository.DELETED_NAME_PREFIX}%"]

            search_term = DatabaseUtils.sanitize_search_term(search)
            search_condition, search_params = QueryBuilder.build_search_condition(search_term, ["name", "symbol"])
            if search_condition:
                conditions.append(search_condition)
                params.extend(search_params)
            
            where_clause, params = QueryBuilder.build_where_clause(conditions, params)
           
            query = f"""
                SELECT id, name, symbol, multiplier
                FROM units
                {where_clause}
                ORDER BY name
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            rows = fetch_all(query, tuple(params))

            return rows
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def count(search: Optional[str] = None) -> int:
        try:
            conditions = ["name NOT LIKE %s"]
            params = [f"{UnitsRepository.DELETED_NAME_PREFIX}%"]

            search_term = DatabaseUtils.sanitize_search_term(search)
            search_condition, search_params = QueryBuilder.build_search_condition(search_term, ["name", "symbol"])
            if search_condition:
                conditions.append(search_condition)
                params.extend(search_params)
            
            where_clause, params = QueryBuilder.build_where_clause(conditions, params)
           
            query = f"""
                SELECT COUNT(*) AS count
                FROM units
                {where_clause}
            """
            row = fetch_one(query, tuple(params))

            return row['count'] if row else 0
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def get_by_id(unit_id: int) -> Optional[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_id(unit_id, "Unit")
            query = "SELECT * FROM units WHERE id = %s AND name NOT LIKE %s"
            row = fetch_one(query, (unit_id, f"{UnitsRepository.DELETED_NAME_PREFIX}%"))
            
            return row
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def get_by_name(name: str) -> Optional[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_string(name, "name")
            
            query = "SELECT * FROM units WHERE name = %s AND name NOT LIKE %s"
            row = fetch_one(query, (name, f"{UnitsRepository.DELETED_NAME_PREFIX}%"))

            return row
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def get_by_symbol(symbol: str) -> Optional[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_string(symbol, "symbol")
            
            query = "SELECT * FROM units WHERE symbol = %s AND name NOT LIKE %s"
            row = fetch_one(query, (symbol, f"{UnitsRepository.DELETED_NAME_PREFIX}%"))

            return row
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def get_or_create_fallback_unit() -> Dict[str, Any]:
        try:
            fallback = UnitsRepository.get_by_name(UnitsRepository.FALLBACK_UNIT_NAME)
            if fallback:
                return fallback

            query = """
                INSERT INTO units (name, symbol, multiplier)
                VALUES (%s, %s, %s)
            """
            execute(
                query,
                (
                    UnitsRepository.FALLBACK_UNIT_NAME,
                    UnitsRepository.FALLBACK_UNIT_SYMBOL,
                    UnitsRepository.FALLBACK_UNIT_MULTIPLIER,
                ),
            )

            fallback = UnitsRepository.get_by_name(UnitsRepository.FALLBACK_UNIT_NAME)
            if not fallback:
                raise RuntimeError("Failed to create fallback unit '-'")

            return fallback
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def get_item_usage_count(unit_id: int) -> int:
        try:
            DatabaseUtils.validate_id(unit_id, "Unit")

            query = "SELECT COUNT(*) AS count FROM items WHERE unit_id = %s"
            result = fetch_one(query, (unit_id,))
            if not result:
                return 0

            return int(result["count"])
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def soft_delete_and_reassign(unit_id: int) -> Dict[str, Any]:
        try:
            DatabaseUtils.validate_id(unit_id, "Unit")

            fallback_unit = UnitsRepository.get_or_create_fallback_unit()
            fallback_id = int(fallback_unit["id"])

            if fallback_id == unit_id:
                raise RuntimeError("Fallback unit '-' cannot be deleted.")

            with get_db_transaction() as connection:
                cursor = connection.cursor(MySQLdb.cursors.DictCursor)
                try:
                    cursor.execute(
                        """
                        SELECT id, name, symbol
                        FROM units
                        WHERE id = %s AND name NOT LIKE %s
                        FOR UPDATE
                        """,
                        (unit_id, f"{UnitsRepository.DELETED_NAME_PREFIX}%"),
                    )
                    target_unit = cursor.fetchone()
                    if not target_unit:
                        raise RuntimeError(f"Unit with id {unit_id} not found")

                    cursor.execute(
                        "SELECT COUNT(*) AS count FROM items WHERE unit_id = %s FOR UPDATE",
                        (unit_id,),
                    )
                    usage_row = cursor.fetchone()
                    affected_items = int(usage_row["count"]) if usage_row else 0

                    if affected_items > 0:
                        cursor.execute(
                            "UPDATE items SET unit_id = %s WHERE unit_id = %s",
                            (fallback_id, unit_id),
                        )

                    deleted_name = f"{UnitsRepository.DELETED_NAME_PREFIX}{unit_id}"
                    cursor.execute(
                        "UPDATE units SET name = %s WHERE id = %s",
                        (deleted_name, unit_id),
                    )

                    if cursor.rowcount <= 0:
                        raise RuntimeError("Failed to soft delete unit")
                finally:
                    cursor.close()

            return {
                "deleted_unit_id": unit_id,
                "deleted_unit_name": target_unit["name"],
                "deleted_unit_symbol": target_unit["symbol"],
                "reassigned_items": affected_items,
                "replacement_unit_name": fallback_unit["name"],
                "replacement_unit_id": fallback_id,
            }
        except Exception as e:
            raise RuntimeError({str(e)})

        
    @staticmethod
    def create(unit_data: UnitCreate) -> Dict[str, Any]:
        try:
            query = """
                INSERT INTO units (name, symbol, multiplier)
                VALUES (%s, %s, %s)
            """
            execute(query, (unit_data.name, unit_data.symbol, unit_data.multiplier))

            create_unit = UnitsRepository.get_by_name(unit_data.name)
            if not create_unit:
                raise RuntimeError("Failed to retrieve the newly created unit.")
            
            return create_unit
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def update(unit_id: int, unit_data: UnitUpdate) -> Optional[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_id(unit_id, "Unit")
            
            # Dynamic update query
            set_clause = []
            params = []

            if unit_data.name is not None:
                set_clause.append("name = %s")
                params.append(unit_data.name)

            if unit_data.symbol is not None:
                set_clause.append("symbol = %s")
                params.append(unit_data.symbol)

            if unit_data.multiplier is not None:
                set_clause.append("multiplier = %s")
                params.append(unit_data.multiplier)

            if not set_clause:
                # Nothing to update
                unit = UnitsRepository.get_by_id(unit_id)
                return unit

            params.append(unit_id)
            query = f"""
                UPDATE units
                SET {', '.join(set_clause)}
                WHERE id = %s
            """

            rows_affected = execute(query, tuple(params))

            if rows_affected > 0:
                return UnitsRepository.get_by_id(unit_id)
            
            return None
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def delete(unit_id: int) -> bool:
        try:
            result = UnitsRepository.soft_delete_and_reassign(unit_id)
            return bool(result)
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def exists_by_name(name: str, exclude_id: Optional[int] = None) -> bool:
        try:
            DatabaseUtils.validate_string(name, "name")
            if exclude_id is not None:
                DatabaseUtils.validate_id(exclude_id, "Unit")
            if exclude_id is not None:
                query = """
                    SELECT 1
                    FROM units
                    WHERE name = %s AND id != %s AND name NOT LIKE %s
                    LIMIT 1
                """
                row = fetch_one(query, (name.strip(), exclude_id, f"{UnitsRepository.DELETED_NAME_PREFIX}%"))
            else:
                query = """
                    SELECT 1
                    FROM units
                    WHERE name = %s AND name NOT LIKE %s
                    LIMIT 1
                """
                row = fetch_one(query, (name.strip(), f"{UnitsRepository.DELETED_NAME_PREFIX}%"))

            return row is not None
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def exists_by_symbol(symbol: str, exclude_id: Optional[int] = None) -> bool:
        try:
            DatabaseUtils.validate_string(symbol, "symbol")
            if exclude_id is not None:
                DatabaseUtils.validate_id(exclude_id, "Unit")
            if exclude_id is not None:
                query = """
                    SELECT 1
                    FROM units
                    WHERE symbol = %s AND id != %s AND name NOT LIKE %s
                    LIMIT 1
                """
                row = fetch_one(query, (symbol.strip(), exclude_id, f"{UnitsRepository.DELETED_NAME_PREFIX}%"))
            else:
                query = """
                    SELECT 1
                    FROM units
                    WHERE symbol = %s AND name NOT LIKE %s
                    LIMIT 1
                """
                row = fetch_one(query, (symbol.strip(), f"{UnitsRepository.DELETED_NAME_PREFIX}%"))

            return row is not None
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def exists_by_id(unit_id: int) -> bool:
        try:
            DatabaseUtils.validate_id(unit_id, "Unit")
            query = """
                SELECT 1
                FROM units
                WHERE id = %s AND name NOT LIKE %s
                LIMIT 1
            """
            row = fetch_one(query, (unit_id, f"{UnitsRepository.DELETED_NAME_PREFIX}%"))
            return row is not None
        except Exception as e:
            raise RuntimeError({str(e)})

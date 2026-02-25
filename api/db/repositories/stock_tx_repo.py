from typing import Optional, List, Dict, Any
from db.pool import fetch_all, fetch_one, execute
from db.base import QueryBuilder, DatabaseUtils

class StockTxRepository:
    DELETED_NOTE_PREFIX = "__deleted__"
    DELETED_LOCATION_NAME_PATTERN = "__deleted__%"
    DELETED_LOCATION_CODE_PATTERN = "DEL_%"

    @staticmethod
    def get_by_id(tx_id: int) -> Optional[Dict[str, Any]]:
        return StockTxRepository.get_by_id_scoped(tx_id)

    @staticmethod
    def get_by_id_scoped(tx_id: int, owner_user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_id(tx_id, "Transaction")
            owner_clause = ""
            params: List[Any] = [
                StockTxRepository.DELETED_LOCATION_NAME_PATTERN,
                StockTxRepository.DELETED_LOCATION_CODE_PATTERN,
                tx_id,
                f"{StockTxRepository.DELETED_NOTE_PREFIX}%",
            ]

            if owner_user_id is not None:
                owner_clause = """
                  AND EXISTS (
                        SELECT 1
                        FROM items io
                        WHERE io.id = st.item_id
                          AND io.owner_user_id = %s
                  )
                """
                params.append(owner_user_id)

            query = """
                SELECT
                    st.id,
                    st.item_id,
                    COALESCE(i.item_code, '-') AS item_code,
                    COALESCE(i.name, '-') AS item_name,
                    st.location_id,
                    COALESCE(l.name, '-') AS location_name,
                    st.tx_type,
                    st.qty,
                    st.ref,
                    st.note,
                    st.tx_at,
                    st.user_id,
                    COALESCE(u.name, '-') AS owner_name
                FROM stock_tx st
                LEFT JOIN items i
                    ON st.item_id = i.id
                   AND i.active = 1
                LEFT JOIN users u
                    ON st.user_id = u.id
                LEFT JOIN locations l
                    ON st.location_id = l.id
                   AND l.active = 1
                   AND l.name NOT LIKE %s
                   AND l.code NOT LIKE %s
                WHERE st.id = %s
                  AND (st.note IS NULL OR st.note NOT LIKE %s)
                {owner_clause}
            """
            query = query.format(owner_clause=owner_clause)
            return fetch_one(query, tuple(params))
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def list_transactions(
        page: int = 1,
        page_size: int = 50,
        item_id: Optional[int] = None,
        location_id: Optional[int] = None,
        tx_type: Optional[str] = None,
        search: Optional[str] = None,
        owner_user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        try:
            conditions = ["(st.note IS NULL OR st.note NOT LIKE %s)"]
            params: List[Any] = [f"{StockTxRepository.DELETED_NOTE_PREFIX}%"]

            if item_id:
                conditions.append("st.item_id = %s")
                params.append(item_id)
            if location_id:
                conditions.append("st.location_id = %s")
                params.append(location_id)
            if tx_type:
                conditions.append("st.tx_type = %s")
                params.append(tx_type)
            if owner_user_id is not None:
                conditions.append(
                    """
                    EXISTS (
                        SELECT 1
                        FROM items io
                        WHERE io.id = st.item_id
                          AND io.owner_user_id = %s
                    )
                    """
                )
                params.append(owner_user_id)

            search_term = DatabaseUtils.sanitize_search_term(search)
            search_condition, search_params = QueryBuilder.build_search_condition(
                search_term, ["i.item_code", "i.name", "l.name", "l.code", "st.ref", "st.note"]
            )
            if search_condition:
                conditions.append(search_condition)
                params.extend(search_params)

            where_clause, params = QueryBuilder.build_where_clause(conditions, params)
            offset = (page - 1) * page_size

            query = f"""
                SELECT
                    st.id,
                    st.item_id,
                    COALESCE(i.item_code, '-') AS item_code,
                    COALESCE(i.name, '-') AS item_name,
                    st.location_id,
                    COALESCE(l.name, '-') AS location_name,
                    st.tx_type,
                    st.qty,
                    st.ref,
                    st.note,
                    st.tx_at,
                    st.user_id,
                    COALESCE(u.name, '-') AS owner_name,
                    sl.qty_on_hand
                FROM stock_tx st
                LEFT JOIN items i
                    ON st.item_id = i.id
                   AND i.active = 1
                LEFT JOIN users u
                    ON st.user_id = u.id
                LEFT JOIN locations l
                    ON st.location_id = l.id
                   AND l.active = 1
                   AND l.name NOT LIKE %s
                   AND l.code NOT LIKE %s
                LEFT JOIN stock_levels sl
                    ON sl.item_id = st.item_id AND sl.location_id = st.location_id
                {where_clause}
                ORDER BY st.tx_at DESC
                LIMIT %s OFFSET %s
            """
            params = [
                StockTxRepository.DELETED_LOCATION_NAME_PATTERN,
                StockTxRepository.DELETED_LOCATION_CODE_PATTERN,
            ] + params
            params.extend([page_size, offset])

            return fetch_all(query, tuple(params))
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def count_transactions(
        item_id: Optional[int] = None,
        location_id: Optional[int] = None,
        tx_type: Optional[str] = None,
        search: Optional[str] = None,
        owner_user_id: Optional[int] = None
    ) -> int:
        try:
            conditions = ["(st.note IS NULL OR st.note NOT LIKE %s)"]
            params: List[Any] = [f"{StockTxRepository.DELETED_NOTE_PREFIX}%"]

            if item_id:
                conditions.append("st.item_id = %s")
                params.append(item_id)
            if location_id:
                conditions.append("st.location_id = %s")
                params.append(location_id)
            if tx_type:
                conditions.append("st.tx_type = %s")
                params.append(tx_type)
            if owner_user_id is not None:
                conditions.append(
                    """
                    EXISTS (
                        SELECT 1
                        FROM items io
                        WHERE io.id = st.item_id
                          AND io.owner_user_id = %s
                    )
                    """
                )
                params.append(owner_user_id)

            search_term = DatabaseUtils.sanitize_search_term(search)
            search_condition, search_params = QueryBuilder.build_search_condition(
                search_term, ["i.item_code", "i.name", "l.name", "l.code", "st.ref", "st.note"]
            )
            if search_condition:
                conditions.append(search_condition)
                params.extend(search_params)

            where_clause, params = QueryBuilder.build_where_clause(conditions, params)

            query = f"""
                SELECT COUNT(*) AS count
                FROM stock_tx st
                LEFT JOIN items i
                    ON st.item_id = i.id
                   AND i.active = 1
                LEFT JOIN locations l
                    ON st.location_id = l.id
                   AND l.active = 1
                   AND l.name NOT LIKE %s
                   AND l.code NOT LIKE %s
                {where_clause}
            """
            params = [
                StockTxRepository.DELETED_LOCATION_NAME_PATTERN,
                StockTxRepository.DELETED_LOCATION_CODE_PATTERN,
            ] + params
            result = fetch_one(query, tuple(params))
            return result["count"] if result else 0
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def create(tx_data: Dict[str, Any]) -> int:
        try:
            query = """
                INSERT INTO stock_tx (item_id, location_id, tx_type, qty, ref, note, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            rows = execute(
                query,
                (
                    tx_data["item_id"],
                    tx_data["location_id"],
                    tx_data["tx_type"],
                    tx_data["qty"],
                    tx_data.get("ref"),
                    tx_data.get("note"),
                    tx_data["user_id"],
                ),
            )
            if rows <= 0:
                raise RuntimeError("Failed to insert transaction")
            inserted = fetch_one("SELECT LAST_INSERT_ID() AS id")
            if not inserted:
                raise RuntimeError("Failed to retrieve inserted transaction ID")
            return int(inserted["id"])
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def update(tx_id: int, tx_data: Dict[str, Any]) -> bool:
        try:
            set_clauses = []
            params = []

            for field in ["item_id", "location_id", "tx_type", "qty", "ref", "note"]:
                if field in tx_data:
                    set_clauses.append(f"{field} = %s")
                    params.append(tx_data[field])
            if "user_id" in tx_data:
                set_clauses.append("user_id = %s")
                params.append(tx_data["user_id"])

            if not set_clauses:
                raise RuntimeError("No fields to update")

            params.append(tx_id)

            query = f"""
                UPDATE stock_tx
                SET {', '.join(set_clauses)}
                WHERE id = %s
            """
            rows = execute(query, tuple(params))
            return rows > 0
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def delete(tx_id: int) -> bool:
        try:
            DatabaseUtils.validate_id(tx_id, "Transaction")
            existing = fetch_one("SELECT note FROM stock_tx WHERE id = %s", (tx_id,))
            if not existing:
                return False

            deleted_note = (
                f"{StockTxRepository.DELETED_NOTE_PREFIX} "
                f"{existing.get('note') or ''}"
            ).strip()
            query = """
                UPDATE stock_tx
                SET note = %s
                WHERE id = %s
                  AND (note IS NULL OR note NOT LIKE %s)
            """
            rows = execute(query, (deleted_note[:255], tx_id, f"{StockTxRepository.DELETED_NOTE_PREFIX}%"))
            return rows > 0
        except Exception as e:
            raise RuntimeError(str(e))

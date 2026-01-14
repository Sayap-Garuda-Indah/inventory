from typing import Optional, List, Dict, Any
from db.pool import fetch_all, fetch_one, execute
from db.base import QueryBuilder, DatabaseUtils

class StockTxRepository:
    @staticmethod
    def get_by_id(tx_id: int) -> Optional[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_id(tx_id, "Transaction")
            query = """
                SELECT
                    st.id,
                    st.item_id,
                    i.item_code,
                    i.name AS item_name,
                    st.location_id,
                    l.name AS location_name,
                    st.tx_type,
                    st.qty,
                    st.ref,
                    st.note,
                    st.tx_at,
                    st.user_id
                FROM stock_tx st
                JOIN items i ON st.item_id = i.id
                JOIN locations l ON st.location_id = l.id
                WHERE st.id = %s
            """
            return fetch_one(query, (tx_id,))
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def list_transactions(
        page: int = 1,
        page_size: int = 50,
        item_id: Optional[int] = None,
        location_id: Optional[int] = None,
        tx_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            conditions = []
            params = []

            if item_id:
                conditions.append("st.item_id = %s")
                params.append(item_id)
            if location_id:
                conditions.append("st.location_id = %s")
                params.append(location_id)
            if tx_type:
                conditions.append("st.tx_type = %s")
                params.append(tx_type)

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
                    i.item_code,
                    i.name AS item_name,
                    st.location_id,
                    l.name AS location_name,
                    st.tx_type,
                    st.qty,
                    st.ref,
                    st.note,
                    st.tx_at,
                    st.user_id,
                    sl.qty_on_hand
                FROM stock_tx st
                JOIN items i ON st.item_id = i.id
                JOIN locations l ON st.location_id = l.id
                LEFT JOIN stock_levels sl
                    ON sl.item_id = st.item_id AND sl.location_id = st.location_id
                {where_clause}
                ORDER BY st.tx_at DESC
                LIMIT %s OFFSET %s
            """
            params.extend([page_size, offset])

            return fetch_all(query, tuple(params))
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def count_transactions(
        item_id: Optional[int] = None,
        location_id: Optional[int] = None,
        tx_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> int:
        try:
            conditions = []
            params = []

            if item_id:
                conditions.append("st.item_id = %s")
                params.append(item_id)
            if location_id:
                conditions.append("st.location_id = %s")
                params.append(location_id)
            if tx_type:
                conditions.append("st.tx_type = %s")
                params.append(tx_type)

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
                JOIN items i ON st.item_id = i.id
                JOIN locations l ON st.location_id = l.id
                {where_clause}
            """
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
            query = "DELETE FROM stock_tx WHERE id = %s"
            rows = execute(query, (tx_id,))
            return rows > 0
        except Exception as e:
            raise RuntimeError(str(e))

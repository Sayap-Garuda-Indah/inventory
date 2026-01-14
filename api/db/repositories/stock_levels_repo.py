from typing import Optional, List, Dict, Any
from db.pool import fetch_all, fetch_one, execute
from db.base import QueryBuilder, DatabaseUtils

class StockLevelsRepository:
    @staticmethod
    def get_by_item_location(item_id: int, location_id: int) -> Optional[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_id(item_id, "Item")
            DatabaseUtils.validate_id(location_id, "Location")
            query = """
                SELECT id, item_id, location_id, qty_on_hand, updated_at
                FROM stock_levels
                WHERE item_id = %s AND location_id = %s
            """
            return fetch_one(query, (item_id, location_id))
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def create(item_id: int, location_id: int, qty_on_hand: float) -> Optional[Dict[str, Any]]:
        try:
            query = """
                INSERT INTO stock_levels (item_id, location_id, qty_on_hand)
                VALUES (%s, %s, %s)
            """
            execute(query, (item_id, location_id, qty_on_hand))
            return StockLevelsRepository.get_by_item_location(item_id, location_id)
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def update_qty(item_id: int, location_id: int, qty_on_hand: float) -> bool:
        try:
            query = """
                UPDATE stock_levels
                SET qty_on_hand = %s
                WHERE item_id = %s AND location_id = %s
            """
            rows = execute(query, (qty_on_hand, item_id, location_id))
            return rows > 0
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def list_levels(
        page: int = 1,
        page_size: int = 50,
        item_id: Optional[int] = None,
        location_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            conditions = []
            params = []

            if item_id:
                conditions.append("sl.item_id = %s")
                params.append(item_id)
            if location_id:
                conditions.append("sl.location_id = %s")
                params.append(location_id)

            search_term = DatabaseUtils.sanitize_search_term(search)
            search_condition, search_params = QueryBuilder.build_search_condition(
                search_term, ["i.item_code", "i.name", "l.name", "l.code"]
            )
            if search_condition:
                conditions.append(search_condition)
                params.extend(search_params)

            where_clause, params = QueryBuilder.build_where_clause(conditions, params)

            offset = (page - 1) * page_size

            query = f"""
                SELECT
                    sl.id,
                    sl.item_id,
                    i.item_code,
                    i.name AS item_name,
                    sl.location_id,
                    l.name AS location_name,
                    sl.qty_on_hand,
                    sl.updated_at
                FROM stock_levels sl
                JOIN items i ON sl.item_id = i.id
                JOIN locations l ON sl.location_id = l.id
                {where_clause}
                ORDER BY sl.updated_at DESC
                LIMIT %s OFFSET %s
            """
            params.extend([page_size, offset])

            return fetch_all(query, tuple(params))
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def count_levels(
        item_id: Optional[int] = None,
        location_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> int:
        try:
            conditions = []
            params = []

            if item_id:
                conditions.append("sl.item_id = %s")
                params.append(item_id)
            if location_id:
                conditions.append("sl.location_id = %s")
                params.append(location_id)

            search_term = DatabaseUtils.sanitize_search_term(search)
            search_condition, search_params = QueryBuilder.build_search_condition(
                search_term, ["i.item_code", "i.name", "l.name", "l.code"]
            )
            if search_condition:
                conditions.append(search_condition)
                params.extend(search_params)

            where_clause, params = QueryBuilder.build_where_clause(conditions, params)

            query = f"""
                SELECT COUNT(*) AS count
                FROM stock_levels sl
                JOIN items i ON sl.item_id = i.id
                JOIN locations l ON sl.location_id = l.id
                {where_clause}
            """
            result = fetch_one(query, tuple(params))
            return result["count"] if result else 0
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def list_expected_by_location(location_id: int) -> List[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_id(location_id, "Location")
            query = """
                    SELECT
                        sl.item_id,
                        sl.qty_on_hand,
                        i.item_code,
                        i.name,
                        i.active
                    FROM stock_levels sl
                    JOIN items i ON sl.item_id = i.id
                    WHERE sl.location_id = %s AND sl.qty_on_hand > 0
                    """
            params = (location_id,)
            results = fetch_all(query, params)

            return results
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def count_expected_items(location_id: int) -> int:
        try:
            DatabaseUtils.validate_id(location_id, "Location")
            query = """
                    SELECT COUNT(*) AS count
                    FROM stock_levels
                    WHERE location_id = %s AND qty_on_hand > 0
                    """
            params = (location_id,)
            results = fetch_one(query, params)

            return results["count"] if results else 0
        except Exception as e:
            raise RuntimeError(str(e))

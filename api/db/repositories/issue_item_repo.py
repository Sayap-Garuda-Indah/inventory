from typing import List, Optional, Dict, Any
from decimal import Decimal
from db.pool import fetch_all, fetch_one, execute, get_db_cursor
from schemas.issue_items import IssueItemCreate, IssueItemUpdate, IssueItemResponse, IssueItemListResponse, IssueItemBulkCreate

class IssueItemRepository:
    @staticmethod
    def get_all(
        issue_id: Optional[Any] = None,
        item_id: Optional[Any] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        try:
            where_conditions = []
            params = []

            if issue_id:
                where_conditions.append("ii.issue_id = %s")
                params.append(issue_id)

            if item_id:
                where_conditions.append("ii.item_id = %s")
                params.append(item_id)

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            query = """
                SELECT
                    ii.id,
                    ii.issue_id,
                    ii.item_id,
                    ii.qty,
                    i.item_code AS item_code,
                    i.name AS item_name
                FROM issue_items ii
                LEFT JOIN items i ON ii.item_id = i.id
                {where_clause}
                ORDER BY ii.id DESC
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])

            return fetch_all(query, tuple(params))
        except Exception as e:
            raise RuntimeError(str(e))
    
    @staticmethod
    def get_by_id(issue_item_id: int) -> Optional[Dict[str, Any]]:
        try:
            if not isinstance(issue_item_id, int) or issue_item_id <= 0:
                raise ValueError("Invalid issue item ID")

            query = """
                SELECT
                    ii.id,
                    ii.issue_id,
                    ii.item_id,
                    ii.qty,
                    i.item_code AS item_code,
                    i.name AS item_name
                FROM issue_items ii
                LEFT JOIN items i ON ii.item_id = i.id
                WHERE ii.id = %s
                """
            
            return fetch_one(query, (issue_item_id,))
        except Exception as e:
            raise RuntimeError(str(e))
        
    @staticmethod
    def get_by_issue_id(issue_id: int) -> List[Dict[str, Any]]:
        try:
            if not isinstance(issue_id, int) or issue_id <= 0:
                raise ValueError("Invalid issue ID")
            
            query = """
                SELECT
                    ii.id,
                    ii.issue_id,
                    ii.item_id,
                    ii.qty,
                    i.item_code as item_code,
                    i.name as item_name,
                    i.unit_id,
                    u.symbol as unit_symbol
                FROM issue_items ii
                LEFT JOIN items i ON ii.item_id = i.id
                LEFT JOIN units u ON i.unit_id = u.id
                WHERE ii.issue_id = %s
                ORDER BY ii.id
            """

            return fetch_all(query, (issue_id,))
        except Exception as e:
            raise RuntimeError(str(e))
        
    @staticmethod
    def create(issue_item_data: IssueItemCreate) -> Optional[Dict[str, Any]]:
        try:
            query = """
                INSERT INTO issue_items (issue_id, item_id, qty)
                VALUES (%s, %s, %s)
                """
            with get_db_cursor(dictionary=False) as cursor:
                cursor.execute(query, (
                    issue_item_data.issue_id,
                    issue_item_data.item_id,
                    issue_item_data.qty
                ))
                last_id = cursor.lastrowid

            if last_id:
                return IssueItemRepository.get_by_id(last_id)
            
            return None
        except Exception as e:
            raise RuntimeError(str(e))
        
    @staticmethod
    def create_bulk(issue_id: int, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        try:
            if not items:
                raise ValueError("Items list cannot be empty")
            
            values = []
            params = []
            for item in items:
                values.append("(%s, %s, %s)")
                params.extend([issue_id, item['item_id'], item['qty']])

            query = f"""
                INSERT INTO issue_items (issue_id, item_id, qty)
                VALUES {', '.join(values)}
            """

            rows_affected = execute(query, tuple(params))

            if rows_affected > 0:
                return IssueItemRepository.get_by_issue_id(issue_id)

            return []
        except Exception as e:
            raise RuntimeError(str(e))
    
    @staticmethod
    def update(issue_item_id: int, issue_item_data: IssueItemUpdate) -> Optional[Dict[str, Any]]:
        try:
            if not isinstance(issue_item_id, int) or issue_item_id <= 0:
                raise ValueError("Invalid issue item ID")
            
            if issue_item_data.qty is None:
                raise ValueError("No fields to update")

            query = """
                UPDATE issue_items
                SET qty = %s
                WHERE id = %s
            """

            rows_affected = execute(query, (issue_item_data.qty, issue_item_id))

            if rows_affected > 0:
                return IssueItemRepository.get_by_id(issue_item_id)

            return None
        except Exception as e:
            raise RuntimeError(str(e))
        
    @staticmethod
    def delete(issue_item_id: int) -> bool:
        try:
            if not isinstance(issue_item_id, int) or issue_item_id <= 0:
                raise ValueError("Invalid issue item ID")

            query = "DELETE FROM issue_items WHERE id = %s"
            rows_affected = execute(query, (issue_item_id,))

            return rows_affected > 0
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def delete_by_issue_id(issue_id: int) -> bool:
        try:
            if not isinstance(issue_id, int) or issue_id <= 0:
                raise ValueError("Invalid issue ID")
            
            query = "DELETE FROM issue_items WHERE issue_id = %s"
            execute(query, (issue_id,))

            return True
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def exists_by_id(issue_item_id: int) -> bool:
        try:
            if not isinstance(issue_item_id, int) or issue_item_id <= 0:
                raise ValueError("Invalid issue item ID")

            return IssueItemRepository.get_by_id(issue_item_id) is not None
        except Exception as e:
            raise RuntimeError(str(e))
        
    @staticmethod
    def exists_by_issue_and_item(issue_id: int, item_id: int) -> bool:
        try:
            query = """
                SELECT COUNT(*) as count
                FROM issue_items
                WHERE issue_id = %s AND item_id = %s
            """
            result = fetch_one(query, (issue_id, item_id))

            return result is not None and result.get('count', 0) > 0
        except Exception as e:
            raise RuntimeError(str(e))
        
    @staticmethod
    def count(issue_id: Optional[int] = None, item_id: Optional[int] = None) -> int:
        try:
            where_conditions = []
            params = []

            if issue_id:
                where_conditions.append("issue_id = %s")
                params.append(issue_id)

            if item_id:
                where_conditions.append("item_id = %s")
                params.append(item_id)

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            query = f"SELECT COUNT(*) as count FROM issue_items {where_clause}"
            result = fetch_one(query, tuple(params))

            return result.get('count', 0) if result else 0
        except Exception as e:
            raise RuntimeError(str(e))

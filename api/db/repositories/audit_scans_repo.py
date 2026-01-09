from typing import Optional, List, Dict, Any
from db.pool import fetch_all, fetch_one, execute
from db.base import DatabaseUtils, QueryBuilder

class AuditScansRepository:
    @staticmethod
    def create(
        session_id: int,
        scanned_by: int,
        scanned_code: str,
        item_id: Optional[str],
        location_id: int,
        result: str,
        note: Optional[str]
    ) -> Dict[str, Any]:
        try:
            DatabaseUtils.validate_id(session_id, "Audit Session")
            DatabaseUtils.validate_id(scanned_by, "User")
            DatabaseUtils.validate_id(location_id, "Location")

            query = """
                    INSERT INTO audit_scans (session_id, scanned_by, scanned_code, item_id, location_id, result, note)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
            params = (session_id, scanned_by, scanned_code, item_id, location_id, result, note)
            execute(query, params)
            scan_result = AuditScansRepository.get_latest_by_session(session_id)

            if scan_result is None or not isinstance(scan_result, dict):
                raise ValueError(f"Failed to retrieve created audit scan for session {session_id}")
            
            return scan_result
        except Exception as e:
            raise RuntimeError(str(e))
    
    @staticmethod
    def get_latest_by_session(session_id: int) -> Optional[Dict[str, Any]]:
        try:
            conditions = ["session_id = %s"]
            where_clause, params = QueryBuilder.build_where_clause(conditions, [session_id])
            
            query = f"""
                    SELECT id, session_id, scanned_at, scanned_by, scanned_code, 
                    item_id, location_id, result, note
                    FROM audit_scans
                    {where_clause}
                    ORDER BY id DESC
                    LIMIT 1
                    """
            result = fetch_one(query, tuple(params))

            return DatabaseUtils.convert_to_dict(result)
        except Exception as e:
            raise RuntimeError(str(e))
    
    @staticmethod
    def list_by_session(session_id: int, result: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            conditions = ["session_id = %s"]
            params: List[Any] = [session_id]

            if result:
                conditions.append("result = %s")
                params.append(result)

            where_clause, params = QueryBuilder.build_where_clause(conditions, params)
            
            query = f"""
                    SELECT id, session_id, scanned_at, scanned_by, scanned_code, 
                    item_id, location_id, result, note
                    FROM audit_scans
                    {where_clause}
                    ORDER BY scanned_at DESC
            """
            results = fetch_all(query, tuple(params))
            
            return results
        except Exception as e:
            raise RuntimeError(str(e))
    
    @staticmethod
    def exists_item_in_session(session_id: int, item_id: int) -> bool:
        try:
            conditions = ["session_id = %s", "item_id = %s"]
            where_clause, params = QueryBuilder.build_where_clause(conditions, [session_id, item_id])
            
            query = f"""
                    SELECT id FROM audit_scans
                    {where_clause}
                    LIMIT 1
                    """
            result = fetch_one(query, tuple(params))

            return result is not None
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def count_by_session(session_id: int) -> int:
        try:
            conditions = ["session_id = %s"]
            where_clause, params = QueryBuilder.build_where_clause(conditions, [session_id])
            
            query = f"SELECT COUNT(*) AS count FROM audit_scans {where_clause}"
            result = fetch_one(query, tuple(params))
            
            return result["count"] if result is not None else 0
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def count_unknown(session_id: int) -> int:
        try:
            conditions = ["session_id = %s", "result = %s"]
            where_clause, params = QueryBuilder.build_where_clause(conditions, [session_id, 'UNKNOWN'])
            
            query = f"SELECT COUNT(*) AS count FROM audit_scans {where_clause}"
            result = fetch_one(query, tuple(params))
            
            return result["count"] if result is not None else 0
        except Exception as e:
            raise RuntimeError(str(e))
            
    @staticmethod
    def list_distinct_item_ids_by_result(session_id: int, results: List[str]) -> List[int]:
        try:
            if not results:
                return []

            placeholders = ", ".join(["%s"] * len(results))
            conditions = ["session_id = %s", "item_id IS NOT NULL", f"result IN ({placeholders})"]
            params = [session_id] + results
            where_clause, _ = QueryBuilder.build_where_clause(conditions, params)
            
            query = f"""
                    SELECT DISTINCT item_id 
                    FROM audit_scans
                    {where_clause}
                    """
            rows = fetch_all(query, tuple(params))

            return [row['item_id'] for row in rows]
        except Exception as e:
            raise RuntimeError(str(e))
from typing import Optional, List, Dict, Any
from db.pool import fetch_all, fetch_one, execute
from db.base import DatabaseUtils, QueryBuilder

class AuditScansRepository:
    @staticmethod
    def create(
        session_id: int,
        scanned_by: int,
        scanned_code: Optional[str],
        item_id: Optional[int],
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
    def list_by_session(
        session_id: int,
        result: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> List[Dict[str, Any]]:
        try:
            conditions = ["session_id = %s"]
            params: List[Any] = [session_id]

            if result:
                conditions.append("result = %s")
                params.append(result)
            else:
                conditions.append("result != %s")
                params.append("MISSING")

            where_clause, params = QueryBuilder.build_where_clause(conditions, params)
            offset, limit = QueryBuilder.build_pagination(page, page_size)
            
            query = f"""
                    SELECT id, session_id, scanned_at, scanned_by, scanned_code, 
                    item_id, location_id, result, note
                    FROM audit_scans
                    {where_clause}
                    ORDER BY scanned_at DESC
                    LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            results = fetch_all(query, tuple(params))

            return DatabaseUtils.convert_rows_dict(results)
        except Exception as e:
            raise RuntimeError(str(e))
    
    @staticmethod
    def exists_item_in_session(session_id: int, item_id: int) -> bool:
        try:
            conditions = ["session_id = %s", "item_id = %s", "result != %s"]
            where_clause, params = QueryBuilder.build_where_clause(conditions, [session_id, item_id, "MISSING"])
            
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
            conditions = ["session_id = %s", "result != %s"]
            where_clause, params = QueryBuilder.build_where_clause(conditions, [session_id, "MISSING"])
            
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

    @staticmethod
    def update_note_by_scan_id(session_id: int, scan_id: int, note: Optional[str]) -> None:
        try:
            DatabaseUtils.validate_id(session_id, "Audit Session")
            DatabaseUtils.validate_id(scan_id, "Audit Scan")
            query = """
                    UPDATE audit_scans
                    SET note = %s
                    WHERE id = %s AND session_id = %s
                    """
            execute(query, (note, scan_id, session_id))
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def update_note_by_item_results(session_id: int, item_id: int, results: List[str], note: Optional[str]) -> None:
        try:
            DatabaseUtils.validate_id(session_id, "Audit Session")
            DatabaseUtils.validate_id(item_id, "Item")
            if not results:
                return
            placeholders = ", ".join(["%s"] * len(results))
            query = f"""
                    UPDATE audit_scans
                    SET note = %s
                    WHERE session_id = %s AND item_id = %s AND result IN ({placeholders})
                    """
            params = [note, session_id, item_id] + results
            execute(query, tuple(params))
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def upsert_missing_note(
        session_id: int,
        item_id: int,
        location_id: int,
        user_id: int,
        note: Optional[str]
    ) -> None:
        try:
            DatabaseUtils.validate_id(session_id, "Audit Session")
            DatabaseUtils.validate_id(item_id, "Item")
            DatabaseUtils.validate_id(location_id, "Location")
            DatabaseUtils.validate_id(user_id, "User")
            query = """
                    SELECT id FROM audit_scans
                    WHERE session_id = %s AND item_id = %s AND result = 'MISSING'
                    LIMIT 1
                    """
            existing = fetch_one(query, (session_id, item_id))
            if existing:
                execute(
                    "UPDATE audit_scans SET note = %s WHERE id = %s",
                    (note, existing["id"])
                )
                return

            insert_query = """
                    INSERT INTO audit_scans
                        (session_id, scanned_by, scanned_code, item_id, location_id, result, note)
                    VALUES (%s, %s, %s, %s, %s, 'MISSING', %s)
                    """
            execute(insert_query, (session_id, user_id, "", item_id, location_id, note))
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def list_notes_by_result(session_id: int, result: str) -> List[Dict[str, Any]]:
        try:
            conditions = ["session_id = %s", "result = %s", "item_id IS NOT NULL"]
            where_clause, params = QueryBuilder.build_where_clause(conditions, [session_id, result])
            query = f"""
                    SELECT item_id, note
                    FROM audit_scans
                    {where_clause}
                    """
            results = fetch_all(query, tuple(params))
            return DatabaseUtils.convert_rows_dict(results)
        except Exception as e:
            raise RuntimeError(str(e))

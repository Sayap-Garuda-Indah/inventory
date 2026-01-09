from typing import Optional, List, Dict, Any
from db.pool import fetch_all, fetch_one, execute
from db.base import DatabaseUtils, QueryBuilder

class AuditSessionRepository:
    @staticmethod
    def create(location_id: int, started_by: int, note: Optional[str], expected_count: int) -> Dict[str, Any]:
        try:
            DatabaseUtils.validate_id(location_id, "Location")
            DatabaseUtils.validate_id(started_by, "User")

            query = """
                    INSERT INTO audit_sessions (location_id, started_by, note, expected_count)
                    VALUES (%s, %s, %s, %s)
                    """
            params = (location_id, started_by, note, expected_count)
            execute(query, params)
            result = AuditSessionRepository.get_latest_by_user(started_by)

            if result is None:
                raise ValueError(f"Failed to retrieve created audit session for user {started_by}")
            
            return result
        except Exception as e:
            raise Exception(str(e))

    @staticmethod
    def get_latest_by_user(user_id: int) -> Optional[Dict[str, Any]]:
        try:
            query = """
                    SELECT  s.*, l.name AS location_name, l.code as location_code,
                            u.name AS started_by_name, uc.name AS closed_by_name
                    FROM audit_sessions s
                    JOIN locations l ON s.location_id = l.id
                    JOIN users u ON s.started_by = u.id
                    LEFT JOIN users uc ON s.closed_by = uc.id
                    WHERE s.started_by = %s
                    ORDER BY s.id DESC
                    LIMIT 1
                    """
            params = (user_id,)
            result = fetch_one(query, params)

            return DatabaseUtils.convert_to_dict(result)
        except Exception as e:
            raise Exception(str(e))
    
    @staticmethod
    def get_by_id(session_id: int) -> Optional[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_id(session_id, "Audit Session")
            query = """SELECT   s.*, l.name AS location_name, l.code AS location_code,
                                u.name AS started_by_name, uc.name AS closed_by_name
                        FROM     audit_sessions s
                        JOIN locations l ON s.location_id = l.id
                        JOIN users u ON s.started_by = u.id
                        LEFT JOIN users uc ON s.closed_by = uc.id
                        WHERE s.id = %s
                    """
            params = (session_id,)
            result = fetch_one(query, params)

            return DatabaseUtils.convert_to_dict(result)
        except Exception as e:
            raise Exception(str(e))

    @staticmethod
    def list_sessions(
        page: int = 1,
        page_size: int = 50,
        status: Optional[str] = None,
        location_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        try:
            conditions = []
            params = []

            if status:
                conditions.append("s.status = %s")
                params.append(status)

            if location_id:
                conditions.append("s.location_id = %s")
                params.append(location_id)

            where_clause, _ = QueryBuilder.build_where_clause(conditions, params)
            offset, limit = QueryBuilder.build_pagination(page, page_size)

            query = f"""
                    SELECT  s.*, l.name AS location_name, l.code AS location_code,
                            u.name AS started_by_name, uc.name AS closed_by_name
                    FROM audit_sessions s
                    JOIN locations l ON s.location_id = l.id
                    JOIN users u ON s.started_by = u.id
                    LEFT JOIN users uc ON s.closed_by = uc.id
                    {where_clause}
                    ORDER BY s.started_at DESC
                    LIMIT %s OFFSET %s
                    """
            params.extend([limit, offset])
            results = fetch_all(query, tuple(params))

            return DatabaseUtils.convert_rows_dict(results)
        except Exception as e:
            raise Exception(str(e))
    
    @staticmethod
    def count_sessions(
        status: Optional[str] = None, 
        location_id: Optional[int] = None
    ) -> int:
        try:
            conditions = []
            params = []

            if status:
                conditions.append("status = %s")
                params.append(status)
            
            if location_id:
                conditions.append("location_id = %s")
                params.append(location_id)

            where_clause, _ = QueryBuilder.build_where_clause(conditions, params)
            query = f"SELECT COUNT(*) AS count FROM audit_sessions {where_clause}"
            result = fetch_one(query, tuple(params))

            return result["count"] if result else 0
        except Exception as e:
            raise Exception(str(e))

    @staticmethod
    def update_status(
        session_id: int,
        status: str,
        closed_by: Optional[int]
    ) -> None:
        try:
            DatabaseUtils.validate_id(session_id, 'Audit Session')
            query = """
                    UPDATE audit_sessions
                    SET status = %s, closed_at = NOW(), closed_by= %s
                    WHERE id = %s
                    """
            params = [status, closed_by, session_id]
            execute(query, tuple(params))
        except Exception as e:
            raise Exception(str(e))

    @staticmethod
    def update_counts(
        session_id: int,
        scanned_count: int,
        missing_count: int,
        unexpected_count: int,
        unknown_count: int
    ) -> None:
        try:
            DatabaseUtils.validate_id(session_id, "Audit Session")
            
            update_fields = {
                "scanned_count": scanned_count,
                "missing_count": missing_count,
                "unexpected_count": unexpected_count,
                "unknown_count": unknown_count
            }
            
            set_clause, params = QueryBuilder.build_update_set(update_fields, exclude_none=False)
            query = f"UPDATE audit_sessions {set_clause} WHERE id = %s"
            params.append(session_id)
            execute(query, tuple(params))
        except Exception as e:
            raise Exception(str(e))

    @staticmethod
    def increment_counts(
        session_id: int,
        scanned_delta: int,
        unknown_delta: int,
        unexpected_delta: int
    ) -> None:
        try:
            DatabaseUtils.validate_id(session_id, "Audit Session")
            query = """
                    UPDATE audit_sessions
                    SET scanned_count = scanned_count + %s,
                        unknown_count = unknown_count + %s,
                        unexpected_count = unexpected_count + %s
                    WHERE id = %s
                    """
            params = (scanned_delta, unknown_delta, unexpected_delta, session_id)
            execute(query, params)
        except Exception as e:
            raise Exception(str(e))
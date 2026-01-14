from typing import List, Optional, Dict, Any
from db.pool import fetch_all, fetch_one, execute
from schemas.issues import IssueCreate, IssueUpdate, IssueResponse, IssueListResponse
from datetime import datetime, timezone

class IssueRepository:
    @staticmethod
    def get_all(
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all issues with optional filters.
        """
        try:
            where_conditions = []
            params = []

            if search:
                where_conditions.append("(code LIKE %s OR status LIKE %s)")
                search_param = f"%{search}%"
                params.extend([search_param, search_param])

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            query = f"""
                SELECT id, code, status, requested_by, approved_by, issued_at, note, updated_at
                FROM issues
                {where_clause}
                ORDER BY issued_at DESC
                LIMIT %s OFFSET %s
                """
            params.extend([limit, offset])

            return fetch_all(query, tuple(params))
        except Exception as e:
            raise RuntimeError({str(e)})
        
    @staticmethod
    def get_by_id(issue_id: int) -> Optional[Dict[str, Any]]:
        """
        Get an issue by its ID.
        """
        try:
            if not isinstance(issue_id, int) or issue_id <= 0:
                raise ValueError("Invalid issue ID")
            
            query = """
                SELECT id, code, status, requested_by, approved_by, issued_at, note, updated_at
                FROM issues
                WHERE id = %s
                """
            return fetch_one(query, (issue_id,))
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def get_by_code(issue_code: str) -> Optional[Dict[str, Any]]:
        """
        Get an issue by its code.
        """
        try:
            if not issue_code:
                raise ValueError("Invalid issue code")
            
            query = """
                SELECT id, code, status, requested_by, approved_by, issued_at, note, updated_at
                FROM issues
                WHERE code = %s
                """
            return fetch_one(query, (issue_code,))
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def create(issue_data: IssueCreate) -> Optional[Dict[str, Any]]:
        """
        Create a new issue.
        """
        try:
            query = """
                INSERT INTO issues (code, status, requested_by, approved_by, issued_at, note, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), %s, NOW())
                """
            params = (
                issue_data.code,
                issue_data.status,
                issue_data.requested_by,
                issue_data.approved_by,
                issue_data.note
            )

            rows_affected = execute(query, params)
            
            if rows_affected == 0:
                return None
            
            data = fetch_one("SELECT * FROM issues WHERE code = %s ORDER BY id DESC LIMIT 1", (issue_data.code,))
            
            return data
        except Exception as e:
            raise RuntimeError({str(e)})
        
    @staticmethod
    def update(issue_id: int, issue_data: IssueUpdate) -> Optional[Dict[str, Any]]:
        try:
            if not isinstance(issue_id, int) or issue_id <= 0:
                raise ValueError("Invalid issue ID")
            
            set_clauses = []
            params = []

            if issue_data.code is not None:
                set_clauses.append("code = %s")
                params.append(issue_data.code)
            if issue_data.status is not None:
                set_clauses.append("status = %s")
                params.append(issue_data.status)
            if issue_data.requested_by is not None:
                set_clauses.append("requested_by = %s")
                params.append(issue_data.requested_by)
            if issue_data.approved_by is not None:
                set_clauses.append("approved_by = %s")
                params.append(issue_data.approved_by)
            if issue_data.issued_at is not None:
                set_clauses.append("issued_at = %s")
                params.append(issue_data.issued_at)
            if issue_data.note is not None:
                set_clauses.append("note = %s")
                params.append(issue_data.note)
            set_clauses.append("updated_at = %s")
            params.append(datetime.now(timezone.utc))
                        
            if not set_clauses:
                raise ValueError("No fields to update")
            
            set_clause = ", ".join(set_clauses)
            params.append(issue_id)

            query = f"""
                UPDATE issues
                SET {set_clause}
                WHERE id = %s
                """
            rows_affected = execute(query, tuple(params))
            
            if rows_affected > 0:
                return IssueRepository.get_by_id(issue_id)
            else:
                return None
        except Exception as e:
            raise RuntimeError({str(e)})
            
    @staticmethod
    def delete(issue_id: int) -> bool:
        try:
            if not isinstance(issue_id, int) or issue_id <= 0:
                raise ValueError("Invalid issue ID")
            
            query = "DELETE FROM issues WHERE id = %s"
            rows_affected = execute(query, (issue_id,))

            if rows_affected > 0:
                return True
            else:
                return False
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def exists_by_id(issue_id: int) -> bool:
        try:
            if not isinstance(issue_id, int) or issue_id <= 0:
                raise ValueError("Invalid issue ID")
            
            if IssueRepository.get_by_id(issue_id) is not None:
                return True
            else:
                return False
        except Exception as e:
            raise RuntimeError({str(e)})
    
    @staticmethod
    def count() -> int:
        """
        Count all issues.
        """
        try:
            query = "SELECT COUNT(1) as count FROM issues"
            result = fetch_one(query)

            if result is not None:
                return result['count']
            else:
                return 0
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def count_status(issue_status : str) -> int:
        try:
            where_conditions = []
            params = []

            if issue_status:
                where_conditions.append("status = %s")
                params.append(issue_status)

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            query = f"""
                SELECT COUNT(1) as count
                FROM issues
                {where_clause}
                """
            result = fetch_one(query, tuple(params))

            if result is not None:
                return result['count']
            else:
                return 0
        except Exception as e:
            raise RuntimeError({str(e)})
    
    @staticmethod
    def count_with_filter(search: Optional[str] = None, status_filter: Optional[str] = None) -> int:
        try:
            where_conditions = []
            params = []

            if search:
                where_conditions.append("(code LIKE %s OR status LIKE %s)")
                search_param = f"%{search}%"
                params.extend([search_param, search_param])

            if status_filter:
                where_conditions.append("status = %s")
                params.append(status_filter)

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            query = f"""
                SELECT COUNT(1) as count
                FROM issues
                {where_clause}
                """
            
            result = fetch_one(query, tuple(params))

            if result is not None:
                return result['count']
            else:
                return 0
        except Exception as e:
            raise RuntimeError({str(e)})
    
    @staticmethod
    def exists_by_code(issue_code: str) -> bool:
        try:
            if not issue_code:
                raise ValueError("Invalid issue code")
            
            if IssueRepository.get_by_code(issue_code) is not None:
                return True
            else:
                return False
        except Exception as e:
            raise RuntimeError({str(e)})
        
    @staticmethod
    def approve_issue(issue_id: int, approver_id: int) -> Optional[Dict[str, Any]]:
        """
        Approve an issue by setting its status to 'APPROVED' and recording the approver's ID.
        """
        try:
            if not isinstance(issue_id, int) or issue_id <= 0:
                raise ValueError("Invalid issue ID")
            
            query = """
                UPDATE issues
                SET status = 'APPROVED', approved_by = %s, updated_at = NOW()
                WHERE id = %s
                """
            
            rows_affected = execute(query, (approver_id, issue_id))

            if rows_affected > 0:
                return IssueRepository.get_by_id(issue_id)
            else:
                return None
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def change_status(issue_id: int, new_status: str) -> Optional[Dict[str, Any]]:
        """
        Change the status of an issue.
        """
        try:
            if not isinstance(issue_id, int) or issue_id <= 0:
                raise ValueError("Invalid issue ID")
            
            query = """
                UPDATE issues
                SET status = %s, updated_at = NOW()
                WHERE id = %s
                """
            
            rows_affected = execute(query, (new_status, issue_id))

            if rows_affected > 0:
                return IssueRepository.get_by_id(issue_id)
            else:
                return None
        except Exception as e:
            raise RuntimeError({str(e)})
from typing import TypeVar, Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime, date
import re
# import json

T = TypeVar('T')

class DatabaseConstants:
    """Common database constants and enums"""

    # Table names
    TABLE_USERS = "users"
    TABLE_ITEMS = "items"
    TABLE_CATEGORIES = "categories"
    TABLE_UNITS = "units"
    TABLE_LOCATIONS = "locations"
    TABLE_ISSUE = "issues"
    TABLE_ISSUE_ITEMS = "issue_items"
    TABLE_STOCK_ITEMS = "stock_levels"
    TABLE_STOCK_TX = "stock_tx"
    TABLE_ATTACHMENTS = "attachments"
    TABLE_AUDIT_LOG = "audit_log"

    # Status values
    STATUS_DRAFT = "DRAFT"
    STATUS_APPROVED = "APPROVED"
    STATUS_ISSUED = "ISSUED"
    STATUS_CANCELED = "CANCELLED"

    # Transaction types
    TX_TYPE_IN = "IN"
    TX_TYPE_OUT = "OUT"
    TX_TYPE_ADJ = "ADJ"
    TX_TYPE_XFER = "XFER"

    # User roles
    ROLE_ADMIN = "ADMIN"
    ROLE_STAFF = "STAFF"
    ROLE_AUDITOR = "AUDITOR"

class QueryBuilder:
    """Helper class for building SQL queries dynamically"""

    @staticmethod
    def build_where_clause(
        conditions: List[str],
        params: List[Any]
    ) -> tuple[str, list]:
        """
        Builds a WHERE clause from given conditions and parameters.

        Args:
            conditions (List[str]): List of SQL conditions as strings.
            params (List[any]): List of parameters corresponding to the conditions.
        Returns:
            tuple[str, list]: A tuple containing the WHERE clause string and the parameters list.
        """
        if not conditions:
            return "", []

        where_clause = "WHERE " + " AND ".join(conditions)

        return where_clause, params

    @staticmethod
    def build_pagination(
        page: int = 1,
        page_size: int = 50
    ) -> tuple[int, int]:
        """
        Calculates offset and limit for pagination.

        Args:
            page (int): The page number (1-indexed).
            page_size (int): The number of items per page.
        Returns:
            tuple[int, int]: A tuple containing the offset and limit.
        """
        offset = (page - 1) * page_size
        limit = page_size
        return offset, limit
    
    @staticmethod
    def build_search_condition(
        search_term: Optional[str],
        fields: List[str]
    ) -> tuple[Optional[str], List[str]]:
        """
        Builds a search condition for SQL queries.

        Args:
            search_term (Optional[str]): The term to search for.
            fields (List[str]): List of fields to search in.
        Returns:
            tuple[Optional[str], List[str]]: A tuple containing the search condition string and the parameters list.
        """
        if not search_term or not fields:
            return None, []

        conditions = [f"{field} LIKE %s" for field in fields]
        condition_str = "(" + " OR ".join(conditions) + ")"
        search_param = f"%{search_term}%"
        params = [search_param] * len(fields)

        return condition_str, params

    @staticmethod
    def build_update_set(
        update_fields: Dict[str, Any],
        exclude_none: bool = True
    ) -> tuple[str, list]:
        """
        Builds a SET clause for SQL UPDATE statements.

        Args:
            update_fields (Dict[str, Any]): A dictionary of fields to update with their new values.
            exclude_none (bool): Whether to exclude fields with None values.
        Returns:
            tuple[str, list]: A tuple containing the SET clause string and the parameters list.
        """
        if exclude_none:
            update_fields = {k: v for k, v in update_fields.items() if v is not None}

        if not update_fields:
            return "", []

        set_parts = [f"{field} = %s" for field in update_fields.keys()]
        set_clause = "SET " + ", ".join(set_parts)
        params = list(update_fields.values())

        return set_clause, params

class DatabaseUtils:
    """Common database utility functions."""

    @staticmethod
    def convert_to_dict(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Convert database row to JSON-serializable dict.
        Handles Decimal, datetime, data types.

        Args:
            row (Optional[Dict[str, Any]]): The database row as a dictionary.
        Returns:
            Optional[Dict[str, Any]]: The JSON-serializable dictionary or None.
        """
        if row is None:
            return None

        result = {}
        for key, value in row.items():
            if isinstance(value, Decimal):
                result[key] = float(value)
            elif isinstance(value, (datetime, date)):
                result[key] = value.isoformat()
            elif isinstance(value, bytes):
                result[key] = value.decode('utf-8')
            else:
                result[key] = value

        return result
    
    @staticmethod
    def convert_rows_dict(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert list of database rows to list of JSON-serializable dicts.
        Handles Decimal, datetime, data types.

        Args:
            rows (List[Dict[str, Any]]): The list of database rows as dictionaries.
        Returns:
            List[Dict[str, Any]]: The list of JSON-serializable dictionaries.
        """
        return [converted for row in rows if (converted := DatabaseUtils.convert_to_dict(row)) is not None]
    
    @staticmethod
    def validate_id(entity_id: Any, entity_name: str = "Entity") -> None:
        """
        Validates that the given ID is a positive integer.

        Args:
            entity_id (Any): The ID to validate.
            entity_name (str): The name of the entity for error messages.
        Raises:
            ValueError: If the ID is not a positive integer.
        """
        if not isinstance(entity_id, int) or entity_id <= 0:
            raise ValueError(f"{entity_name} ID must be a positive integer.")
        
    @staticmethod
    def validate_string(
        value: Any,
        field_name: str,
        min_length: int = 1,
        max_length: Optional[int] = None
    ) -> None:
        """
        Validates that the given value is a string within specified length constraints.
        """
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string.")
        
        if not value or not value.strip():
            raise ValueError(f"{field_name} cannot be empty or whitespace.")
        
        if len(value) < min_length:
            raise ValueError(f"{field_name} must be at least {min_length} characters long.")
        
        if max_length is not None and len(value) > max_length:
            raise ValueError(f"{field_name} cannot exceed {max_length} characters.")

    @staticmethod
    def sanitize_search_term(search: Optional[str]) -> Optional[str]:
        """
        Sanitize search term by stripping leading/trailing whitespace.

        Args:
            search (Optional[str]): The search term to sanitize.

        Returns:
            Optional[str]: The sanitized search term or None.
        """
        if not search:
            return None

        # Escape special LIKE wildcards
        # sanitize = search.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')

        # Remove dangerous characters but keep spaces and alphanumeric
        sanitized = re.sub(r'[^\w\s\-]', '', search.strip())

        return sanitized if sanitized else None
    
class BaseRepository:
    """
    Optional base repository class with common patterns.
    Repositories can use these static methods without inheritance.
    """
    @staticmethod
    def exists_by_field(
        table_name: str,
        field_name: str,
        field_value: Any,
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        Generic exists check by field.

        Args:
            table_name (str): The name of the table to query.
            field_name (str): The field to check.
            field_value (Any): The value to check for.
            exclude_id (Optional[int]): An optional ID to exclude from the check.

        Returns:
            bool: True if a record exists with the given field value, False otherwise.
        """
        from db.pool import fetch_one  # Local import to avoid circular dependency

        if exclude_id:
            query = f"SELECT COUNT(*) AS count FROM {table_name} WHERE {field_name} = %s AND id != %s"
            result = fetch_one(query, (field_value, exclude_id))
        else:
            query = f"SELECT COUNT(*) AS count FROM {table_name} WHERE {field_name} = %s"
            result = fetch_one(query, (field_value,))

        if result and result.get("count", 0) > 0:
            return True
        
        return False
    
    @staticmethod
    def soft_delete(table_name: str, record_id: int, field_name: str = 'active') -> bool:
        """
        Generic soft delete by setting a field to False.

        Args:
            table_name (str): The name of the table to update.
            record_id (int): The ID of the record to soft delete.
            field_name (str): The field to set to False (default is 'active').

        Returns:
            bool: True if the record was updated, False otherwise.
        """
        from db.pool import execute  # Local import to avoid circular dependency

        if field_name == 'active':
            query = f"UPDATE {table_name} SET {field_name} = 0 WHERE id = %s"
        elif field_name == 'is_active':
            query = f"UPDATE {table_name} SET {field_name} = 'CANCELED' WHERE id = %s"
        else:
            query = f"UPDATE {table_name} SET {field_name} = NULL WHERE id = %s"

        rows_affected = execute(query, (record_id,))
        
        return rows_affected > 0

__all__ = [
    "DatabaseConstants",
    "QueryBuilder",
    "DatabaseUtils",
    "BaseRepository",
]
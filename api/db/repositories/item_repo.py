from typing import Optional, List, Dict, Any
from db.pool import fetch_all, fetch_one, execute
from db.base import QueryBuilder, DatabaseUtils, BaseRepository, DatabaseConstants
from schemas.items import ItemCreate, ItemUpdate

class ItemRepository:
    DELETED_TX_NOTE_PREFIX = "__deleted__"

    @staticmethod
    def get_all(
        active_only: bool = True,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all items with optional filters.
        """
        try:
            conditions = []
            params = []

            if active_only:
                conditions.append("active = %s")
                params.append(True)

            # Sanitize and validate search term
            if search and search.strip():
                search_term = DatabaseUtils.sanitize_search_term(search)
                if search_term:
                    search_condition, search_params = QueryBuilder.build_search_condition(
                        search_term, 
                        ["item_code", "name", "description"]
                    )
                    if search_condition:
                        conditions.append(search_condition)
                        params.extend(search_params)

            where_clause, params = QueryBuilder.build_where_clause(conditions, params)

            query = f"""
                SELECT 
                    id, item_code, name, category_id, unit_id, 
                    owner_user_id, serial_number, min_stock, 
                    description, image_url, active
                FROM items
                {where_clause}
                ORDER BY name
                LIMIT %s OFFSET %s
                """
            params.extend([limit, offset])

            return fetch_all(query, tuple(params))
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def get_by_id(item_id: int) -> Optional[Dict[str, Any]]:
        """
        Get an item by its ID.
        """
        try:
            DatabaseUtils.validate_id(item_id, "Item")
            
            query = """
                SELECT 
                    id, item_code, serial_number, name, category_id, unit_id, 
                    owner_user_id, min_stock, description, image_url, active
                FROM items
                WHERE id = %s
                """
            return fetch_one(query, (item_id,))
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def get_by_item_code(item_code: str) -> Optional[Dict[str, Any]]:
        """
        Get an item by its item code.
        """
        try:
            DatabaseUtils.validate_string(item_code, "item_code")
            
            query = """
                SELECT id, item_code, name, category_id, unit_id, owner_user_id, serial_number, min_stock, description, image_url, active
                FROM items
                WHERE item_code = %s
                """
            return fetch_one(query, (item_code.strip().upper(),))
        except Exception as e:
            raise RuntimeError(str(e))

        
    @staticmethod
    def create(item_data: ItemCreate) -> Optional[Dict[str, Any]]:
        """
        Create a new item.
        """
        try:
            query = """
                INSERT INTO items (item_code, serial_number, name, category_id, unit_id, owner_user_id, min_stock, description, image_url, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
            execute(query, (
                item_data.item_code.strip().upper(),
                item_data.serial_number,
                item_data.name,
                item_data.category_id,
                item_data.unit_id,
                item_data.owner_user_id,
                item_data.min_stock,
                item_data.description,
                item_data.image_url,
                item_data.active,
            ))
            
            return ItemRepository.get_by_item_code(item_data.item_code)
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def update(item_id: int, item_data: ItemUpdate) -> Optional[Dict[str, Any]]:
        """
        Update an existing item.
        """
        try:
            DatabaseUtils.validate_id(item_id, "Item")
            
            set_clauses = []
            params = []

            if item_data.item_code is not None:
                set_clauses.append("item_code = %s")
                params.append(item_data.item_code.strip().upper())
            if item_data.serial_number is not None:
                set_clauses.append("serial_number = %s")
                params.append(item_data.serial_number)
            if item_data.name is not None:
                set_clauses.append("name = %s")
                params.append(item_data.name)
            if item_data.category_id is not None:
                set_clauses.append("category_id = %s")
                params.append(item_data.category_id)
            if item_data.unit_id is not None:
                set_clauses.append("unit_id = %s")
                params.append(item_data.unit_id)
            if item_data.owner_user_id is not None:
                set_clauses.append("owner_user_id = %s")
                params.append(item_data.owner_user_id)
            if item_data.min_stock is not None:
                set_clauses.append("min_stock = %s")
                params.append(item_data.min_stock)
            if item_data.description is not None:
                set_clauses.append("description = %s")
                params.append(item_data.description)
            if item_data.image_url is not None:
                set_clauses.append("image_url = %s")
                params.append(item_data.image_url)
            if item_data.active is not None:
                set_clauses.append("active = %s")
                params.append(item_data.active)

            if not set_clauses:
                raise ValueError("No fields to update")
            
            set_clause = ", ".join(set_clauses)
            params.append(item_id)

            query = f"""
                UPDATE items
                SET {set_clause}
                WHERE id = %s
                """
            rows_affected = execute(query, tuple(params))

            if rows_affected > 0:
                return ItemRepository.get_by_id(item_id)
            else:
                return None
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def delete(item_id: int) -> bool:
        """
        Soft delete an item by setting its active status to False.
        """
        try:
            DatabaseUtils.validate_id(item_id, "Item")
            query = "UPDATE items SET active = 0 WHERE id = %s AND active = 1"
            rows_affected = execute(query, (item_id,))
            return rows_affected > 0
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def get_dependency_summary(item_id: int) -> Dict[str, int]:
        try:
            DatabaseUtils.validate_id(item_id, "Item")

            issue_items = fetch_one(
                "SELECT COUNT(*) AS count FROM issue_items WHERE item_id = %s",
                (item_id,),
            )
            stock_levels = fetch_one(
                "SELECT COUNT(*) AS count FROM stock_levels WHERE item_id = %s",
                (item_id,),
            )
            stock_transactions = fetch_one(
                """
                SELECT COUNT(*) AS count
                FROM stock_tx
                WHERE item_id = %s
                  AND (note IS NULL OR note NOT LIKE %s)
                """,
                (item_id, f"{ItemRepository.DELETED_TX_NOTE_PREFIX}%"),
            )
            audit_scans = fetch_one(
                "SELECT COUNT(*) AS count FROM audit_scans WHERE item_id = %s",
                (item_id,),
            )

            return {
                "issue_items": int(issue_items["count"]) if issue_items else 0,
                "stock_levels": int(stock_levels["count"]) if stock_levels else 0,
                "stock_transactions": int(stock_transactions["count"]) if stock_transactions else 0,
                "audit_scans": int(audit_scans["count"]) if audit_scans else 0,
            }
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def count(active_only: bool = True, search: Optional[str] = None) -> int:
        """
        Count items with optional filters.
        """
        try:
            conditions = []
            params = []

            if active_only:
                conditions.append("active = %s")
                params.append(True)

            search_term = DatabaseUtils.sanitize_search_term(search)
            search_condition, search_params = QueryBuilder.build_search_condition(search_term, ["item_code", "name"])
            if search_condition:
                conditions.append(search_condition)
                params.extend(search_params)

            where_clause, params = QueryBuilder.build_where_clause(conditions, params)

            query = f"SELECT COUNT(*) as count FROM items {where_clause}"
            result = fetch_one(query, tuple(params))

            return result['count'] if result else 0
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def exists_by_item_code(item_code: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if an item exists by its item code.
        """
        try:
            DatabaseUtils.validate_string(item_code, "item_code")
            if exclude_id is not None:
                DatabaseUtils.validate_id(exclude_id, "Item")
            return BaseRepository.exists_by_field(
                DatabaseConstants.TABLE_ITEMS,
                "item_code",
                item_code.strip().upper(),
                exclude_id
            )
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def exists_by_id(item_id: int) -> bool:
        """
        Check if an item exists by its ID.
        """
        try:
            DatabaseUtils.validate_id(item_id, "Item")
            return BaseRepository.exists_by_field(DatabaseConstants.TABLE_ITEMS, "id", item_id)
        except Exception as e:
            raise RuntimeError(str(e))
        
    @staticmethod
    def get_by_serial_number(serial_number: str) -> Optional[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_string(serial_number, "serial_number")
            
            query = """
                SELECT 
                    id, item_code, serial_number, name, category_id, unit_id, 
                    owner_user_id, min_stock, description, image_url, active
                FROM items
                WHERE serial_number = %s
                """
            return fetch_one(query, (serial_number.strip(),))
        except Exception as e:
            raise RuntimeError(str(e))

from typing import Optional, List, Dict, Any
import pymysql as MySQLdb
from db.pool import fetch_all, fetch_one, execute_transaction, execute, get_db_transaction
from db.base import QueryBuilder, DatabaseUtils
from schemas.categories import CategoryCreate, CategoryUpdate

class CategoryRepository:
    DELETED_NAME_PREFIX = "__deleted__"
    FALLBACK_CATEGORY_NAME = "-"

    @staticmethod
    def get_all(
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            conditions = ["name NOT LIKE %s"]
            params = [f"{CategoryRepository.DELETED_NAME_PREFIX}%"]

            search_term = DatabaseUtils.sanitize_search_term(search)
            search_condition, search_params = QueryBuilder.build_search_condition(search_term, ["name"])
            if search_condition:
                conditions.append(search_condition)
                params.extend(search_params)

            where_clause, params = QueryBuilder.build_where_clause(conditions, params)
            query = f"""
                SELECT id, name
                FROM categories
                {where_clause}
                ORDER BY name
                LIMIT %s OFFSET %s
                """

            params.extend([limit, offset])

            category_list = fetch_all(query, tuple(params))
            return category_list
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def get_by_id(category_id: int) -> Optional[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_id(category_id, "Category")

            query = """
                SELECT id, name
                FROM categories
                WHERE id = %s AND name NOT LIKE %s
                """

            cat_id = fetch_one(query, (category_id, f"{CategoryRepository.DELETED_NAME_PREFIX}%"))
            return cat_id
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def exists_by_name(name: str) -> bool:
        try:
            DatabaseUtils.validate_string(name, "name")
            query = """
                SELECT 1
                FROM categories
                WHERE name = %s AND name NOT LIKE %s
                LIMIT 1
            """
            row = fetch_one(query, (name.strip(), f"{CategoryRepository.DELETED_NAME_PREFIX}%"))
            return row is not None
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def exists_by_id(category_id: int) -> bool:
        try:
            DatabaseUtils.validate_id(category_id, "Category")
            query = """
                SELECT 1
                FROM categories
                WHERE id = %s AND name NOT LIKE %s
                LIMIT 1
            """
            row = fetch_one(query, (category_id, f"{CategoryRepository.DELETED_NAME_PREFIX}%"))
            return row is not None
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def get_by_name(name: str) -> Optional[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_string(name, "name")

            query = """
                SELECT id, name
                FROM categories
                WHERE name = %s AND name NOT LIKE %s
            """
            return fetch_one(query, (name.strip(), f"{CategoryRepository.DELETED_NAME_PREFIX}%"))
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def get_or_create_fallback_category() -> Dict[str, Any]:
        try:
            fallback = CategoryRepository.get_by_name(CategoryRepository.FALLBACK_CATEGORY_NAME)
            if fallback:
                return fallback

            query = """
                INSERT INTO categories (name)
                VALUES (%s)
            """
            results = execute_transaction([(query, (CategoryRepository.FALLBACK_CATEGORY_NAME,))])
            if not results or not results[0]:
                raise RuntimeError("Failed to create fallback category '-'")

            fallback = CategoryRepository.get_by_name(CategoryRepository.FALLBACK_CATEGORY_NAME)
            if not fallback:
                raise RuntimeError("Failed to fetch fallback category '-'")

            return fallback
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def soft_delete_and_reassign(category_id: int) -> Dict[str, Any]:
        try:
            DatabaseUtils.validate_id(category_id, "Category")

            fallback = CategoryRepository.get_or_create_fallback_category()
            fallback_id = int(fallback["id"])
            if fallback_id == category_id:
                raise RuntimeError("Fallback category '-' cannot be deleted.")

            with get_db_transaction() as connection:
                cursor = connection.cursor(MySQLdb.cursors.DictCursor)
                try:
                    cursor.execute(
                        """
                        SELECT id, name
                        FROM categories
                        WHERE id = %s AND name NOT LIKE %s
                        FOR UPDATE
                        """,
                        (category_id, f"{CategoryRepository.DELETED_NAME_PREFIX}%"),
                    )
                    target = cursor.fetchone()
                    if not target:
                        raise RuntimeError(f"Category with id {category_id} not found")

                    cursor.execute(
                        "SELECT COUNT(*) AS count FROM items WHERE category_id = %s FOR UPDATE",
                        (category_id,),
                    )
                    row = cursor.fetchone()
                    reassigned_items = int(row["count"]) if row else 0

                    if reassigned_items > 0:
                        cursor.execute(
                            "UPDATE items SET category_id = %s WHERE category_id = %s",
                            (fallback_id, category_id),
                        )

                    deleted_name = f"{CategoryRepository.DELETED_NAME_PREFIX}{category_id}"
                    cursor.execute(
                        "UPDATE categories SET name = %s WHERE id = %s",
                        (deleted_name, category_id),
                    )
                    if cursor.rowcount <= 0:
                        raise RuntimeError("Failed to soft delete category")
                finally:
                    cursor.close()

            return {
                "deleted_category_id": category_id,
                "deleted_category_name": target["name"],
                "reassigned_items": reassigned_items,
                "replacement_category_name": fallback["name"],
                "replacement_category_id": fallback_id,
            }
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def create(category: CategoryCreate) -> int:
        try:
            query = """
                INSERT INTO categories (name)
                VALUES (%s)
                """

            results = execute_transaction([(query, (category.name,))])
            if not results or not results[0]:
                raise RuntimeError("Failed to create category")

            return int(results[0])
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def update(category_id: int, category: CategoryUpdate) -> None:
        try:
            DatabaseUtils.validate_id(category_id, "Category")

            query = """
                UPDATE categories
                SET name = %s
                WHERE id = %s
                """
            execute(query, (category.name, category_id))
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def delete(category_id: int) -> bool:
        try:
            result = CategoryRepository.soft_delete_and_reassign(category_id)
            return bool(result)
        except Exception as e:
            raise RuntimeError({str(e)})

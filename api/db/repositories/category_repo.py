from typing import Optional, List, Dict, Any
from db.pool import fetch_all, fetch_one, execute
from db.base import QueryBuilder, DatabaseUtils, BaseRepository
from schemas.categories import CategoryCreate, CategoryUpdate

class CategoryRepository:
    @staticmethod
    def get_all(
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            conditions = []
            params = []

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
                WHERE id = %s
                """

            cat_id = fetch_one(query, (category_id,))
            return cat_id
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def exists_by_name(name: str) -> bool:
        try:
            DatabaseUtils.validate_string(name, "name")
            return BaseRepository.exists_by_field("categories", "name", name.strip())
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def exists_by_id(category_id: int) -> bool:
        try:
            DatabaseUtils.validate_id(category_id, "Category")
            return BaseRepository.exists_by_field("categories", "id", category_id)
        except Exception as e:
            raise RuntimeError({str(e)})


    @staticmethod
    def create(category: CategoryCreate) -> int:
        try:
            query = """
                INSERT INTO categories (name)
                VALUES (%s)
                RETURNING id
                """
            
            new_id = fetch_one(query, (category.name,))

            if new_id is None:
                raise RuntimeError("Failed to create category")

            return new_id['id']
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
            DatabaseUtils.validate_id(category_id, "Category")

            query = "DELETE FROM categories WHERE id = %s"
            rows_affected = execute(query, (category_id,))

            return rows_affected > 0
        except Exception as e:
            raise RuntimeError({str(e)})

from typing import Optional, List, Dict, Any
from db.pool import fetch_all, fetch_one
from db.base import QueryBuilder, DatabaseUtils, BaseRepository, DatabaseConstants

class LocationsRepository:
    @staticmethod
    def get_all(
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            conditions = []
            params = []

            if active_only:
                conditions.append("active = %s")
                params.append(True)

            search_term = DatabaseUtils.sanitize_search_term(search)
            search_condition, search_params = QueryBuilder.build_search_condition(search_term, ["name", "code"])
            if search_condition:
                conditions.append(search_condition)
                params.extend(search_params)

            where_clause, params = QueryBuilder.build_where_clause(conditions, params)

            query = f"""
                SELECT id, name, code, active
                FROM locations
                {where_clause}
                ORDER BY name
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])

            return fetch_all(query, tuple(params))
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def get_by_id(location_id: int) -> Optional[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_id(location_id, "Location")
            query = """
                SELECT id, name, code, active
                FROM locations
                WHERE id = %s
            """
            return fetch_one(query, (location_id,))
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def exists_by_id(location_id: int) -> bool:
        try:
            DatabaseUtils.validate_id(location_id, "Location")
            return BaseRepository.exists_by_field(DatabaseConstants.TABLE_LOCATIONS, "id", location_id)
        except Exception as e:
            raise RuntimeError(str(e))

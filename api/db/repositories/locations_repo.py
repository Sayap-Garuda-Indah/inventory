from typing import Optional, List, Dict, Any
from db.pool import fetch_all, fetch_one, execute
from db.base import QueryBuilder, DatabaseUtils, BaseRepository, DatabaseConstants
from schemas.locations import LocationCreate, LocationUpdate

class LocationsRepository:
    DELETED_TX_NOTE_PREFIX = "__deleted__"

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
    def get_by_code(code: str) -> Optional[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_string(code, "code")
            query = """
                SELECT id, name, code, active
                FROM locations
                WHERE code = %s
            """
            return fetch_one(query, (code.strip(),))
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def get_by_name(name: str) -> Optional[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_string(name, "name")
            query = """
                SELECT id, name, code, active
                FROM locations
                WHERE name = %s
            """
            return fetch_one(query, (name.strip(),))
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def exists_by_id(location_id: int) -> bool:
        try:
            DatabaseUtils.validate_id(location_id, "Location")
            return BaseRepository.exists_by_field(DatabaseConstants.TABLE_LOCATIONS, "id", location_id)
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def exists_by_name(name: str, exclude_id: Optional[int] = None) -> bool:
        try:
            DatabaseUtils.validate_string(name, "name")
            if exclude_id is not None:
                DatabaseUtils.validate_id(exclude_id, "Location")
            return BaseRepository.exists_by_field(DatabaseConstants.TABLE_LOCATIONS, "name", name.strip(), exclude_id)
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def exists_by_code(code: str, exclude_id: Optional[int] = None) -> bool:
        try:
            DatabaseUtils.validate_string(code, "code")
            if exclude_id is not None:
                DatabaseUtils.validate_id(exclude_id, "Location")
            return BaseRepository.exists_by_field(DatabaseConstants.TABLE_LOCATIONS, "code", code.strip(), exclude_id)
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def create(location_data: LocationCreate) -> Dict[str, Any]:
        try:
            query = """
                INSERT INTO locations (name, code, active)
                VALUES (%s, %s, %s)
            """
            execute(query, (location_data.name, location_data.code, bool(location_data.active)))
            location = LocationsRepository.get_by_code(location_data.code)
            if not location:
                raise RuntimeError("Failed to retrieve created location.")
            return location
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def update(location_id: int, location_data: LocationUpdate) -> Optional[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_id(location_id, "Location")
            set_clause = []
            params: List[Any] = []

            if location_data.name is not None:
                set_clause.append("name = %s")
                params.append(location_data.name)

            if location_data.code is not None:
                set_clause.append("code = %s")
                params.append(location_data.code)

            if location_data.active is not None:
                set_clause.append("active = %s")
                params.append(bool(location_data.active))

            if not set_clause:
                return LocationsRepository.get_by_id(location_id)

            params.append(location_id)
            query = f"""
                UPDATE locations
                SET {', '.join(set_clause)}
                WHERE id = %s
            """
            rows = execute(query, tuple(params))
            if rows <= 0:
                return None
            return LocationsRepository.get_by_id(location_id)
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def delete(location_id: int) -> bool:
        try:
            DatabaseUtils.validate_id(location_id, "Location")
            query = "UPDATE locations SET active = 0 WHERE id = %s AND active = 1"
            rows = execute(query, (location_id,))
            return rows > 0
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def get_dependency_summary(location_id: int) -> Dict[str, int]:
        try:
            DatabaseUtils.validate_id(location_id, "Location")

            stock_levels = fetch_one(
                "SELECT COUNT(*) AS count FROM stock_levels WHERE location_id = %s",
                (location_id,),
            )
            stock_transactions = fetch_one(
                """
                SELECT COUNT(*) AS count
                FROM stock_tx
                WHERE location_id = %s
                  AND (note IS NULL OR note NOT LIKE %s)
                """,
                (location_id, f"{LocationsRepository.DELETED_TX_NOTE_PREFIX}%"),
            )
            audit_sessions = fetch_one(
                "SELECT COUNT(*) AS count FROM audit_sessions WHERE location_id = %s",
                (location_id,),
            )
            audit_scans = fetch_one(
                "SELECT COUNT(*) AS count FROM audit_scans WHERE location_id = %s",
                (location_id,),
            )

            return {
                "stock_levels": int(stock_levels["count"]) if stock_levels else 0,
                "stock_transactions": int(stock_transactions["count"]) if stock_transactions else 0,
                "audit_sessions": int(audit_sessions["count"]) if audit_sessions else 0,
                "audit_scans": int(audit_scans["count"]) if audit_scans else 0,
            }
        except Exception as e:
            raise RuntimeError(str(e))

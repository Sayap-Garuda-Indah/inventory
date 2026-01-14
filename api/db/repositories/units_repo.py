from typing import Optional, List, Dict, Any
from db.pool import fetch_all, fetch_one, execute
from db.base import QueryBuilder, DatabaseUtils, BaseRepository
from schemas.units import UnitCreate, UnitUpdate


class UnitsRepository:
    @staticmethod
    def get_all(
        limit: int = 100,
        offset: int = 0,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            conditions = []
            params = []

            search_term = DatabaseUtils.sanitize_search_term(search)
            search_condition, search_params = QueryBuilder.build_search_condition(search_term, ["name", "symbol"])
            if search_condition:
                conditions.append(search_condition)
                params.extend(search_params)
            
            where_clause, params = QueryBuilder.build_where_clause(conditions, params)
           
            query = f"""
                SELECT id, name, symbol, multiplier
                FROM units
                {where_clause}
                ORDER BY name
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            rows = fetch_all(query, tuple(params))

            return rows
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def count(search: Optional[str] = None) -> int:
        try:
            conditions = []
            params = []

            search_term = DatabaseUtils.sanitize_search_term(search)
            search_condition, search_params = QueryBuilder.build_search_condition(search_term, ["name", "symbol"])
            if search_condition:
                conditions.append(search_condition)
                params.extend(search_params)
            
            where_clause, params = QueryBuilder.build_where_clause(conditions, params)
           
            query = f"""
                SELECT COUNT(*) AS count
                FROM units
                {where_clause}
            """
            row = fetch_one(query, tuple(params))

            return row['count'] if row else 0
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def get_by_id(unit_id: int) -> Optional[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_id(unit_id, "Unit")
            query = "SELECT * FROM units WHERE id = %s"
            row = fetch_one(query, (unit_id,))
            
            return row
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def get_by_name(name: str) -> Optional[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_string(name, "name")
            
            query = "SELECT * FROM units WHERE name = %s"
            row = fetch_one(query, (name,))

            return row
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def get_by_symbol(symbol: str) -> Optional[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_string(symbol, "symbol")
            
            query = "SELECT * FROM units WHERE symbol = %s"
            row = fetch_one(query, (symbol,))

            return row
        except Exception as e:
            raise RuntimeError({str(e)})

        
    @staticmethod
    def create(unit_data: UnitCreate) -> Dict[str, Any]:
        try:
            query = """
                INSERT INTO units (name, symbol, description)
                VALUES (%s, %s, %s)
            """
            execute(query, (unit_data.name, unit_data.symbol, unit_data.multiplier))

            create_unit = UnitsRepository.get_by_name(unit_data.name)
            if not create_unit:
                raise RuntimeError("Failed to retrieve the newly created unit.")
            
            return create_unit
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def update(unit_id: int, unit_data: UnitUpdate) -> Optional[Dict[str, Any]]:
        try:
            DatabaseUtils.validate_id(unit_id, "Unit")
            
            # Dynamic update query
            set_clause = []
            params = []

            if unit_data.name is not None:
                set_clause.append("name = %s")
                params.append(unit_data.name)

            if unit_data.symbol is not None:
                set_clause.append("symbol = %s")
                params.append(unit_data.symbol)

            if unit_data.multiplier is not None:
                set_clause.append("description = %s")
                params.append(unit_data.multiplier)

            if not set_clause:
                # Nothing to update
                unit = UnitsRepository.get_by_id(unit_id)
                return unit

            params.append(unit_id)
            query = f"""
                UPDATE units
                SET {', '.join(set_clause)}
                WHERE id = %s
            """

            rows_affected = execute(query, tuple(params))

            if rows_affected > 0:
                return UnitsRepository.get_by_id(unit_id)
            
            return None
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def delete(unit_id: int) -> bool:
        try:
            DatabaseUtils.validate_id(unit_id, "Unit")
            
            check_query = "SELECT COUNT(1) AS count FROM units WHERE id = %s"
            result = fetch_one(check_query, (unit_id,))

            if result and result['count'] > 0:
                raise RuntimeError(f"Cannot delete unit with id {unit_id} as it is referenced by other records.")
            
            query = "DELETE FROM units WHERE id = %s"
            rows_affected = execute(query, (unit_id,))

            return rows_affected > 0
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def exists_by_name(name: str, exclude_id: Optional[int] = None) -> bool:
        try:
            DatabaseUtils.validate_string(name, "name")
            if exclude_id is not None:
                DatabaseUtils.validate_id(exclude_id, "Unit")
            return BaseRepository.exists_by_field("units", "name", name.strip(), exclude_id)
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def exists_by_symbol(symbol: str, exclude_id: Optional[int] = None) -> bool:
        try:
            DatabaseUtils.validate_string(symbol, "symbol")
            if exclude_id is not None:
                DatabaseUtils.validate_id(exclude_id, "Unit")
            return BaseRepository.exists_by_field("units", "symbol", symbol.strip(), exclude_id)
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def exists_by_id(unit_id: int) -> bool:
        try:
            DatabaseUtils.validate_id(unit_id, "Unit")
            return BaseRepository.exists_by_field("units", "id", unit_id)
        except Exception as e:
            raise RuntimeError({str(e)})

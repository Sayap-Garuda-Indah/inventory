from typing import Optional, List, Dict, Any
from db.pool import fetch_all, fetch_one, execute, execute_many
from db.base import QueryBuilder, DatabaseUtils
from schemas.users import UserCreate, UserUpdate
from datetime import datetime, timezone

class UserRepository:
    @staticmethod
    def get_all(
        active_only: bool = True, 
        limit: int = 50, 
        offset: int = 0, 
        search: Optional[str] = None
        ) -> List[Dict[str, Any]]:
        """
        Get all users with optional filtering
        """
        try:
            conditions = []
            params = []

            if active_only:
                conditions.append("active = %s")
                params.append(True)

            search_term = DatabaseUtils.sanitize_search_term(search)
            search_condition, search_params = QueryBuilder.build_search_condition(search_term, ["email", "name"])
            if search_condition:
                conditions.append(search_condition)
                params.extend(search_params)

            where_clause, params = QueryBuilder.build_where_clause(conditions, params)

            query = f"""
                SELECT id, email, password_hash, name, role, active, created_at
                FROM users
                {where_clause}
                ORDER BY email
                LIMIT %s OFFSET %s
                """

            params.extend([limit, offset])

            return fetch_all(query, tuple(params))
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def count(active_only: bool = True, search: Optional[str] = None) -> int:
        """
        Count users with optional filtering
        """
        try:
            conditions = []
            params = []

            if active_only:
                conditions.append("active = %s")
                params.append(True)

            search_term = DatabaseUtils.sanitize_search_term(search)
            search_condition, search_params = QueryBuilder.build_search_condition(search_term, ["email", "name"])
            if search_condition:
                conditions.append(search_condition)
                params.extend(search_params)

            where_clause, params = QueryBuilder.build_where_clause(conditions, params)

            query = f"SELECT COUNT(*) as count FROM users {where_clause}"
            result = fetch_one(query, tuple(params))

            if result:
                return result['count']
            else:
                return 0
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a user by internal ID
        """
        try:
            DatabaseUtils.validate_id(user_id, "User")
            
            query = """
                SELECT id, email, password_hash, name, role, active, created_at
                FROM users
                WHERE id = %s
                """
            result = fetch_one(query, (user_id,))

            return result
        except Exception as e:
            raise RuntimeError({str(e)})


    @staticmethod
    # def get_by_oid(m365_oid: str) -> Optional[Dict[str, Any]]:
    #     """
    #     Get a user by Microsoft 365 Object ID
    #     """
    #     try:
    #         if not m365_oid or not m365_oid.strip():
    #             raise ValueError("invalid m365_oid")
            
    #         query = """
    #             SELECT id, m365_oid, name, email, role, active, created_at
    #             FROM users
    #             WHERE m365_oid = %s
    #             """
    #         result = fetch_one(query, (m365_oid,))

    #         return result
    #     except Exception as e:
    #         raise RuntimeError(f"Error fetching user by OID: {str(e)}")

    @staticmethod
    def get_by_email(email: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by email
        """
        try:
            DatabaseUtils.validate_string(email, "email")
            
            query = """
                SELECT id, email, password_hash, name, role, active, created_at
                FROM users
                WHERE email = %s
                """
            result = fetch_one(query, (email,))

            return result
        except Exception as e:
            raise RuntimeError({str(e)})


    @staticmethod
    def create(user_data: UserCreate, password_hash: str) -> Optional[Dict[str, Any]]:
        """
        Create a new user
        """
        try:
            query = """
                INSERT INTO users (email, password_hash, name, role, active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
            result = execute(
                query,
                (
                    user_data.email.lower(),
                    password_hash,
                    user_data.name,
                    user_data.role.value,
                    user_data.active,
                    datetime.now(timezone.utc)
                )
            )

            # If execute returns the last inserted ID
            if result:
                return UserRepository.get_by_id(result)
            
            # Alternative: get by unique identifier if ID not returned
            return UserRepository.get_by_email(user_data.email.lower())
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def create_bulk(users_data: List[UserCreate], password_hashes: List[str]) -> List[Dict[str, Any]]:
        """
        Create multiple users in bulk
        """
        try:
            query = """
                INSERT INTO users (email, password_hash, name, role, active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
            params = []
            for user_data, password_hash in zip(users_data, password_hashes):
                params.append((
                    user_data.email.lower(),
                    password_hash,
                    user_data.name,
                    user_data.role.value,
                    user_data.active,
                    datetime.now(timezone.utc)
                ))
            
            execute_many(query, params)

            created_users = []
            for user_data in users_data:
                user = UserRepository.get_by_email(user_data.email.lower())
                if user:
                    created_users.append(user)
            
            return created_users
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def update(user_id: int, user_data: UserUpdate, password_hash: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Update an existing user
        """
        try:
            DatabaseUtils.validate_id(user_id, "User")
            
            set_clauses = []
            params = []

            if password_hash is not None:
                set_clauses.append("password_hash = %s")
                params.append(password_hash)

            if user_data.name is not None:
                set_clauses.append("name = %s")
                params.append(user_data.name)

            if user_data.email is not None:
                set_clauses.append("email = %s")
                params.append(user_data.email.lower())

            if user_data.role is not None:
                set_clauses.append("role = %s")
                params.append(user_data.role.value)

            if user_data.active is not None:
                set_clauses.append("active = %s")
                params.append(user_data.active)

            if not set_clauses:
                raise ValueError("No fields to update")

            params.append(user_id)
            set_clause = ", ".join(set_clauses)

            query = f"""
                UPDATE users
                SET {set_clause}
                WHERE id = %s
            """

            rows_affected = execute(query, tuple(params))
            if rows_affected > 0:
                return UserRepository.get_by_id(user_id)
            else:
                return None
        except Exception as e:
            raise RuntimeError({str(e)})


    @staticmethod
    def delete(user_id: int) -> bool:
        """
        Soft delete user (set active = False)
        """
        try:
            if not isinstance(user_id, int) or user_id <= 0:
                raise ValueError("invalid user id")
            
            query = "UPDATE users SET active = %s WHERE id = %s"
            rows_affected = execute(query, (False, user_id))

            if rows_affected > 0:
                return True

            return False
        except Exception as e:
            raise RuntimeError({str(e)})

    @staticmethod
    def exists_by_id(user_id: int, exclude_id: Optional[int] = None) -> bool:
        """
        Check if a user exists by ID
        """
        try:
            if not isinstance(user_id, int) or user_id <= 0:
                return False
            
            if exclude_id:
                result = fetch_one(
                    "SELECT COUNT(*) as count FROM users WHERE id = %s AND id != %s",
                    (user_id, exclude_id)
                )
            else:
                result = fetch_one(
                    "SELECT COUNT(*) as count FROM users WHERE id = %s",
                    (user_id,)
                )
            
            if result and result['count'] > 0:
                return True
            
            return False
        except Exception as e:
            raise RuntimeError({str(e)})

    # @staticmethod
    # def exists_by_username(username: str, exclude_id: Optional[int] = None) -> bool:
    #     """
    #     Check if a user exists by username
    #     """
    #     try:
    #         if not username or not username.strip():
    #             return False
            
    #         if exclude_id:
    #             result = fetch_one(
    #                 "SELECT COUNT(*) as count FROM users WHERE username = %s AND id != %s",
    #                 (username, exclude_id)
    #             )
    #         else:
    #             result = fetch_one(
    #                 "SELECT COUNT(*) as count FROM users WHERE username = %s",
    #                 (username,)
    #             )
            
    #         if result and result['count'] > 0:
    #             return True
            
    #         return False
    #     except Exception as e:
    #         raise RuntimeError({str(e)})

    @staticmethod
    def exists_by_email(email: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if a user exists by email
        """
        try:
            if not email or not email.strip():
                return False
            
            if exclude_id:
                result = fetch_one(
                    "SELECT COUNT(*) as count FROM users WHERE email = %s AND id != %s",
                    (email, exclude_id)
                )
            else:
                result = fetch_one(
                    "SELECT COUNT(*) as count FROM users WHERE email = %s",
                    (email,)
                )
            
            if result and result['count'] > 0:
                return True
            
            return False
        except Exception as e:
            raise RuntimeError({str(e)})

    # @staticmethod
    # def exists_by_oid(m365_oid: str, exclude_id: Optional[int] = None) -> bool:
    #     """
    #     Check if user with Microsoft 365 Object ID exists
    #     """
    #     try:
    #         if not m365_oid or not m365_oid.strip():
    #             return False
            
    #         if exclude_id:
    #             result = fetch_one(
    #                 "SELECT COUNT(*) as count FROM users WHERE m365_oid = %s AND id != %s",
    #                 (m365_oid, exclude_id)
    #             )
    #         else:
    #             result = fetch_one(
    #                 "SELECT COUNT(*) as count FROM users WHERE m365_oid = %s",
    #                 (m365_oid,)
    #             )
            
    #         if result and result['count'] > 0:
    #             return True

    #         return False
    #     except Exception as e:
    #         raise RuntimeError(f"Error checking user existence by OID: {str(e)}")
    
    @staticmethod
    def de_activate_user(user_id: int, active: int) -> bool:
        """
        Deactivate or activate user (set active = 1)
        """
        try:
            if not isinstance(user_id, int) or user_id <= 0:
                raise ValueError("invalid user id")
            
            query = "UPDATE users SET active = %s WHERE id = %s"
            rows_affected = execute(query, (active, user_id))

            if rows_affected > 0:
                return True
            
            return False
        except Exception as e:
            raise RuntimeError({str(e)})

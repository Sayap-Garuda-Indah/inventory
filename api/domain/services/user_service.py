from typing import Optional
from fastapi import HTTPException, status
from db.repositories.user_repo import UserRepository
from schemas.users import UserCreate, UserUpdate, UserResponse, UserListResponse, UserLogin, TokenResponse
from core.security.password import hash_password, verify_password
from core.security.jwt import create_access_token
from datetime import timedelta
from core.config import settings

class UserService:
    
    @staticmethod
    def get_all_users(
        active_only: bool = True,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None
    ) -> UserListResponse:
        """
        Get paginated list of users with optional filtering by active status and search term.
        """
        try:
            if page < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Page number must be greater than 0."
                )
            
            if page_size < 1 or page_size > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Page size must be between 1 and 100."
                )
            
            offset = (page - 1) * page_size
            users_data = UserRepository.get_all(
                active_only=active_only,
                limit=page_size,
                offset=offset,
                search=search
            )

            total = UserRepository.count(active_only=active_only, search=search)
            users = [UserResponse(**user) for user in users_data]

            results = UserListResponse(
                users=users,
                total=total,
                page=page,
                page_size=page_size
            )

            return results
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve users: {str(e)}"
            )
    
    @staticmethod
    def get_user_by_id(user_id: int) -> UserResponse:
        """
        Get a single user by their ID.
        """
        try:
            if not isinstance(user_id, int) or user_id <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User ID must be a positive integer."
                )
            
            user_data = UserRepository.get_by_id(user_id)
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found."
                )
            
            result = UserResponse(**user_data)

            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve user: {str(e)}"
            )
        
    @staticmethod
    def authenticate_user(login_date: UserLogin) -> TokenResponse:
        """
        Authenticate user and return JWT token.
        """
        try:
            user_data = UserRepository.get_by_email(login_date.email)

            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password."
                )
            
            if not verify_password(login_date.password, user_data['password_hash']):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password."
                )

            if not user_data['active']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive."
                )
            
            # Create JWT Access Token
            access_token = create_access_token(
                data={
                    "sub": user_data['email'],
                    "user_id": user_data['id'],
                    "role": user_data['role']
                },
                expires_delta=timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
            )

            token_response = TokenResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.JWT_EXPIRE_MINUTES * 60
            )

            return token_response
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to authenticate user: {str(e)}"
            )

    @staticmethod
    def create_user(user_data: UserCreate) -> UserResponse:
        """
        Create a new user.
        """
        # Check for existing user with same email
        existing_user_by_email = UserRepository.exists_by_email(user_data.email)
        if existing_user_by_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {user_data.email} already exists."
            )
        
        try:
            password_hash = hash_password(user_data.password)
            created_user = UserRepository.create(user_data=user_data, password_hash=password_hash)
            if not created_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user."
                )
                
            result = UserResponse(**created_user)
            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {str(e)}"
            )

    @staticmethod
    def create_bulk_users(users_data: list[UserCreate]) -> list[UserResponse]:
        """
        Create multiple users in bulk.
        """
        created_users = []
        password_hashes = []
        try:
            for user_data in users_data:
                # Check for existing user with same email
                if UserRepository.exists_by_email(user_data.email):
                    continue # skip existing users

                password_hashes.append(hash_password(user_data.password))
            
            response = UserRepository.create_bulk(users_data, password_hashes)

            for user in response:
                created_users.append(UserResponse(**user))

            return created_users
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create bulk users: {str(e)}"
            )

    @staticmethod
    def update_user(user_id: int, user_data: UserUpdate) -> UserResponse:
        """
        Update an existing user.
        """
        try:
            if not user_data.model_dump(exclude_unset=True):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one field is required to update a user."
                )

            existing_user = UserRepository.get_by_id(user_id)
            if not existing_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found."
                )
            
            # Check email uniqueness if email is being updated
            if user_data.email and user_data.email != existing_user['email']:
                if UserRepository.exists_by_email(user_data.email, exclude_id=user_id):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"User with email {user_data.email} already exists."
                    )
                
            password_hash = None
            if user_data.password:
                password_hash = hash_password(user_data.password)

            updated_user = UserRepository.update(user_id, user_data, password_hash=password_hash)
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user."
                )
            result = UserResponse(**updated_user)

            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve user for update: {str(e)}"
            )
        
    @staticmethod
    def delete_user(user_id: int) -> dict:
        """
        Soft delete a user by setting active to False.
        """
        try:
            if not isinstance(user_id, int) or user_id <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User ID must be a positive integer."
                )
            
            existing_user = UserRepository.get_by_id(user_id)
            if not existing_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found."
                )
            
            # Prevent deleting already inactive users
            if existing_user['active'] == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User with ID {user_id} is already inactive."
                )
            
            success = UserRepository.delete(user_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete user."
                )
            
            response = {"message": f"User {existing_user['name']} has been deactivated."}
            
            return response
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve user for deletion: {str(e)}"
            )
        
    # @staticmethod
    # def get_or_create_user(m365_oid: str, name: str, email: str) -> UserResponse:
    #     """
    #     Get a user by email or create if not exists.
    #     """
    #     try:
    #         existing_user = UserRepository.get_by_email(email)

    #         if existing_user:
    #             result = UserResponse(**existing_user)
    #             return result
            
    #         # Auto-create user with STAFF role
    #         user_data = UserCreate(
    #             username=name,
    #             password="",
    #             name=name,
    #             email=email,
    #             role=UserRole.STAFF,
    #             active=1
    #         )
            
    #         created_user = UserRepository.create(user_data, password_hash="")

    #         return UserResponse(**created_user)
    #     except HTTPException:
    #         raise
    #     except Exception as e:
    #         raise HTTPException(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             detail=f"Failed to retrieve or create user: {str(e)}"
    #         )
        
    @staticmethod
    def activate_user(user_id: int, activate: int) -> bool:
        """
        Activate a user by setting active to 1.
        """
        try:
            existing_user = UserRepository.get_by_id(user_id)
            if not existing_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found."
                )
            
            activated_user = UserRepository.de_activate_user(user_id, active=activate)
            if not activated_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to activate user."
                )
            
            result = activated_user

            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to activate user: {str(e)}"
            )
            
    @staticmethod
    def deactivate_user(user_id: int, deactivate: int) -> bool:
        """
        Deactivate a user by setting active to 0.
        """
        try:
            existing_user = UserRepository.get_by_id(user_id)
            if not existing_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found."
                )
            
            deactivated_user = UserRepository.de_activate_user(user_id, active=deactivate)
            if not deactivated_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to deactivate user."
                )
            
            result = deactivated_user

            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to deactivate user: {str(e)}"
            )

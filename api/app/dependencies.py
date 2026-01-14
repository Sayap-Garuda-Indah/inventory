from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.security.jwt import verify_access_token
from db.repositories.user_repo import UserRepository
from core.logging import get_logger
# from db.pool import fetch_one, execute

logger = get_logger(__name__)
bearer = HTTPBearer(auto_error=False)

def get_current_user(request: Request, credential: HTTPAuthorizationCredentials = Depends(bearer)):
    if not credential or not credential.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token")

    # Upsert user into DB
    try:
        payload = verify_access_token(token=credential.credentials)
        user_id = payload.get('user_id')

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid token payload"
            )
        
        user = UserRepository.get_by_id(user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="User not found"
            )

        if not user['active']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="User inactive or not found"
            )

        result = {
            "id": user['id'],
            "email": user['email'],
            "name": user['name'],
            "role": user['role'],
            "active": user['active']
        }

        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

def require_role(*roles):
    def checker(user=Depends(get_current_user)):
        if user["role"] not in roles:
            logger.warning(
                "Access denied",
                extra={
                    "user_role": user["role"],
                    "required_roles": roles
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Insufficient permissions"
            )
        return user
    return checker
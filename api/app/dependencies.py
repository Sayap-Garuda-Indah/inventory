from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.security.jwt import verify_access_token
from db.repositories.user_repo import UserRepository
from core.logging import get_logger
# from db.pool import fetch_one, execute

logger = get_logger(__name__)
bearer = HTTPBearer(auto_error=False)
AUTH_HEADERS = {"WWW-Authenticate": "Bearer"}

def get_current_user(request: Request, credential: HTTPAuthorizationCredentials = Depends(bearer)):
    if not credential or not credential.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers=AUTH_HEADERS,
        )

    try:
        payload = verify_access_token(token=credential.credentials)
        user_id = payload.get('user_id')

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers=AUTH_HEADERS,
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
        logger.warning(
            "Token verification failed",
            extra={
                "path": str(request.url.path),
                "client_ip": getattr(request.client, 'host', 'unknown') if request.client else 'unknown',
                "error": str(e),
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers=AUTH_HEADERS,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Authentication error",
            extra={
                "path": str(request.url.path),
                "client_ip": getattr(request.client, 'host', 'unknown') if request.client else 'unknown',
                "error": str(e),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
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

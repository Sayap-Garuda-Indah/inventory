from fastapi import APIRouter, HTTPException, Depends, status
from schemas.settings import SettingsUpdate, SettingsUpdate, SettingsResponse
from domain.services.settings_service import SettingsService
from app.dependencies import require_role
from schemas.users import UserRole
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/", response_model=SettingsResponse)
def get_settings(current_user= Depends(require_role(UserRole.ADMIN))) -> SettingsResponse:
    """
    Retrieve application settings. Accessible only by ADMIN users.
    """
    try:
        logger.info(
            "Settings requested",
            extra={
                "requested_by": current_user['id'],
                "requestor_email": current_user['email']
            }
        )
        settings = SettingsService.get_settings()
        
        return settings
    except Exception as e:
        logger.error(f"Error retrieving settings: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve settings.")
    
@router.put("/", response_model=SettingsResponse)
def update_settings(
    settings_data: SettingsUpdate,
    current_user= Depends(require_role(UserRole.ADMIN))
) -> SettingsResponse:
    """
    Update application settings. Accessible only by ADMIN users.
    """
    try:
        logger.info(
            "Settings update requested",
            extra={
                "requested_by": current_user['id'],
                "requestor_email": current_user['email'],
                "updated_fields": list(settings_data.model_dump(exclude_unset=True).keys())
            }
        )
        update_settings = SettingsService.update_settings(settings_data, current_user['id'])

        return update_settings
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update settings.")
    
@router.post("/backup", status_code=status.HTTP_200_OK)
def trigger_backup(current_user= Depends(require_role(UserRole.ADMIN))) -> dict:
    """
    Trigger a manual backup of the application data. Accessible only by ADMIN users.
    """
    try:
        logger.info(
            "Backup trigger requested",
            extra={
                "triggered_by": current_user['id'],
                "requestor_email": current_user['email']
            }
        )

        return SettingsService.trigger_backup()
    except Exception as e:
        logger.error(f"Error triggering backup: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to trigger backup.")
    
@router.get("/system-info")
def get_system_info(current_user= Depends(require_role(UserRole.ADMIN))) -> dict:
    """
    Retrieve system information such as CPU and memory usage. Accessible only by ADMIN users.
    """
    try:
        logger.info(
            "System info requested",
            extra={
                "requested_by": current_user['id'],
                "requestor_email": current_user['email']
            }
        )
        system_info = SettingsService.get_system_info()

        return system_info
    except Exception as e:
        logger.error(f"Error retrieving system info: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve system info.")
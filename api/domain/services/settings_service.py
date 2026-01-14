from typing import Optional
from fastapi import HTTPException, status
from db.repositories.settings_repo import SettingsRepository
from schemas.settings import SettingsUpdate, SettingsResponse
from core.logging import get_logger
import platform
import psutil
from datetime import datetime
import subprocess

logger = get_logger(__name__)

class SettingsService:
    @staticmethod
    def get_settings() -> SettingsResponse:
        try:
            settings_data = SettingsRepository.get()

            if not settings_data:
                # initialize default settings
                SettingsRepository.initialize_defaults()
                settings_data = SettingsRepository.get()

            if not settings_data:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve settings.")
            
            return SettingsResponse(**settings_data)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving settings: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while retrieving settings.")
        
    @staticmethod
    def update_settings(
        settings_data: SettingsUpdate,
        user_id: int
    ) -> SettingsResponse:
        try:
            updated_data = SettingsRepository.update(settings_data, user_id)

            if not updated_data:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update settings.")
            
            logger.info(
                "Settings updated successfully",
                extra={
                    "user_id": user_id, 
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            return SettingsResponse(**updated_data)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while updating settings.")
        
    @staticmethod
    def trigger_backup() -> dict:
        try:
            logger.info(
                "Manual backup triggered", 
                extra={
                    "timestamp": datetime.now().isoformat()
                }
            )
            init_backup = SettingsRepository.initialize_defaults()
            if init_backup:
                response = {
                    "message": "Backup process started successfully",
                    "timestamp": datetime.now().isoformat()
                }
                return response
            else:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initiate backup process.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error triggering backup: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while triggering backup.")
        
    @staticmethod
    def get_system_info() -> dict:
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            system_info = {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(logical=True),
                "cpu_usage_percent": cpu_usage,
                "memory_total_gb": round(memory.total / (1024 ** 3), 2),
                "memory_used_gb": round(memory.used / (1024 ** 3), 2),
                "memory_usage_percent": memory_usage,
                "disk_total_gb": round(psutil.disk_usage('/').total / (1024 ** 3), 2),
                "disk_used_gb": round(psutil.disk_usage('/').used / (1024 ** 3), 2),
                "disk_usage_percent": psutil.disk_usage('/').percent,
                "uptime": subprocess.check_output("uptime", shell=True).decode().strip()
            }

            return system_info
        except Exception as e:
            logger.error(f"Error retrieving system info: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while retrieving system info.")
            
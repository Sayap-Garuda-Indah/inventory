from typing import Optional, Dict, Any
from db.pool import fetch_one, execute
from schemas.settings import SettingsUpdate

class SettingsRepository:
    @staticmethod
    def get() -> Optional[Dict[str, Any]]:
        try:
            query = """
                    SELECT
                        id, app_name, items_per_page, allow_negative_stock,
                        auto_backup_enabled, backup_retention_days, low_stock_threshold,
                        enable_notifications, updated_at, updated_by
                    FROM settings
                    WHERE id = 1;
                    """
            result = fetch_one(query)

            return result
        except Exception as e:
            raise RuntimeError(str(e))
        
    @staticmethod
    def update(
        settings_data: SettingsUpdate,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        try:
            updates = []
            params = []

            if settings_data.app_name is not None:
                updates.append("app_name = %s")
                params.append(settings_data.app_name)

            if settings_data.items_per_page is not None:
                updates.append("items_per_page = %s")
                params.append(settings_data.items_per_page)

            if settings_data.allow_negative_stock is not None:
                updates.append("allow_negative_stock = %s")
                params.append(settings_data.allow_negative_stock)

            if settings_data.auto_backup_enabled is not None:
                updates.append("auto_backup_enabled = %s")
                params.append(settings_data.auto_backup_enabled)

            if settings_data.backup_retention_days is not None:
                updates.append("backup_retention_days = %s")
                params.append(settings_data.backup_retention_days)

            if settings_data.low_stock_threshold is not None:
                updates.append("low_stock_threshold = %s")
                params.append(settings_data.low_stock_threshold)

            if settings_data.enable_notifications is not None:
                updates.append("enable_notifications = %s")
                params.append(settings_data.enable_notifications)

            if not updates:
                response = SettingsRepository.get()

                return response
            
            updates.append("updated_by = %s")
            params.append(user_id)
            updates.append("updated_at = NOW()")

            query = f"""
                    UPDATE settings
                    SET {', '.join(updates)}
                    WHERE id = 1
                    """
            
            execute(query, tuple(params))
            response = SettingsRepository.get()

            return response
        except Exception as e:
            raise RuntimeError(str(e))
        
    @staticmethod
    def initialize_defaults() -> bool:
        try:
            query = """
                    INSERT INTO settings 
                    (id, app_name, items_per_page, allow_negative_stock,
                     auto_backup_enabled, backup_retention_days, low_stock_threshold, enable_notifications)
                    VALUES
                    (1, 'Inventory Management System', 50, 0, 1, 30, 10, 1)
                    ON DUPLICATE KEY UPDATE id = id;
                    """
            execute(query)

            return True
        except Exception as e:
            raise RuntimeError(str(e))

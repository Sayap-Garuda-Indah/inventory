from typing import Optional, Dict, Any
from db.pool import execute
from db.base import DatabaseUtils

import json

class AuditLogRepository:
    @staticmethod
    def create(
        actor_user_id: int,
        action: str,
        entity_type: str,
        entity_id: Optional[int],
        session_id: Optional[int],
        payload_json: Optional[Dict[str, Any]]
    ) -> None:
        try:
            DatabaseUtils.validate_id(actor_user_id, 'User')
            query = """
            INSERT INTO audit_log
            (actor_user_id, action, entity_type, entity_id, session_id, payload_json)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = (
                actor_user_id,
                action,
                entity_type,
                entity_id,
                session_id,
                json.dumps(payload_json) if payload_json else None
            )
            execute(query, params)
        except Exception as e:
            raise RuntimeError(str(e))
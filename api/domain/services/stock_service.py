from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from db.pool import get_transaction_cursor
from db.repositories.item_repo import ItemRepository
from db.repositories.locations_repo import LocationsRepository
from db.repositories.stock_levels_repo import StockLevelsRepository
from db.repositories.stock_tx_repo import StockTxRepository
from db.repositories.settings_repo import SettingsRepository
from db.repositories.user_repo import UserRepository
from schemas.users import UserRole
from schemas.stock_tx import StockTxCreate, StockTxUpdate, StockTxListResponse, StockTxResponse
from schemas.stock_levels import StockLevelListResponse, StockLevelResponse
from core.logging import get_logger

logger = get_logger(__name__)

class StockService:
    @staticmethod
    def _is_staff(current_user: Optional[Dict[str, Any]]) -> bool:
        return bool(current_user) and str(current_user.get("role", "")).upper() == UserRole.STAFF.value

    @staticmethod
    def _owner_scope(current_user: Optional[Dict[str, Any]]) -> Optional[int]:
        if StockService._is_staff(current_user):
            return int(current_user["id"])
        return None

    @staticmethod
    def _assert_staff_item_ownership(item_id: int, current_user: Optional[Dict[str, Any]]) -> None:
        if not StockService._is_staff(current_user):
            return

        item = ItemRepository.get_by_id(item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        if item.get("owner_user_id") != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="STAFF can only access transactions for their own items",
            )

    @staticmethod
    def _assert_transaction_access(existing_tx: Dict[str, Any], current_user: Optional[Dict[str, Any]]) -> None:
        if not StockService._is_staff(current_user):
            return
        StockService._assert_staff_item_ownership(int(existing_tx["item_id"]), current_user)

    @staticmethod
    def _resolve_target_owner_user_id(
        payload_user_id: Optional[int],
        fallback_user_id: Optional[int],
        current_user: Optional[Dict[str, Any]],
    ) -> int:
        selected_user_id = payload_user_id if payload_user_id is not None else fallback_user_id
        if selected_user_id is None and current_user:
            selected_user_id = current_user.get("id")
        if not isinstance(selected_user_id, int) or selected_user_id <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid owner user ID")
        return selected_user_id

    @staticmethod
    def _validate_target_owner_user(owner_user_id: int) -> None:
        owner_user = UserRepository.get_by_id(owner_user_id)
        if not owner_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner user not found")
        if not owner_user.get("active", False):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner user is inactive")

    @staticmethod
    def _set_item_owner(cursor, item_id: int, owner_user_id: int) -> None:
        cursor.execute(
            """
            UPDATE items
            SET owner_user_id = %s
            WHERE id = %s AND active = 1
            """,
            (owner_user_id, item_id),
        )
        if cursor.rowcount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update item owner")

    @staticmethod
    def list_transactions(
        page: int = 1,
        page_size: int = 50,
        item_id: Optional[int] = None,
        location_id: Optional[int] = None,
        tx_type: Optional[str] = None,
        search: Optional[str] = None,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> StockTxListResponse:
        if page < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Page number must be at least 1")
        if page_size < 1 or page_size > 100:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Page size must be between 1 and 100")

        if item_id is not None:
            StockService._assert_staff_item_ownership(item_id, current_user)

        owner_scope = StockService._owner_scope(current_user)
        txs = StockTxRepository.list_transactions(
            page=page,
            page_size=page_size,
            item_id=item_id,
            location_id=location_id,
            tx_type=tx_type,
            search=search,
            owner_user_id=owner_scope,
        )
        total = StockTxRepository.count_transactions(
            item_id=item_id,
            location_id=location_id,
            tx_type=tx_type,
            search=search,
            owner_user_id=owner_scope,
        )
        return StockTxListResponse(
            txs=[StockTxResponse(**tx) for tx in txs],
            total=total,
            page=page,
            page_size=page_size
        )

    @staticmethod
    def list_stock_levels(
        page: int = 1,
        page_size: int = 50,
        item_id: Optional[int] = None,
        location_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> StockLevelListResponse:
        if page < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Page number must be at least 1")
        if page_size < 1 or page_size > 100:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Page size must be between 1 and 100")

        levels = StockLevelsRepository.list_levels(
            page=page,
            page_size=page_size,
            item_id=item_id,
            location_id=location_id,
            search=search
        )
        total = StockLevelsRepository.count_levels(item_id=item_id, location_id=location_id, search=search)
        return StockLevelListResponse(
            levels=[StockLevelResponse(**level) for level in levels],
            total=total,
            page=page,
            page_size=page_size
        )

    @staticmethod
    def get_transaction(tx_id: int, current_user: Optional[Dict[str, Any]] = None) -> StockTxResponse:
        tx = StockTxRepository.get_by_id(tx_id)
        if not tx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        StockService._assert_transaction_access(tx, current_user)
        return StockTxResponse(**tx)

    @staticmethod
    def create_transaction(tx_data: StockTxCreate, current_user: Dict[str, Any]) -> StockTxResponse:
        StockService._validate_tx_inputs(tx_data.item_id, tx_data.location_id, tx_data.tx_type, tx_data.qty)

        if not ItemRepository.exists_by_id(tx_data.item_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item not found")
        if not LocationsRepository.exists_by_id(tx_data.location_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Location not found")
        StockService._assert_staff_item_ownership(tx_data.item_id, current_user)
        owner_user_id = StockService._resolve_target_owner_user_id(
            tx_data.user_id,
            fallback_user_id=None,
            current_user=current_user,
        )
        StockService._validate_target_owner_user(owner_user_id)

        allow_negative = StockService._allow_negative_stock()

        with get_transaction_cursor(dictionary=True) as cursor:
            current_qty = StockService._get_qty_for_update(cursor, tx_data.item_id, tx_data.location_id)
            new_qty = StockService._apply_effect(current_qty, tx_data.tx_type, tx_data.qty)

            if not allow_negative and new_qty < 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock for transaction")

            StockService._upsert_stock_level(cursor, tx_data.item_id, tx_data.location_id, new_qty)
            StockService._set_item_owner(cursor, tx_data.item_id, owner_user_id)

            cursor.execute(
                """
                INSERT INTO stock_tx (item_id, location_id, tx_type, qty, ref, note, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    tx_data.item_id,
                    tx_data.location_id,
                    tx_data.tx_type,
                    tx_data.qty,
                    tx_data.ref,
                    tx_data.note,
                    owner_user_id,
                ),
            )
            tx_id = cursor.lastrowid

        created = StockTxRepository.get_by_id(int(tx_id))
        if not created:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create transaction")
        created["qty_on_hand"] = new_qty
        return StockTxResponse(**created)

    @staticmethod
    def update_transaction(tx_id: int, tx_data: StockTxUpdate, current_user: Optional[Dict[str, Any]] = None) -> StockTxResponse:
        existing = StockTxRepository.get_by_id(tx_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        StockService._assert_transaction_access(existing, current_user)

        next_item_id = tx_data.item_id if tx_data.item_id is not None else existing["item_id"]
        next_location_id = tx_data.location_id if tx_data.location_id is not None else existing["location_id"]
        next_tx_type = tx_data.tx_type if tx_data.tx_type is not None else existing["tx_type"]
        next_qty = tx_data.qty if tx_data.qty is not None else float(existing["qty"])
        next_owner_user_id = StockService._resolve_target_owner_user_id(
            tx_data.user_id,
            fallback_user_id=existing.get("user_id"),
            current_user=current_user,
        )

        StockService._validate_tx_inputs(next_item_id, next_location_id, next_tx_type, next_qty)

        if not ItemRepository.exists_by_id(next_item_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item not found")
        if not LocationsRepository.exists_by_id(next_location_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Location not found")
        StockService._assert_staff_item_ownership(int(next_item_id), current_user)
        StockService._validate_target_owner_user(next_owner_user_id)

        allow_negative = StockService._allow_negative_stock()

        with get_transaction_cursor(dictionary=True) as cursor:
            StockService._reverse_transaction(
                cursor,
                existing["item_id"],
                existing["location_id"],
                existing["tx_type"],
                float(existing["qty"]),
                allow_negative,
            )

            updated_qty = StockService._apply_new_transaction(
                cursor,
                next_item_id,
                next_location_id,
                next_tx_type,
                float(next_qty),
                allow_negative,
            )
            StockService._set_item_owner(cursor, int(next_item_id), next_owner_user_id)

            cursor.execute(
                """
                UPDATE stock_tx
                SET item_id = %s, location_id = %s, tx_type = %s, qty = %s, ref = %s, note = %s, user_id = %s
                WHERE id = %s
                """,
                (
                    next_item_id,
                    next_location_id,
                    next_tx_type,
                    next_qty,
                    tx_data.ref if tx_data.ref is not None else existing["ref"],
                    tx_data.note if tx_data.note is not None else existing["note"],
                    next_owner_user_id,
                    tx_id,
                ),
            )

        updated = StockTxRepository.get_by_id(tx_id)
        if not updated:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update transaction")
        updated["qty_on_hand"] = updated_qty
        return StockTxResponse(**updated)

    @staticmethod
    def delete_transaction(tx_id: int, current_user: Optional[Dict[str, Any]] = None) -> dict:
        existing = StockTxRepository.get_by_id(tx_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        StockService._assert_transaction_access(existing, current_user)

        allow_negative = StockService._allow_negative_stock()

        with get_transaction_cursor(dictionary=True) as cursor:
            StockService._reverse_transaction(
                cursor,
                existing["item_id"],
                existing["location_id"],
                existing["tx_type"],
                float(existing["qty"]),
                allow_negative,
            )
            deleted_note = (
                f"{StockTxRepository.DELETED_NOTE_PREFIX} "
                f"{existing.get('note') or ''}"
            ).strip()[:255]
            cursor.execute(
                """
                UPDATE stock_tx
                SET note = %s
                WHERE id = %s
                  AND (note IS NULL OR note NOT LIKE %s)
                """,
                (deleted_note, tx_id, f"{StockTxRepository.DELETED_NOTE_PREFIX}%"),
            )
            if cursor.rowcount <= 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to soft delete transaction",
                )

        return {
            "message": "Transaction soft-deleted successfully",
            "warning": "Stock impact from this transaction has been reversed; the transaction is hidden from active list.",
            "transaction_id": tx_id,
        }

    @staticmethod
    def _validate_tx_inputs(item_id: int, location_id: int, tx_type: str, qty: float) -> None:
        if not isinstance(item_id, int) or item_id <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid item ID")
        if not isinstance(location_id, int) or location_id <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid location ID")
        if tx_type not in ["IN", "OUT", "ADJ", "XFER"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported transaction type")
        if qty == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be non-zero")
        if tx_type in ["IN", "OUT", "XFER"] and qty < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be positive for IN/OUT")

    @staticmethod
    def _allow_negative_stock() -> bool:
        settings = SettingsRepository.get()
        if not settings:
            SettingsRepository.initialize_defaults()
            settings = SettingsRepository.get()
        return bool(settings and settings.get("allow_negative_stock"))

    @staticmethod
    def _get_qty_for_update(cursor, item_id: int, location_id: int) -> float:
        cursor.execute(
            """
            SELECT qty_on_hand
            FROM stock_levels
            WHERE item_id = %s AND location_id = %s
            FOR UPDATE
            """,
            (item_id, location_id),
        )
        row = cursor.fetchone()
        if row:
            return float(row["qty_on_hand"])

        cursor.execute(
            """
            INSERT INTO stock_levels (item_id, location_id, qty_on_hand)
            VALUES (%s, %s, 0)
            """,
            (item_id, location_id),
        )
        return 0.0

    @staticmethod
    def _apply_effect(current_qty: float, tx_type: str, qty: float) -> float:
        if tx_type == "IN":
            return current_qty + qty
        if tx_type in ["OUT", "XFER"]:
            return current_qty - qty
        return current_qty + qty

    @staticmethod
    def _upsert_stock_level(cursor, item_id: int, location_id: int, qty_on_hand: float) -> None:
        cursor.execute(
            """
            UPDATE stock_levels
            SET qty_on_hand = %s
            WHERE item_id = %s AND location_id = %s
            """,
            (qty_on_hand, item_id, location_id),
        )
        if cursor.rowcount == 0:
            cursor.execute(
                """
                INSERT INTO stock_levels (item_id, location_id, qty_on_hand)
                VALUES (%s, %s, %s)
                """,
                (item_id, location_id, qty_on_hand),
            )

    @staticmethod
    def _reverse_transaction(
        cursor,
        item_id: int,
        location_id: int,
        tx_type: str,
        qty: float,
        allow_negative: bool,
    ) -> None:
        current_qty = StockService._get_qty_for_update(cursor, item_id, location_id)
        if tx_type == "IN":
            new_qty = current_qty - qty
        elif tx_type in ["OUT", "XFER"]:
            new_qty = current_qty + qty
        else:
            new_qty = current_qty - qty

        if not allow_negative and new_qty < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Negative stock not allowed")

        StockService._upsert_stock_level(cursor, item_id, location_id, new_qty)

    @staticmethod
    def _apply_new_transaction(
        cursor,
        item_id: int,
        location_id: int,
        tx_type: str,
        qty: float,
        allow_negative: bool,
    ) -> float:
        current_qty = StockService._get_qty_for_update(cursor, item_id, location_id)
        new_qty = StockService._apply_effect(current_qty, tx_type, qty)

        if not allow_negative and new_qty < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock for transaction")

        StockService._upsert_stock_level(cursor, item_id, location_id, new_qty)
        return new_qty

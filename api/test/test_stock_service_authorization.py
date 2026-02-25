import pytest
from fastapi import HTTPException

from domain.services.stock_service import StockService
from schemas.stock_tx import StockTxCreate, StockTxUpdate


STAFF_USER = {
    "id": 10,
    "name": "Staff User",
    "email": "staff@example.com",
    "role": "STAFF",
    "active": True,
}

ADMIN_USER = {
    "id": 1,
    "name": "Admin User",
    "email": "admin@example.com",
    "role": "ADMIN",
    "active": True,
}


def test_list_transactions_staff_scopes_owner(monkeypatch):
    captured = {}

    def fake_list_transactions(**kwargs):
        captured["list"] = kwargs
        return []

    def fake_count_transactions(**kwargs):
        captured["count"] = kwargs
        return 0

    monkeypatch.setattr("domain.services.stock_service.StockTxRepository.list_transactions", fake_list_transactions)
    monkeypatch.setattr("domain.services.stock_service.StockTxRepository.count_transactions", fake_count_transactions)

    result = StockService.list_transactions(page=1, page_size=10, current_user=STAFF_USER)

    assert result.total == 0
    assert captured["list"]["owner_user_id"] == STAFF_USER["id"]
    assert captured["count"]["owner_user_id"] == STAFF_USER["id"]


def test_get_transaction_staff_forbidden_for_foreign_item(monkeypatch):
    monkeypatch.setattr(
        "domain.services.stock_service.StockTxRepository.get_by_id",
        lambda tx_id: {
            "id": tx_id,
            "item_id": 99,
            "item_code": "ITM-099",
            "item_name": "Foreign Item",
            "location_id": 1,
            "location_name": "Main",
            "tx_type": "IN",
            "qty": 1,
            "ref": None,
            "note": None,
            "tx_at": "2026-01-01T00:00:00",
            "user_id": 1,
            "qty_on_hand": 1,
        },
    )
    monkeypatch.setattr(
        "domain.services.stock_service.ItemRepository.get_by_id",
        lambda item_id: {"id": item_id, "owner_user_id": 999, "active": 1},
    )

    with pytest.raises(HTTPException) as exc:
        StockService.get_transaction(1, current_user=STAFF_USER)

    assert exc.value.status_code == 403


def test_create_transaction_staff_forbidden_for_foreign_item(monkeypatch):
    monkeypatch.setattr("domain.services.stock_service.ItemRepository.exists_by_id", lambda item_id: True)
    monkeypatch.setattr("domain.services.stock_service.LocationsRepository.exists_by_id", lambda location_id: True)
    monkeypatch.setattr(
        "domain.services.stock_service.ItemRepository.get_by_id",
        lambda item_id: {"id": item_id, "owner_user_id": 999, "active": 1},
    )

    with pytest.raises(HTTPException) as exc:
        StockService.create_transaction(
            StockTxCreate(item_id=1, location_id=1, tx_type="IN", qty=1, ref=None, note=None),
            current_user=STAFF_USER,
        )

    assert exc.value.status_code == 403


def test_create_transaction_defaults_owner_to_authenticated_user_id_when_missing(monkeypatch):
    captured = {"insert_params": None, "item_owner_update": None}

    class DummyCursor:
        def __init__(self):
            self.lastrowid = 123
            self.rowcount = 1

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params=None):
            if "INSERT INTO stock_tx" in query:
                captured["insert_params"] = params
            if "UPDATE items" in query and "owner_user_id" in query:
                captured["item_owner_update"] = params

    monkeypatch.setattr("domain.services.stock_service.ItemRepository.exists_by_id", lambda item_id: True)
    monkeypatch.setattr("domain.services.stock_service.LocationsRepository.exists_by_id", lambda location_id: True)
    monkeypatch.setattr(
        "domain.services.stock_service.UserRepository.get_by_id",
        lambda user_id: {"id": user_id, "name": "Any User", "active": True},
    )
    monkeypatch.setattr(
        "domain.services.stock_service.ItemRepository.get_by_id",
        lambda item_id: {"id": item_id, "owner_user_id": STAFF_USER["id"], "active": 1},
    )
    monkeypatch.setattr("domain.services.stock_service.StockService._allow_negative_stock", lambda: True)
    monkeypatch.setattr("domain.services.stock_service.StockService._get_qty_for_update", lambda cursor, item_id, location_id: 0.0)
    monkeypatch.setattr("domain.services.stock_service.StockService._apply_effect", lambda current_qty, tx_type, qty: current_qty + qty)
    monkeypatch.setattr("domain.services.stock_service.StockService._upsert_stock_level", lambda cursor, item_id, location_id, qty_on_hand: None)
    monkeypatch.setattr("domain.services.stock_service.get_transaction_cursor", lambda dictionary=True: DummyCursor())
    monkeypatch.setattr(
        "domain.services.stock_service.StockTxRepository.get_by_id",
        lambda tx_id: {
            "id": tx_id,
            "item_id": 1,
            "item_code": "ITM-001",
            "item_name": "Owned Item",
            "location_id": 1,
            "location_name": "Main",
            "tx_type": "IN",
            "qty": 5,
            "ref": None,
            "note": None,
            "tx_at": "2026-01-01T00:00:00",
            "user_id": STAFF_USER["id"],
            "qty_on_hand": 0,
        },
    )

    response = StockService.create_transaction(
        StockTxCreate(item_id=1, location_id=1, tx_type="IN", qty=5, ref=None, note=None),
        current_user=STAFF_USER,
    )

    assert response.user_id == STAFF_USER["id"]
    assert captured["insert_params"][-1] == STAFF_USER["id"]
    assert captured["item_owner_update"] == (STAFF_USER["id"], 1)


def test_create_transaction_uses_payload_owner_user_id_and_updates_item_owner(monkeypatch):
    captured = {"insert_params": None, "item_owner_update": None}

    class DummyCursor:
        def __init__(self):
            self.lastrowid = 124
            self.rowcount = 1

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params=None):
            if "INSERT INTO stock_tx" in query:
                captured["insert_params"] = params
            if "UPDATE items" in query and "owner_user_id" in query:
                captured["item_owner_update"] = params
                self.rowcount = 1

    monkeypatch.setattr("domain.services.stock_service.ItemRepository.exists_by_id", lambda item_id: True)
    monkeypatch.setattr("domain.services.stock_service.LocationsRepository.exists_by_id", lambda location_id: True)
    monkeypatch.setattr(
        "domain.services.stock_service.ItemRepository.get_by_id",
        lambda item_id: {"id": item_id, "owner_user_id": STAFF_USER["id"], "active": 1},
    )
    monkeypatch.setattr(
        "domain.services.stock_service.UserRepository.get_by_id",
        lambda user_id: {"id": user_id, "name": "Target Owner", "active": True},
    )
    monkeypatch.setattr("domain.services.stock_service.StockService._allow_negative_stock", lambda: True)
    monkeypatch.setattr("domain.services.stock_service.StockService._get_qty_for_update", lambda cursor, item_id, location_id: 0.0)
    monkeypatch.setattr("domain.services.stock_service.StockService._apply_effect", lambda current_qty, tx_type, qty: current_qty + qty)
    monkeypatch.setattr("domain.services.stock_service.StockService._upsert_stock_level", lambda cursor, item_id, location_id, qty_on_hand: None)
    monkeypatch.setattr("domain.services.stock_service.get_transaction_cursor", lambda dictionary=True: DummyCursor())
    monkeypatch.setattr(
        "domain.services.stock_service.StockTxRepository.get_by_id",
        lambda tx_id: {
            "id": tx_id,
            "item_id": 1,
            "item_code": "ITM-001",
            "item_name": "Owned Item",
            "location_id": 1,
            "location_name": "Main",
            "tx_type": "IN",
            "qty": 5,
            "ref": None,
            "note": None,
            "tx_at": "2026-01-01T00:00:00",
            "user_id": 77,
            "owner_name": "Target Owner",
            "qty_on_hand": 0,
        },
    )

    response = StockService.create_transaction(
        StockTxCreate(item_id=1, location_id=1, tx_type="IN", qty=5, user_id=77, ref=None, note=None),
        current_user=STAFF_USER,
    )

    assert response.user_id == 77
    assert captured["insert_params"][-1] == 77
    assert captured["item_owner_update"] == (77, 1)


def test_update_transaction_staff_forbidden_when_target_item_is_foreign(monkeypatch):
    monkeypatch.setattr(
        "domain.services.stock_service.StockTxRepository.get_by_id",
        lambda tx_id: {
            "id": tx_id,
            "item_id": 1,
            "item_code": "ITM-001",
            "item_name": "Owned Item",
            "location_id": 1,
            "location_name": "Main",
            "tx_type": "IN",
            "qty": 2.0,
            "ref": None,
            "note": None,
            "tx_at": "2026-01-01T00:00:00",
            "user_id": STAFF_USER["id"],
            "qty_on_hand": 2,
        },
    )
    monkeypatch.setattr("domain.services.stock_service.ItemRepository.exists_by_id", lambda item_id: True)
    monkeypatch.setattr("domain.services.stock_service.LocationsRepository.exists_by_id", lambda location_id: True)

    def fake_get_item(item_id):
        if item_id == 1:
            return {"id": 1, "owner_user_id": STAFF_USER["id"], "active": 1}
        return {"id": item_id, "owner_user_id": 999, "active": 1}

    monkeypatch.setattr("domain.services.stock_service.ItemRepository.get_by_id", fake_get_item)

    with pytest.raises(HTTPException) as exc:
        StockService.update_transaction(
            1,
            StockTxUpdate(item_id=2),
            current_user=STAFF_USER,
        )

    assert exc.value.status_code == 403


def test_delete_transaction_admin_allowed(monkeypatch):
    monkeypatch.setattr(
        "domain.services.stock_service.StockTxRepository.get_by_id",
        lambda tx_id: {
            "id": tx_id,
            "item_id": 1,
            "item_code": "ITM-001",
            "item_name": "Owned Item",
            "location_id": 1,
            "location_name": "Main",
            "tx_type": "IN",
            "qty": 1.0,
            "ref": None,
            "note": None,
            "tx_at": "2026-01-01T00:00:00",
            "user_id": ADMIN_USER["id"],
            "qty_on_hand": 1,
        },
    )
    monkeypatch.setattr("domain.services.stock_service.StockService._allow_negative_stock", lambda: True)
    monkeypatch.setattr(
        "domain.services.stock_service.StockService._reverse_transaction",
        lambda cursor, item_id, location_id, tx_type, qty, allow_negative: None,
    )

    class DummyCursor:
        def __init__(self):
            self.rowcount = 1

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params=None):
            self.rowcount = 1

    monkeypatch.setattr("domain.services.stock_service.get_transaction_cursor", lambda dictionary=True: DummyCursor())

    result = StockService.delete_transaction(1, current_user=ADMIN_USER)
    assert result["transaction_id"] == 1

from db.repositories.item_repo import ItemRepository
from db.repositories.issue_item_repo import IssueItemRepository
from domain.services.issue_item_service import IssueItemService
from schemas.items import ItemUpdate


def test_item_update_returns_current_item_when_no_row_changes(monkeypatch):
    expected_item = {
        "id": 4,
        "item_code": "ITM-004",
        "serial_number": None,
        "name": "Monitor",
        "category_id": 1,
        "unit_id": 1,
        "owner_user_id": 2,
        "min_stock": 0,
        "description": None,
        "image_url": None,
        "active": 1,
    }

    monkeypatch.setattr("db.repositories.item_repo.execute", lambda sql, params: 0)
    monkeypatch.setattr(
        "db.repositories.item_repo.ItemRepository.get_by_id",
        lambda item_id: expected_item,
    )

    result = ItemRepository.update(4, ItemUpdate(name="Monitor"))

    assert result == expected_item


def test_issue_item_repository_formats_where_clause(monkeypatch):
    captured = {"query": None, "params": None}

    def fake_fetch_all(query, params):
        captured["query"] = query
        captured["params"] = params
        return []

    monkeypatch.setattr("db.repositories.issue_item_repo.fetch_all", fake_fetch_all)

    IssueItemRepository.get_all(issue_id=1, item_id=2, limit=10, offset=5)

    assert captured["query"] is not None
    assert "{where_clause}" not in captured["query"]
    assert "WHERE ii.issue_id = %s AND ii.item_id = %s" in captured["query"]
    assert captured["params"] == (1, 2, 10, 5)


def test_staff_can_filter_issue_items_by_owned_item(monkeypatch):
    staff_user = {"id": 9, "role": "STAFF"}

    monkeypatch.setattr(
        "domain.services.issue_item_service.IssueItemService._assert_item_access",
        lambda item_id, current_user: {"id": item_id, "owner_user_id": current_user["id"]},
    )
    monkeypatch.setattr(
        "domain.services.issue_item_service.IssueItemRepository.get_all",
        lambda issue_id=None, item_id=None, limit=50, offset=0: [],
    )
    monkeypatch.setattr(
        "domain.services.issue_item_service.IssueItemRepository.count",
        lambda issue_id=None, item_id=None: 0,
    )

    response = IssueItemService.get_all_issue_items(
        item_id=7,
        page=1,
        page_size=50,
        current_user=staff_user,
    )

    assert response.total == 0
    assert response.issue_item == []

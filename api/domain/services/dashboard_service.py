from decimal import Decimal
from typing import Dict, Any
from fastapi import HTTPException, status
from db.repositories.issue_repo import IssueRepository
from db.repositories.item_repo import ItemRepository
from db.repositories.issue_item_repo import IssueItemRepository
from db.repositories.category_repo import CategoryRepository
from db.repositories.units_repo import UnitsRepository
from schemas.issues import IssueResponse
from schemas.issue_items import IssueItemResponse
from core.logging import get_logger

logger = get_logger(__name__)

class DashboardService:
    """
    Service for aggregating dashboard data related to issues, issue items, categories, units, and users.
    """
        
    @staticmethod
    def get_issue_statistics() -> Dict[str, Any]:
        """
        Get dashboard statistics for issues
        """
        try:
            total_issues = IssueRepository.count()

            if total_issues == 0:
                return {
                    "total": 0,
                    "status_breakdown": {
                        "draft": {"count": 0, "percentage": 0.0},
                        "approved": {"count": 0, "percentage": 0.0},
                        "issued": {"count": 0, "percentage": 0.0},
                        "cancelled": {"count": 0, "percentage": 0.0},
                    }
                }

            draft_count = IssueRepository.count_status('DRAFT')
            approved_count = IssueRepository.count_status('APPROVED')
            issued_count = IssueRepository.count_status('ISSUED')
            cancelled_count = IssueRepository.count_status('CANCELLED')

            # Calculate percentages
            draft_percentage = round((draft_count / total_issues) * 100, 2)
            approved_percentage = round((approved_count / total_issues) * 100, 2)
            issued_percentage = round((issued_count / total_issues) * 100, 2)
            cancelled_percentage = round((cancelled_count / total_issues) * 100, 2)

            logger.info(
                "Issue statistics retrieved successfully",
                extra={
                    "total": total_issues,
                    "draft": draft_count,
                    "approved": approved_count,
                    "issued": issued_count,
                    "cancelled": cancelled_count,
                }
            )

            results = {
                "total": total_issues,
                "status_breakdown": {
                    "draft": {"count": draft_count, "percentage": draft_percentage},
                    "approved": {"count": approved_count, "percentage": approved_percentage},
                    "issued": {"count": issued_count, "percentage": issued_percentage},
                    "cancelled": {"count": cancelled_count, "percentage": cancelled_percentage},
                }
            }

            return results
        except Exception as e:
            logger.error(
                "Error retrieving issue statistics",
                extra={
                    "error": str(e),
                }
            )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
        
    @staticmethod
    def get_issue_with_details(issue_id: int) -> Dict[str, Any]:
        """
        Get detailed information about items in a specific issue with item metadata.
        """
        try:
            # Validate issue exists
            issue_data = IssueRepository.get_by_id(issue_id)
            if not issue_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Issue {issue_id} not found"
                )

            # Fetch issue
            issue = IssueResponse(**issue_data)

            # Fetch issue items with details
            items_data = IssueItemRepository.get_by_issue_id(issue_id)
            items = [IssueItemResponse(**item) for item in items_data]

            # Fetch all categories
            categories_data = CategoryRepository.get_all(limit=1000, offset=0)
            categories = {cat['id']: cat['name'] for cat in categories_data}

            # Fetch all units
            units_data = UnitsRepository.get_all(limit=1000, offset=0)
            units = {unit['id']: {'name': unit['name'], 'symbol': unit['symbol']} for unit in units_data}

            logger.info(
                "Issue details retrieved successfully",
                extra={
                    "issue_id": issue_id,
                    "item_count": len(items),
                }
            )

            results = {
                "issue": issue,
                "items": items,
                "categories": categories,
                "units": units,
            }

            return results
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Error retrieving issue details",
                extra={
                    "issue_id": issue_id,
                    "error": str(e)
                }
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve issue details"
            )

    @staticmethod
    def get_items_by_issue(issue_id: int) -> Dict[str, Any]:
        """
        Get items associated with a specific issue.
        """
        try:
            # Validate issue exists
            issue_data = IssueRepository.get_by_id(issue_id)
            if not issue_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Issue {issue_id} not found"
                )

            # Fetch issue items
            items_data = IssueItemRepository.get_by_issue_id(issue_id)
            # items = [IssueItemResponse(**item) for item in items_data]
            if not items_data:
                logger.info(
                    "Items for issue retrieved successfully",
                    extra={"issue_id": issue_id}
                )

                results = {
                    "issue": IssueResponse(**issue_data),
                    "items": [],
                    "total_qty": 0,
                    "total_items": 0
                }

                return results
            
            # Fetch categories and units for mapping
            categories_data = CategoryRepository.get_all(limit=1000, offset=0)
            categories_map = {cat['id']: cat for cat in categories_data}

            units_data = UnitsRepository.get_all(limit=1000, offset=0)
            units_map = {unit['id']: unit for unit in units_data}

            # Enrich items with category and unit information
            enriched_items = []
            total_qty = Decimal("0")

            for item in items_data:
                # item_response = IssueItemResponse(**item)

                # Get full item details
                item_details = ItemRepository.get_by_id(item['item_id'])

                if not item_details:
                    logger.warning(
                        "Item not found while enriching issue items",
                        extra={"item_id": item['item_id']}
                    )
                    continue

                enriched_item = {
                    "id": item['id'],
                    "item_id": item['item_id'],
                    "issue_id": item['issue_id'],
                    "qty": float(item['qty']),
                    "item_code": item.get('item_code') or item_details.get('item_code'),
                    "item_name": item.get('item_name') or item_details.get('name'),
                    "category_id": item_details.get('category_id'),
                    "category_name": categories_map.get(item_details.get('category_id')),
                    "unit_id": item_details.get('unit_id'),
                    "unit_name": units_map.get(item_details.get('unit_id'), {}).get('name') if item_details else None,
                    "unit_symbol": units_map.get(item_details.get('unit_id'), {}).get('symbol') if item_details else None,
                    "description": item_details.get('description') if item_details else None,
                    "active": item_details.get('active'),
                }

                enriched_items.append(enriched_item)
                total_qty += Decimal(str(item['qty']))

            logger.info(
                "Items for issue retrieved successfully",
                extra={
                    "issue_id": issue_id,
                    "item_count": len(enriched_items),
                    "total_qty": str(total_qty)
                }
            )

            results = {
                "issue": IssueResponse(**issue_data),
                "items": enriched_items,
                "total_qty": int(total_qty),
                "total_items": len(enriched_items)
            }

            return results
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Error retrieving items for issue",
                extra={
                    "issue_id": issue_id,
                    "error": str(e)
                }
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve items for issue"
            )
        
    @staticmethod
    def get_advanced_statistics() -> Dict[str, Any]:
        """
        Get advanced statistics including average items per issue, 
        status distribution, and trend data.
        """
        try:
            total_issues = IssueRepository.count()
            
            if total_issues == 0:
                response = {
                    "total_issues": 0,
                    "total_items": 0,
                    "avg_items_per_issue": 0,
                    "status_breakdown": {
                        "draft": {"count": 0, "percentage": 0},
                        "approved": {"count": 0, "percentage": 0},
                        "issued": {"count": 0, "percentage": 0},
                        "cancelled": {"count": 0, "percentage": 0}
                    },
                    "issue_completion_rate": 0
                }

                return response

            # Get status counts
            draft_count = IssueRepository.count_status("DRAFT")
            approved_count = IssueRepository.count_status("APPROVED")
            issued_count = IssueRepository.count_status("ISSUED")
            cancelled_count = IssueRepository.count_status("CANCELLED")

            # Calculate percentages
            draft_pct = round((draft_count / total_issues) * 100, 2)
            approved_pct = round((approved_count / total_issues) * 100, 2)
            issued_pct = round((issued_count / total_issues) * 100, 2)
            cancelled_pct = round((cancelled_count / total_issues) * 100, 2)

            # Get total items across all issues
            all_issues = IssueRepository.get_all(limit=10000, offset=0)
            total_items = 0
            for issue in all_issues:
                items_count = IssueItemRepository.count(issue_id=issue['id'])
                total_items += items_count

            avg_items = round(total_items / total_issues, 2) if total_issues > 0 else 0

            # Calculate completion rate (approved + issued) / total
            completion_rate = round(((approved_count + issued_count) / total_issues) * 100, 2) if total_issues > 0 else 0

            logger.info(
                "Advanced statistics retrieved successfully",
                extra={
                    "total_issues": total_issues,
                    "total_items": total_items,
                    "avg_items": avg_items,
                    "completion_rate": completion_rate
                }
            )
            response = {
                "total_issues": total_issues,
                "total_items": total_items,
                "avg_items_per_issue": avg_items,
                "status_breakdown": {
                    "draft": {"count": draft_count, "percentage": draft_pct},
                    "approved": {"count": approved_count, "percentage": approved_pct},
                    "issued": {"count": issued_count, "percentage": issued_pct},
                    "cancelled": {"count": cancelled_count, "percentage": cancelled_pct}
                },
                "issue_completion_rate": completion_rate
            }

            return response 
        except Exception as e:
            logger.error(
                "Failed to retrieve advanced statistics",
                extra={"error": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve advanced statistics"
            )

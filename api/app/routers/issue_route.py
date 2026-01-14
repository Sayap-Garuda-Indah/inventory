from typing import Optional
from core.logging import get_logger
from domain.services.issue_service import IssueService
from domain.services.dashboard_service import DashboardService
from app.dependencies import require_role, get_current_user
from schemas.users import UserRole
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from schemas.issues import Issue, IssueCreate, IssueUpdate, IssueListResponse, IssueResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/issues", tags=["Issues"])

@router.get("/stats", tags=["Issues"])
def get_issue_statistics(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Get issue statistics for dashboard
    """
    try:
        logger.info(
            "Issue statistics requested",
            extra={
                "requested_by": current_user["id"]
            }
        )

        stats = DashboardService.get_issue_statistics()

        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error retrieving issue statistics",
            extra={
                "error": str(e),
                "requested_by": current_user["id"]
            }
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/", response_model=IssueListResponse)
def list_issues(
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(50, ge=1, le=100, description="Number of issues per page"),
    search: Optional[str] = Query(None, description="Search term for issue code or status"),
    status_filter: Optional[str] = Query(None, description="Filter issues by status"),
    current_user: dict = Depends(get_current_user)
) -> IssueListResponse:
    try:
        logger.info(
            "Issue list requested",
            extra={
                "requested_by": current_user["id"],
                "search": search,
                "status_filter": status_filter,
                "page": page,
                "page_size": page_size
            }
        )

        issues_data = IssueService.get_all_issues(
            page=page,
            page_size=page_size,
            search=search,
            status_filter=status_filter
        )
    
        return issues_data
    except Exception as e:
        logger.error(f"Error in list_issues. ", extra={"error": str(e), "requested_by": current_user["id"]})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/{issue_id}", response_model=IssueResponse)
def get_issue(
    issue_id: int = Path(..., gt=0, description="The ID of the issue to retrieve"),
    current_user: dict = Depends(get_current_user)  
) -> IssueResponse:
    try:
        logger.info(
            "Issue details requested",
            extra={
                "requested_by": current_user["id"],
                "issue_id": issue_id
            }
        )

        issue_data = IssueService.get_issue_by_id(issue_id)
        return issue_data
    except Exception as e:
        logger.error(f"Error in get_issue. ", extra={"error": str(e), "requested_by": current_user["id"]})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/code/{code}", response_model=IssueResponse)
def get_issue_by_code(
    code: str = Path(..., description="The code of the issue to retrieve"),
    current_user: dict = Depends(get_current_user)
) -> IssueResponse:
    try:
        logger.info(
            "Issue detailes requested",
            extra={
                "requested_by": current_user["id"],
                "code": code
            }
        )

        issue_data = IssueService.get_issue_by_code(code)
        
        if issue_data is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Issue with code '{code}' not found")
        
        return issue_data
    except Exception as e:
        logger.error(f"Error in get_issue_by_code. ", extra={"error": str(e), "requested_by": current_user["id"]})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/{issue_id}/items", tags=["Issues"])
def get_issue_items_details(
    issue_id: int = Path(..., gt=0, description="The ID of the issue"),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get detailed items for a specific issue with full metadata (categories, units, etc).
    """
    try:
        logger.info(
            "Issue items details requested",
            extra={
                "requested_by": current_user['id'],
                "issue_id": issue_id
            }
        )

        items_data = DashboardService.get_items_by_issue(issue_id)

        logger.info(
            "Issue items details retrieved successfully",
            extra={
                "requested_by": current_user['id'],
                "issue_id": issue_id,
                "item_count": len(items_data.get('items', []))
            }
        )

        return items_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error retrieving issue items details",
            extra={
                "error": str(e),
                "issue_id": issue_id,
                "requested_by": current_user['id']
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# @router.get("/stats", tags=["Issues"])
# def get_statistics(current_user: dict = Depends(get_current_user)) -> dict:
#     """
#     Get issue statistics for dashboard.
#     """
#     try:
#         logger.info(
#             "Issue statistics requested",
#             extra={"requested_by": current_user["id"]}
#         )
        
#         stats = DashboardService.get_issue_statistics()
        
#         return stats
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(
#             "Error retrieving statistics",
#             extra={"error": str(e), "requested_by": current_user["id"]}
#         )
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to retrieve statistics"
#         )

@router.get("/advanced-stats", tags=["Issues"])
def get_advanced_statistics(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get advanced issue statistics including completion rates and averages.
    """
    try:
        logger.info(
            "Advanced statistics requested",
            extra={"requested_by": current_user["id"]}
        )
        
        stats = DashboardService.get_advanced_statistics()
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error retrieving advanced statistics",
            extra={"error": str(e), "requested_by": current_user["id"]}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve advanced statistics"
        )

@router.get("/{issue_id}/items-detailed", tags=["Issues"])
def get_issue_items_detailed(
    issue_id: int = Path(..., gt=0, description="The ID of the issue"),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get detailed items for a specific issue with full metadata.
    (This is an alias for /items endpoint)
    """
    return get_issue_items_details(issue_id, current_user)

@router.post("/", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def create_issue(
    issue_data: IssueCreate,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
) -> IssueResponse:
    try:
        logger.info(
            "Issue creation requested",
            extra={
                "requested_by": current_user["id"],
                "issue_code": issue_data.code,
                "status": issue_data.status
            }
        )

        new_issue = IssueService.create_issue(issue_data, current_user["id"])
        
        logger.info(
            "Issue created successfully",
            extra={
                "issue_id": new_issue.id,
                "created_by": current_user["id"],
                "issue_code": new_issue.code,
                "status": new_issue.status
            }
        )

        return new_issue
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_issue. ", extra={"error": str(e), "requested_by": current_user["id"]})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    
@router.put("/{issue_id}", response_model=IssueResponse)
def update_issue(
    issue_data: IssueUpdate,
    issue_id: int = Path(..., gt=0, description="The ID of the issue to update"),
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
) -> IssueResponse:
    try:
        logger.info(
            "Issue update requested",
            extra={
                "updated_by": current_user["id"],
                "issue_id": issue_id,
                "updated_fields": {
                    k: v for k, v in issue_data.model_dump(exclude_unset=True).items() if v is not None
                }
            }
        )

        response = IssueService.update_issue(issue_id, issue_data)

        logger.info(
            "Issue updated successfully",
            extra={
                "updated_by": current_user["id"],
                "issue_id": issue_id
            }
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update issue", 
            extra={
                "error": str(e), 
                "issue_id": issue_id, 
                "updated_by": current_user["id"]
            })
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    
@router.delete("/{issue_id}", status_code=status.HTTP_200_OK)
def delete_issue(
    issue_id: int = Path(..., gt=0, description="The ID of the issue to delete"),
    current_user: dict = Depends(require_role(UserRole.ADMIN))
) -> dict:
    try:
        logger.info(
            "Issue deletion requested",
            extra={
                "deleted_by": current_user["id"],
                "issue_id": issue_id
            }
        )

        result = IssueService.delete_issue(issue_id)
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Issue with ID '{issue_id}' not found")


        logger.info(
            "Issue deleted successfully",
            extra={
                "deleted_by": current_user["id"],
                "issue_id": issue_id
            }
        )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            logger.error(
                "Failed to delete issue",
                extra={"error": str(e), "issue_id": issue_id}
            )
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    
@router.patch("/{issue_ud}/approve", response_model=IssueResponse)
def approve_issue(
    issue_id: int = Path(..., gt=0, description="The ID of the issue to approve"),
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
) -> IssueResponse:
    try:
        logger.info(
            "Issue approval requested",
            extra={
                "approved_by": current_user["id"],
                "issue_id": issue_id
            }
        )

        approved_issue = IssueService.approve_issue(issue_id, current_user["id"])

        logger.info(
            "Issue approved successfully",
            extra={
                "approved_by": current_user["id"],
                "issue_id": issue_id
            }
        )

        return approved_issue
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in approve_issue. ", extra={"error": str(e), "issue_id": issue_id})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.patch("/{issue_id}/status", response_model=IssueResponse)
def change_issue_status(issue_id: int = Path(..., gt=0, description="The ID of the issue to change status"),
                        new_status: str = Query(..., description="The new status for the issue"),
                        current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
                        ) -> IssueResponse:
    try:
        logger.info(
            "Issue status change requested",
            extra={
                "changed_by": current_user["id"],
                "issue_id": issue_id,
                "new_status": new_status
            }
        )

        updated_issue = IssueService.change_issue_status(issue_id, new_status)

        logger.info(
            "Issue status changed successfully",
            extra={
                "changed_by": current_user["id"],
                "issue_id": issue_id,
                "new_status": new_status
            }
        )

        return updated_issue
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in change_issue_status. ", extra={"error": str(e), "issue_id": issue_id})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    

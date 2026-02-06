from typing import Optional, List
from fastapi import HTTPException, status
# from api.db.repositories.item_repo import ItemRepository
from db.pool import fetch_one
from db.repositories.user_repo import UserRepository
from db.repositories.issue_repo import IssueRepository
from schemas.issues import IssueCreate, IssueUpdate, IssueResponse, IssueListResponse
from core.logging import get_logger

logger = get_logger(__name__)

class IssueService:
    @staticmethod
    def get_all_issues(
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> IssueListResponse:
        try:
            if page < 1:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Page number must be at least 1")
            if page_size < 1 or page_size > 100:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Page size must be between 1 and 100")
            
            offset = (page - 1) * page_size

            # Fetch issues with filters and pagination
            issue_data = IssueRepository.get_all(
                limit=page_size,
                offset=offset,
                search=search,
                status_filter=status_filter
            )
            
            # Get total count for pagination
            total = IssueRepository.count_with_filter(search=search, status_filter=status_filter)

            # Convert to response models
            issues = [IssueResponse(**issue) for issue in issue_data]

            results = IssueListResponse(
                total=total,
                page=page,
                page_size=page_size,
                issues=issues
                
            )

            logger.info(
                "Issues retrieved successfully",
                extra={
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "search": search,
                    "status_filter": status_filter
                }
            )

            return results
        except HTTPException:
            raise 
        except Exception as e:
            logger.error(
                "Failed to retrieve issues. ",
                extra={
                    "error": str(e), 
                    "search": search, 
                    "page": page, 
                    "page_size": page_size
                }
            )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
        
    @staticmethod
    def get_issue_by_id(issue_id: int) -> IssueResponse:
        """
        Get an issue by its ID.
        """
        try:
            if not isinstance(issue_id, int) or issue_id <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid issue ID")
            
            issue_data = IssueRepository.get_by_id(issue_id)
            if not issue_data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Issue {issue_id} not found")
            
            return IssueResponse(**issue_data)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in get_issue_by_id: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    
    @staticmethod
    def get_issue_by_code(code: str) -> Optional[IssueResponse]:
        """
        Get an issue by its code.
        """
        try:
            if not code or not code.strip():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code must be a non-empty string")
            
            issue_data = IssueRepository.get_by_code(code.strip())
            if not issue_data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Issue with code '{code}' not found")
            
            return IssueResponse(**issue_data)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve issue by code. ", extra={"error": str(e), "code": code})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    @staticmethod
    def create_issue(issue_data: IssueCreate, requested_by: int) -> IssueResponse:
        """
        Create a new issue.
        """
        try:
            if IssueRepository.exists_by_code(issue_data.code):
                logger.warning(
                    "Issue creation failed - duplicate code.",
                    extra={
                        "code": issue_data.code,
                        "requested_by": requested_by
                    }
                )
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Issue with code '{issue_data.code}' already exists")
            
            # Validate foreign keys if provided
            if issue_data.requested_by:
                if not UserRepository.exists_by_id(issue_data.requested_by):
                    logger.warning(
                        "Issue creation failed - invalid requested_by user ID.",
                        extra={
                            "requested_by": issue_data.requested_by,
                            "issue_code": issue_data.code,
                            "creator_id": requested_by
                        }
                    )
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Requested by user ID {issue_data.requested_by} does not exist")
                
            if issue_data.approved_by:
                if not UserRepository.exists_by_id(issue_data.approved_by):
                    logger.warning(
                        "Issue creation failed - invalid approved_by user ID.",
                        extra={
                            "approved_by": issue_data.approved_by,
                            "issue_code": issue_data.code,
                            "creator_id": requested_by
                        }
                    )
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Approved by user ID {issue_data.approved_by} does not exist")
                
            new_issue = IssueRepository.create(issue_data)
            if not new_issue:
                logger.warning(
                    "Issue creation failed - repository error.",
                    extra={
                        "issue_code": issue_data.code,
                        "creator_id": requested_by
                    }
                )
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create issue")

            logger.info("Issue created successfully", extra={"issue_id": new_issue["id"], "issue_code": new_issue["id"]})
            
            return IssueResponse(**new_issue)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Error in create_issue. ", 
                extra={
                    "error": str(e), 
                    "issue_code": issue_data.code
                }
            )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
        
    @staticmethod
    def update_issue(issue_id: int, issue_data: IssueUpdate) -> IssueResponse:
        """
        Update an existing issue.
        """
        try:
            if not isinstance(issue_id, int) or issue_id <= 0:
                logger.warning(
                    "Issue update failed - invalid issue ID.",
                    extra={
                        "issue_id": issue_id,
                        "updated_fields": issue_data.model_dump(exclude_unset=True)
                    }
                )
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid issue ID")
            
            # Check if issue exists
            existing_issue = IssueRepository.get_by_id(issue_id)
            if not existing_issue:
                logger.warning(
                    "Issues already exists.",
                    extra={
                        "issue_id": issue_id,
                        "updated_fields": issue_data.model_dump(exclude_unset=True)
                    }
                )
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Issue {issue_id} not found")
            
            # Check for code conflict if code is being updated
            if issue_data.code and issue_data.code != existing_issue["code"]:
                if IssueRepository.exists_by_code(issue_data.code):
                    logger.warning(
                        "Issue update failed - duplicate code.",
                        extra={
                            "issue_id": issue_id,
                            "new_code": issue_data.code
                        }
                    )
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Issue with code '{issue_data.code}' already exists")

            # Validate foreign keys if provided
            if issue_data.requested_by is not None:
                if not UserRepository.exists_by_id(issue_data.requested_by):
                    logger.warning(
                        "Issue update failed - invalid requested_by user ID.",
                        extra={
                            "issue_id": issue_id,
                            "requested_by": issue_data.requested_by
                        }
                    )
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Requested by user ID {issue_data.requested_by} does not exist")
                
            if issue_data.approved_by is not None:
                if not UserRepository.exists_by_id(issue_data.approved_by):
                    logger.warning(
                        "Issue update failed - invalid approved_by user ID.",
                        extra={
                            "issue_id": issue_id,
                            "approved_by": issue_data.approved_by
                        }
                    )
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Approved by user ID {issue_data.approved_by} does not exist")

            updated_issue = IssueRepository.update(issue_id, issue_data)
            if not updated_issue:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Issue {issue_id} not found")
            
            logger.info(
                f"Issue updated successfully", 
                extra={
                    "issue_id": issue_id,
                    "updated_fields": {
                        k: v for k, v in issue_data.model_dump(exclude_unset=True).items() if v is not None
                    }
                }
            )

            return IssueResponse(**updated_issue)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Error in update_issue. ", 
                extra={
                    "error": str(e), 
                    "issue_id": issue_id
                }
            )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
        
    @staticmethod
    def delete_issue(issue_id: int) -> Optional[dict]:
        """
        Soft delete an issue by its ID.
        """
        try:
            if not isinstance(issue_id, int) or issue_id <= 0:
                logger.warning(
                    "Issue deletion failed - invalid issue ID.",
                    extra={
                        "issue_id": issue_id,
                    }
                )
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid issue ID")
            
            existing_issue = IssueRepository.get_by_id(issue_id)
            if not existing_issue:
                logger.warning(
                    "Issue deletion failed - issue not found.",
                    extra={
                        "issue_id": issue_id,
                    }
                )
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Issue {issue_id} not found")
            
            issue_items = fetch_one(
                "SELECT COUNT(*) AS count FROM issue_items WHERE issue_id = %s",
                (issue_id,),
            )
            issue_item_count = int(issue_items["count"]) if issue_items else 0

            success = IssueRepository.delete(issue_id)
            if not success:
                logger.error(
                    "Issue deletion failed - repository error.",
                    extra={
                        "issue_id": issue_id,
                    }
                )
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete issue {issue_id}")

            logger.info(
                "Issue soft-deleted successfully.",
                extra={
                    "issue_id": issue_id,
                    "issue_code": existing_issue["code"],
                    "issue_items": issue_item_count,
                }
            )

            warning = None
            if issue_item_count > 0:
                warning = (
                    f"Issue has {issue_item_count} related issue item record(s) kept for history. "
                    "Issue status is changed to CANCELLED and hidden from normal list."
                )

            message = {
                "message": f"Issue '{existing_issue['code']}' (ID: {issue_id}) has been soft-deleted successfully.",
                "warning": warning,
                "issue_items": issue_item_count,
            }

            return message
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Error in delete_issue. ", 
                extra={
                    "error": str(e), 
                    "issue_id": issue_id
                }
            )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
        
    @staticmethod
    def approve_issue(issue_id: int, approver_id: int) -> IssueResponse:
        """
        Approve an issue by its ID.
        """
        try:
            if not isinstance(issue_id, int) or issue_id <= 0:
                logger.warning(
                    "Issue approval failed - invalid issue ID.",
                    extra={
                        "issue_id": issue_id,
                        "approver_id": approver_id
                    }
                )
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid issue ID")
            
            existing_issue = IssueRepository.get_by_id(issue_id)
            if not existing_issue:
                logger.warning(
                    "Issue approval failed - issue not found.",
                    extra={
                        "issue_id": issue_id,
                        "approver_id": approver_id
                    }
                )
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Issue {issue_id} not found")
            
            # Check if issue is in DRAFT status
            if existing_issue["status"] != "DRAFT":
                logger.warning(
                    "Issue approval failed - issue not in DRAFT status.",
                    extra={
                        "issue_id": issue_id,
                        "current_status": existing_issue["status"],
                        "approver_id": approver_id
                    }
                )
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Issue {issue_id} is not in DRAFT status and cannot be approved")
            
            # Validate approver
            if not UserRepository.exists_by_id(approver_id):
                logger.warning(
                    "Issue approval failed - invalid approver user ID.",
                    extra={
                        "issue_id": issue_id,
                        "approver_id": approver_id
                    }
                )
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Approver user ID {approver_id} does not exist")
            
            approved_issue = IssueRepository.approve_issue(issue_id, approver_id)
            if not approved_issue:
                logger.error(
                    "Failed to approve issue.",
                    extra={
                        "issue_id": issue_id,
                        "approver_id": approver_id
                    }
                )
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to approve issue {issue_id}")
            
            logger.info("Issue approved successfully", extra={"issue_id": issue_id, "approver_id": approver_id})

            return IssueResponse(**approved_issue)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Error in approve_issue. ", 
                extra={
                    "error": str(e), 
                    "issue_id": issue_id
                }
            )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    @staticmethod
    def change_issue_status(issue_id: int, new_status: str) -> IssueResponse:
        """
        Change the status of an issue.
        """
        try:
            if not isinstance(issue_id, int) or issue_id <= 0:
                logger.warning(
                    "Issue status change failed - invalid issue ID.",
                    extra={
                        "issue_id": issue_id,
                        "new_status": new_status
                    }
                )
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid issue ID")
            
            existing_issue = IssueRepository.get_by_id(issue_id)
            if not existing_issue:
                logger.warning(
                    "Issue status change failed - issue not found.",
                    extra={
                        "issue_id": issue_id,
                        "new_status": new_status
                    }
                )
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Issue {issue_id} not found")
            
            updated_issue = IssueRepository.change_status(issue_id, new_status)
            if not updated_issue:
                logger.error(
                    "Failed to change issue status.",
                    extra={
                        "issue_id": issue_id,
                        "new_status": new_status
                    }
                )
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to change status for issue {issue_id}")
            
            logger.info("Issue status changed successfully", extra={"issue_id": issue_id, "new_status": new_status})

            return IssueResponse(**updated_issue)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Error in change_issue_status. ", 
                extra={
                    "error": str(e), 
                    "issue_id": issue_id
                }
            )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

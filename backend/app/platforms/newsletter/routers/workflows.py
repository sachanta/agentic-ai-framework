"""
Workflow management API endpoints.

Phase 11: HITL workflow management endpoints.
"""
import asyncio
import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime

from app.core.security import get_current_user, decode_access_token
from app.platforms.newsletter.services import NewsletterService
from app.platforms.newsletter.orchestrator import get_newsletter_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["workflows"])


# Response schemas
class WorkflowListItem(BaseModel):
    """Brief workflow item for list views."""
    workflow_id: str
    status: str
    current_step: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class WorkflowListResponse(BaseModel):
    """Workflow list response."""
    items: List[WorkflowListItem]
    total: int


class WorkflowDetail(BaseModel):
    """Full workflow details."""
    workflow_id: str
    user_id: str
    status: str
    current_step: Optional[str] = None
    current_checkpoint: Optional[Dict[str, Any]] = None
    topics: List[str] = []
    tone: str = "professional"
    article_count: int = 0
    newsletter_id: Optional[str] = None
    checkpoints_completed: List[str] = []
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class WorkflowHistoryItem(BaseModel):
    """Workflow history entry."""
    step: str
    status: str
    timestamp: datetime
    data: Dict[str, Any] = {}


class WorkflowHistoryResponse(BaseModel):
    """Workflow execution history."""
    workflow_id: str
    history: List[WorkflowHistoryItem]


class CheckpointDetail(BaseModel):
    """Checkpoint details."""
    checkpoint_id: str
    checkpoint_type: str
    title: str
    description: str
    data: Dict[str, Any]
    actions: List[str]
    metadata: Dict[str, Any] = {}


class EditCheckpointRequest(BaseModel):
    """Request to edit and continue from checkpoint."""
    checkpoint_id: str
    modifications: Dict[str, Any]
    feedback: Optional[str] = None


class RejectCheckpointRequest(BaseModel):
    """Request to reject and re-run from checkpoint."""
    checkpoint_id: str
    feedback: Optional[str] = None


class ApproveCheckpointRequest(BaseModel):
    """Request to approve a checkpoint."""
    checkpoint_id: str
    action: str = "approve"  # approve, edit, reject
    modifications: Optional[Dict[str, Any]] = None
    feedback: Optional[str] = None


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    status: Optional[str] = Query(None, description="Filter by status (running, awaiting_approval, completed, cancelled, failed)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    current_user: dict = Depends(get_current_user),
):
    """
    List user's workflows.

    Returns a list of workflow summaries with optional status filtering.
    """
    try:
        orchestrator = get_newsletter_orchestrator()
        user_id = current_user["id"]

        workflows = await orchestrator.list_workflows(
            user_id=user_id,
            status=status,
            limit=limit,
        )

        items = [
            WorkflowListItem(
                workflow_id=wf.get("workflow_id", ""),
                status=wf.get("status", "unknown"),
                current_step=wf.get("current_step"),
                created_at=wf.get("created_at", datetime.now()),
                updated_at=wf.get("updated_at", datetime.now()),
            )
            for wf in workflows
        ]

        return WorkflowListResponse(
            items=items,
            total=len(items),
        )

    except Exception as e:
        logger.error(f"List workflows failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}", response_model=WorkflowDetail)
async def get_workflow(
    workflow_id: str = Path(..., description="Workflow ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get workflow status and details.

    Returns the current state of the workflow including any pending checkpoint.
    """
    try:
        orchestrator = get_newsletter_orchestrator()
        result = await orchestrator.get_workflow_status(workflow_id)

        if not result:
            raise HTTPException(status_code=404, detail="Workflow not found")

        return WorkflowDetail(
            workflow_id=result.get("workflow_id", workflow_id),
            user_id=result.get("user_id", ""),
            status=result.get("status", "unknown"),
            current_step=result.get("current_step"),
            current_checkpoint=result.get("current_checkpoint"),
            topics=result.get("topics", []),
            tone=result.get("tone", "professional"),
            article_count=len(result.get("articles", [])),
            newsletter_id=result.get("newsletter_id"),
            checkpoints_completed=result.get("checkpoints_completed", []),
            error=result.get("error"),
            created_at=result.get("created_at", datetime.now()),
            updated_at=result.get("updated_at", datetime.now()),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get workflow failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/checkpoint", response_model=CheckpointDetail)
async def get_checkpoint(
    workflow_id: str = Path(..., description="Workflow ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get the current pending checkpoint for a workflow.

    Returns checkpoint details including available actions.
    """
    try:
        orchestrator = get_newsletter_orchestrator()
        result = await orchestrator.get_pending_checkpoint(workflow_id)

        if not result:
            raise HTTPException(status_code=404, detail="No pending checkpoint")

        return CheckpointDetail(
            checkpoint_id=result.get("checkpoint_id", ""),
            checkpoint_type=result.get("checkpoint_type", ""),
            title=result.get("title", ""),
            description=result.get("description", ""),
            data=result.get("data", {}),
            actions=result.get("actions", ["approve", "edit", "reject"]),
            metadata=result.get("metadata", {}),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get checkpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/approve")
async def approve_checkpoint(
    request: ApproveCheckpointRequest,
    workflow_id: str = Path(..., description="Workflow ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Approve, edit, or reject the current checkpoint.

    Actions:
    - approve: Accept and continue to next step
    - edit: Modify data and continue
    - reject: Re-run the previous step
    """
    try:
        orchestrator = get_newsletter_orchestrator()
        result = await orchestrator.approve_checkpoint(
            workflow_id=workflow_id,
            checkpoint_id=request.checkpoint_id,
            action=request.action,
            modifications=request.modifications,
            feedback=request.feedback,
        )
        return result

    except Exception as e:
        logger.error(f"Approve checkpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/edit")
async def edit_checkpoint(
    request: EditCheckpointRequest,
    workflow_id: str = Path(..., description="Workflow ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Edit checkpoint data and continue workflow.

    Allows modifying articles, content, or other checkpoint data
    before continuing to the next step.
    """
    try:
        orchestrator = get_newsletter_orchestrator()
        result = await orchestrator.approve_checkpoint(
            workflow_id=workflow_id,
            checkpoint_id=request.checkpoint_id,
            action="edit",
            modifications=request.modifications,
            feedback=request.feedback,
        )
        return result

    except Exception as e:
        logger.error(f"Edit checkpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/reject")
async def reject_checkpoint(
    request: RejectCheckpointRequest,
    workflow_id: str = Path(..., description="Workflow ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Reject checkpoint and re-run the previous step.

    This will go back to the previous agent and regenerate output.
    """
    try:
        orchestrator = get_newsletter_orchestrator()
        result = await orchestrator.approve_checkpoint(
            workflow_id=workflow_id,
            checkpoint_id=request.checkpoint_id,
            action="reject",
            feedback=request.feedback,
        )
        return result

    except Exception as e:
        logger.error(f"Reject checkpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/history", response_model=WorkflowHistoryResponse)
async def get_workflow_history(
    workflow_id: str = Path(..., description="Workflow ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get workflow execution history.

    Returns a chronological list of steps executed in the workflow.
    """
    try:
        orchestrator = get_newsletter_orchestrator()
        result = await orchestrator.get_workflow_status(workflow_id)

        if not result:
            raise HTTPException(status_code=404, detail="Workflow not found")

        history = result.get("history", [])
        history_items = [
            WorkflowHistoryItem(
                step=h.get("step", "unknown"),
                status=h.get("status", "unknown"),
                timestamp=h.get("timestamp", datetime.now()),
                data=h.get("data", {}),
            )
            for h in history
        ]

        return WorkflowHistoryResponse(
            workflow_id=workflow_id,
            history=history_items,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get workflow history failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/stream")
async def stream_workflow_progress(
    workflow_id: str = Path(..., description="Workflow ID"),
    token: Optional[str] = Query(None, description="JWT token for SSE auth (EventSource cannot set headers)"),
):
    """
    Stream workflow progress via Server-Sent Events (SSE).

    Returns real-time updates as the workflow progresses.
    Connect with EventSource to receive updates.

    Accepts auth via ?token= query parameter since EventSource
    cannot set Authorization headers.
    """
    # Validate token from query parameter
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    async def event_generator():
        orchestrator = get_newsletter_orchestrator()
        last_status = None
        poll_count = 0
        max_polls = 300  # 5 minutes at 1 second intervals

        while poll_count < max_polls:
            try:
                result = await orchestrator.get_workflow_status(workflow_id)

                if not result:
                    yield f"event: error\ndata: {{\"error\": \"Workflow not found\"}}\n\n"
                    break

                current_status = result.get("status")
                current_step = result.get("current_step")

                # Send update if status or step changed
                if current_status != last_status:
                    event_data = {
                        "workflow_id": workflow_id,
                        "status": current_status,
                        "current_step": current_step,
                        "checkpoint": result.get("current_checkpoint"),
                    }
                    yield f"event: status\ndata: {str(event_data)}\n\n"
                    last_status = current_status

                # Check if workflow completed or needs human input
                if current_status in ["completed", "cancelled", "failed"]:
                    yield f"event: complete\ndata: {{\"status\": \"{current_status}\"}}\n\n"
                    break

                if current_status == "awaiting_approval":
                    checkpoint = result.get("current_checkpoint", {})
                    yield f"event: checkpoint\ndata: {str(checkpoint)}\n\n"
                    break

                await asyncio.sleep(1)
                poll_count += 1

            except Exception as e:
                yield f"event: error\ndata: {{\"error\": \"{str(e)}\"}}\n\n"
                break

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: str = Path(..., description="Workflow ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Cancel a running workflow.

    Stops workflow execution and marks it as cancelled.
    """
    try:
        orchestrator = get_newsletter_orchestrator()
        result = await orchestrator.cancel_workflow(workflow_id)
        return result

    except Exception as e:
        logger.error(f"Cancel workflow failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

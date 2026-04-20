"""
Action Log API routes - Query and audit logs
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.models.models import ActionLog, ActionType
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/logs", tags=["logs"])


class ActionLogResponse(BaseModel):
    """Action log response"""
    id: str
    project_id: str
    document_id: Optional[str]
    chapter_id: Optional[str]
    user_id: str
    action_type: str
    description: Optional[str]
    extra_data: Optional[dict]
    created_at: str
    
    class Config:
        from_attributes = True


@router.get("/{project_id}", response_model=List[ActionLogResponse])
async def list_project_logs(
    project_id: str,
    limit: int = 50,
    offset: int = 0,
    action_type: str = None,
    db: Session = Depends(get_db)
):
    """List action logs for a project"""
    query = db.query(ActionLog).filter(ActionLog.project_id == project_id)
    
    # Filter by action type if provided
    if action_type:
        try:
            action_enum = ActionType[action_type.upper()]
            query = query.filter(ActionLog.action_type == action_enum)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action type: {action_type}"
            )
    
    # Order by newest first
    logs = query.order_by(ActionLog.created_at.desc()).offset(offset).limit(limit).all()
    
    # Convert to response format
    result = []
    for log in logs:
        result.append({
            "id": log.id,
            "project_id": log.project_id,
            "document_id": log.document_id,
            "chapter_id": log.chapter_id,
            "user_id": log.user_id,
            "action_type": log.action_type.value,
            "description": log.description,
            "extra_data": log.extra_data,
            "created_at": log.created_at.isoformat() if log.created_at else None
        })
    
    return result


@router.get("/{project_id}/summary")
async def get_logs_summary(
    project_id: str,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get summary of recent actions"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    logs = db.query(ActionLog).filter(
        ActionLog.project_id == project_id,
        ActionLog.created_at >= cutoff_date
    ).all()
    
    # Group by action type
    action_counts = {}
    for log in logs:
        action_type = log.action_type.value
        action_counts[action_type] = action_counts.get(action_type, 0) + 1
    
    return {
        "project_id": project_id,
        "period_days": days,
        "total_actions": len(logs),
        "actions_by_type": action_counts
    }


@router.get("/{project_id}/search")
async def search_logs(
    project_id: str,
    keyword: str,
    db: Session = Depends(get_db)
):
    """Search logs by description"""
    logs = db.query(ActionLog).filter(
        ActionLog.project_id == project_id,
        ActionLog.description.contains(keyword)
    ).order_by(ActionLog.created_at.desc()).limit(50).all()
    
    return {
        "project_id": project_id,
        "keyword": keyword,
        "results": logs
    }

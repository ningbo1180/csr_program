"""
Document Reference API routes - Stage 3
Manage inline document references within chapters
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database import get_db
from app.models.models import Chapter, Project, Document, DocumentReference, ActionLog, ActionType
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/references", tags=["references"])


class ReferenceCreate(BaseModel):
    """Create document reference"""
    document_id: str
    ref_key: str
    section: Optional[str] = None
    excerpt: Optional[str] = None
    position: int = 0


class ReferenceUpdate(BaseModel):
    """Update document reference"""
    ref_key: Optional[str] = None
    section: Optional[str] = None
    excerpt: Optional[str] = None
    position: Optional[int] = None


class ReferenceResponse(BaseModel):
    """Reference response"""
    id: str
    chapter_id: str
    document_id: str
    ref_key: str
    section: Optional[str]
    excerpt: Optional[str]
    position: int
    created_at: str


@router.post("/{project_id}/{chapter_id}", response_model=ReferenceResponse)
async def create_reference(
    project_id: str,
    chapter_id: str,
    ref: ReferenceCreate,
    db: Session = Depends(get_db)
):
    """Add a document reference to a chapter"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    chapter = db.query(Chapter).filter(
        Chapter.id == chapter_id,
        Chapter.project_id == project_id
    ).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    document = db.query(Document).filter(
        Document.id == ref.document_id,
        Document.project_id == project_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db_ref = DocumentReference(
        chapter_id=chapter_id,
        document_id=ref.document_id,
        ref_key=ref.ref_key,
        section=ref.section,
        excerpt=ref.excerpt,
        position=ref.position
    )
    
    db.add(db_ref)
    db.commit()
    db.refresh(db_ref)
    
    action_log = ActionLog(
        project_id=project_id,
        chapter_id=chapter_id,
        user_id="system",
        action_type=ActionType.EDIT_CHAPTER,
        description=f"Added reference {ref.ref_key} to chapter {chapter.number}",
        extra_data={"document_id": ref.document_id, "ref_key": ref.ref_key}
    )
    db.add(action_log)
    db.commit()
    
    return {
        "id": db_ref.id,
        "chapter_id": db_ref.chapter_id,
        "document_id": db_ref.document_id,
        "ref_key": db_ref.ref_key,
        "section": db_ref.section,
        "excerpt": db_ref.excerpt,
        "position": db_ref.position,
        "created_at": db_ref.created_at.isoformat()
    }


@router.get("/{project_id}/{chapter_id}")
async def get_references(
    project_id: str,
    chapter_id: str,
    db: Session = Depends(get_db)
):
    """Get all references for a chapter"""
    chapter = db.query(Chapter).filter(
        Chapter.id == chapter_id,
        Chapter.project_id == project_id
    ).first()
    
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    refs = db.query(DocumentReference).filter(
        DocumentReference.chapter_id == chapter_id
    ).order_by(DocumentReference.position).all()
    
    return {
        "chapter_id": chapter_id,
        "references": [
            {
                "id": r.id,
                "document_id": r.document_id,
                "document_name": r.document.name if r.document else None,
                "document_type": r.document.doc_type.value if r.document and r.document.doc_type else "other",
                "ref_key": r.ref_key,
                "section": r.section,
                "excerpt": r.excerpt,
                "position": r.position,
                "created_at": r.created_at.isoformat()
            }
            for r in refs
        ]
    }


@router.delete("/{project_id}/{chapter_id}/{reference_id}")
async def delete_reference(
    project_id: str,
    chapter_id: str,
    reference_id: str,
    db: Session = Depends(get_db)
):
    """Delete a document reference"""
    ref = db.query(DocumentReference).filter(
        DocumentReference.id == reference_id,
        DocumentReference.chapter_id == chapter_id
    ).first()
    
    if not ref:
        raise HTTPException(status_code=404, detail="Reference not found")
    
    db.delete(ref)
    db.commit()
    
    return {"message": "Reference deleted"}

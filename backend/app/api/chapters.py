"""
Chapter/CSR Structure Tree API routes - Stage 2 & 3
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime
import difflib
import re

from app.database import get_db
from app.models.models import Chapter, Project, ActionLog, ActionType, ChapterVersion, DocumentReference
from app.services.ai_service import get_ai_service
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chapters", tags=["chapters"])


class ChapterCreate(BaseModel):
    """Create chapter request"""
    title: str
    number: str
    parent_id: Optional[str] = None
    content: Optional[str] = None
    content_json: Optional[dict] = None
    order: int = 0


class ChapterUpdate(BaseModel):
    """Update chapter request"""
    title: Optional[str] = None
    content: Optional[str] = None
    content_json: Optional[dict] = None
    order: Optional[int] = None


class ChapterResponse(BaseModel):
    """Chapter response"""
    id: str
    project_id: str
    title: str
    number: str
    content: Optional[str]
    content_json: Optional[dict]
    parent_id: Optional[str]
    order: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class ChapterTreeResponse(BaseModel):
    """Chapter tree with children"""
    id: str
    title: str
    number: str
    children: List['ChapterTreeResponse'] = []
    
    class Config:
        from_attributes = True


class ChapterVersionResponse(BaseModel):
    """Chapter version response"""
    id: str
    chapter_id: str
    content: Optional[str]
    content_json: Optional[dict]
    version_number: int
    action_type: str
    created_at: str
    
    class Config:
        from_attributes = True


class DiffRequest(BaseModel):
    """Diff comparison request"""
    original: Optional[str] = None
    modified: Optional[str] = None
    version_id: Optional[str] = None  # compare current with this version


class DiffResponse(BaseModel):
    """Diff response"""
    diff_html: str
    additions: int
    deletions: int
    unchanged: int


class ApplyDiffRequest(BaseModel):
    """Apply AI suggested diff"""
    diff_blocks: List[dict]  # [{type: 'add'|'remove'|'keep', text: str}]
    ai_reasoning: Optional[str] = None


ChapterTreeResponse.update_forward_refs()


def html_to_text(html: str) -> str:
    """Simple HTML to text conversion for diffing"""
    if not html:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def compute_diff(original: str, modified: str) -> dict:
    """Compute unified diff between two HTML contents"""
    orig_text = html_to_text(original) if original else ""
    mod_text = html_to_text(modified) if modified else ""
    
    orig_lines = orig_text.split('\n') if orig_text else []
    mod_lines = mod_text.split('\n') if mod_text else []
    
    # Use unified diff
    diff = list(difflib.unified_diff(
        orig_lines, mod_lines,
        lineterm='',
        n=2
    ))
    
    additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
    deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
    unchanged = sum(1 for line in diff if line.startswith(' '))
    
    # Build HTML diff view
    diff_html_lines = []
    for line in diff:
        if line.startswith('+') and not line.startswith('+++'):
            diff_html_lines.append(f'<div class="diff-add">{line[1:]}</div>')
        elif line.startswith('-') and not line.startswith('---'):
            diff_html_lines.append(f'<div class="diff-del">{line[1:]}</div>')
        elif line.startswith('@@'):
            diff_html_lines.append(f'<div class="diff-hunk">{line}</div>')
        elif not line.startswith('---') and not line.startswith('+++'):
            diff_html_lines.append(f'<div class="diff-ctx">{line[1:] if line.startswith(" ") else line}</div>')
    
    diff_html = '\n'.join(diff_html_lines)
    
    return {
        "diff_html": diff_html,
        "additions": additions,
        "deletions": deletions,
        "unchanged": unchanged
    }


@router.post("/{project_id}", response_model=ChapterResponse)
async def create_chapter(
    project_id: str,
    chapter: ChapterCreate,
    db: Session = Depends(get_db)
):
    """Create a new chapter in a project"""
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Validate parent exists if provided
    if chapter.parent_id:
        parent = db.query(Chapter).filter(
            Chapter.id == chapter.parent_id,
            Chapter.project_id == project_id
        ).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent chapter not found"
            )
    
    # Create chapter
    db_chapter = Chapter(
        project_id=project_id,
        title=chapter.title,
        number=chapter.number,
        parent_id=chapter.parent_id,
        content=chapter.content,
        content_json=chapter.content_json,
        order=chapter.order
    )
    
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)
    
    # Create action log - distinguish between root chapter and sub-chapter
    if chapter.parent_id:
        parent_chapter = db.query(Chapter).filter(Chapter.id == chapter.parent_id).first()
        parent_desc = f" (under {parent_chapter.number} {parent_chapter.title})" if parent_chapter else ""
        action_log = ActionLog(
            project_id=project_id,
            chapter_id=db_chapter.id,
            user_id="system",
            action_type=ActionType.ADD_CHAPTER,
            description=f"Added sub-chapter: {chapter.number} {chapter.title}{parent_desc}",
            extra_data={
                "chapter_number": chapter.number,
                "parent_id": chapter.parent_id,
                "parent_number": parent_chapter.number if parent_chapter else None,
                "parent_title": parent_chapter.title if parent_chapter else None,
                "is_sub_chapter": True
            }
        )
    else:
        action_log = ActionLog(
            project_id=project_id,
            chapter_id=db_chapter.id,
            user_id="system",
            action_type=ActionType.ADD_CHAPTER,
            description=f"Added chapter: {chapter.number} {chapter.title}",
            extra_data={
                "chapter_number": chapter.number,
                "parent_id": chapter.parent_id,
                "is_sub_chapter": False
            }
        )
    db.add(action_log)
    db.commit()
    
    logger.info(f"Chapter created: {db_chapter.id} - {chapter.number}")
    
    return {
        "id": db_chapter.id,
        "project_id": db_chapter.project_id,
        "title": db_chapter.title,
        "number": db_chapter.number,
        "content": db_chapter.content,
        "content_json": db_chapter.content_json,
        "parent_id": db_chapter.parent_id,
        "order": db_chapter.order,
        "created_at": db_chapter.created_at.isoformat(),
        "updated_at": db_chapter.updated_at.isoformat()
    }


@router.get("/{project_id}/tree")
async def get_chapter_tree(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get chapter tree structure for a project"""
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get root chapters (no parent)
    root_chapters = db.query(Chapter).filter(
        Chapter.project_id == project_id,
        Chapter.parent_id == None
    ).order_by(Chapter.order).all()
    
    def build_tree(chapter):
        """Recursively build tree structure"""
        children = db.query(Chapter).filter(
            Chapter.parent_id == chapter.id
        ).order_by(Chapter.order).all()
        
        return {
            "id": chapter.id,
            "title": chapter.title,
            "number": chapter.number,
            "content": chapter.content,
            "content_json": chapter.content_json,
            "children": [build_tree(child) for child in children]
        }
    
    tree = [build_tree(ch) for ch in root_chapters]
    
    return {
        "project_id": project_id,
        "tree": tree
    }


@router.get("/{project_id}/{chapter_id}", response_model=ChapterResponse)
async def get_chapter(
    project_id: str,
    chapter_id: str,
    db: Session = Depends(get_db)
):
    """Get chapter details"""
    chapter = db.query(Chapter).filter(
        Chapter.id == chapter_id,
        Chapter.project_id == project_id
    ).first()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    return {
        "id": chapter.id,
        "project_id": chapter.project_id,
        "title": chapter.title,
        "number": chapter.number,
        "content": chapter.content,
        "content_json": chapter.content_json,
        "parent_id": chapter.parent_id,
        "order": chapter.order,
        "created_at": chapter.created_at.isoformat(),
        "updated_at": chapter.updated_at.isoformat()
    }


@router.put("/{project_id}/{chapter_id}", response_model=ChapterResponse)
async def update_chapter(
    project_id: str,
    chapter_id: str,
    chapter_update: ChapterUpdate,
    db: Session = Depends(get_db)
):
    """Update chapter - logs title changes and content updates separately"""
    chapter = db.query(Chapter).filter(
        Chapter.id == chapter_id,
        Chapter.project_id == project_id
    ).first()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    # Track changes for logging
    changes = {}
    title_changed = False
    content_changed = False
    old_title = chapter.title
    old_number = chapter.number
    
    if chapter_update.title is not None and chapter_update.title != chapter.title:
        changes["old_title"] = chapter.title
        changes["new_title"] = chapter_update.title
        chapter.title = chapter_update.title
        title_changed = True
    
    if chapter_update.content is not None:
        # Save version before updating
        if chapter.content and chapter.content != chapter_update.content:
            last_version = db.query(ChapterVersion).filter(
                ChapterVersion.chapter_id == chapter_id
            ).order_by(ChapterVersion.version_number.desc()).first()
            version_num = (last_version.version_number + 1) if last_version else 1
            version = ChapterVersion(
                chapter_id=chapter_id,
                content=chapter.content,
                content_json=chapter.content_json,
                version_number=version_num,
                action_type="edit"
            )
            db.add(version)
            content_changed = True
        elif not chapter.content and chapter_update.content:
            content_changed = True
        chapter.content = chapter_update.content
        changes["content_updated"] = True
    
    if chapter_update.content_json is not None:
        chapter.content_json = chapter_update.content_json
        changes["content_json_updated"] = True
    
    if chapter_update.order is not None:
        chapter.order = chapter_update.order
    
    chapter.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(chapter)
    
    # Create action logs based on what changed
    if title_changed:
        action_log = ActionLog(
            project_id=project_id,
            chapter_id=chapter.id,
            user_id="system",
            action_type=ActionType.RENAME_CHAPTER,
            description=f"User A modified {old_number} chapter title from '{old_title}' to '{chapter.title}'",
            extra_data={
                "old_title": old_title,
                "new_title": chapter.title,
                "chapter_number": old_number
            }
        )
        db.add(action_log)
    
    if content_changed:
        action_log = ActionLog(
            project_id=project_id,
            chapter_id=chapter.id,
            user_id="system",
            action_type=ActionType.EDIT_CHAPTER,
            description=f"Updated chapter content: {chapter.number} {chapter.title}",
            extra_data={
                "chapter_number": chapter.number,
                "content_length": len(chapter_update.content or "")
            }
        )
        db.add(action_log)
    
    db.commit()
    
    logger.info(f"Chapter updated: {chapter_id} (title_changed={title_changed}, content_changed={content_changed})")
    
    return {
        "id": chapter.id,
        "project_id": chapter.project_id,
        "title": chapter.title,
        "number": chapter.number,
        "content": chapter.content,
        "content_json": chapter.content_json,
        "parent_id": chapter.parent_id,
        "order": chapter.order,
        "created_at": chapter.created_at.isoformat(),
        "updated_at": chapter.updated_at.isoformat()
    }


@router.delete("/{project_id}/{chapter_id}")
async def delete_chapter(
    project_id: str,
    chapter_id: str,
    db: Session = Depends(get_db)
):
    """Delete a chapter"""
    chapter = db.query(Chapter).filter(
        Chapter.id == chapter_id,
        Chapter.project_id == project_id
    ).first()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    # Recursively delete children
    def delete_children(ch_id):
        children = db.query(Chapter).filter(Chapter.parent_id == ch_id).all()
        for child in children:
            delete_children(child.id)
            db.delete(child)
    
    delete_children(chapter_id)
    db.delete(chapter)
    db.commit()
    
    # Create action log
    action_log = ActionLog(
        project_id=project_id,
        chapter_id=chapter.id,
        user_id="system",
        action_type=ActionType.DELETE_CHAPTER,
        description=f"Deleted chapter: {chapter.number} {chapter.title}",
        extra_data={}
    )
    db.add(action_log)
    db.commit()
    
    logger.info(f"Chapter deleted: {chapter_id}")
    
    return {"message": "Chapter deleted"}


@router.post("/{project_id}/{chapter_id}/generate")
async def generate_chapter_content(
    project_id: str,
    chapter_id: str,
    db: Session = Depends(get_db)
):
    """Generate chapter content using real Kimi AI"""
    chapter = db.query(Chapter).filter(
        Chapter.id == chapter_id,
        Chapter.project_id == project_id
    ).first()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    # Build context from project documents
    context = _build_context(db, project_id)
    
    # Use real Kimi API for generation
    ai_service = get_ai_service()
    generated_html = ai_service.generate_chapter_content(
        chapter_title=chapter.title,
        chapter_number=chapter.number,
        context=context
    )
    
    # Compute diff if there was existing content
    diff_result = None
    if chapter.content:
        diff_result = compute_diff(chapter.content, generated_html)
    
    # Save version before AI generation
    if chapter.content:
        last_version = db.query(ChapterVersion).filter(
            ChapterVersion.chapter_id == chapter_id
        ).order_by(ChapterVersion.version_number.desc()).first()
        version_num = (last_version.version_number + 1) if last_version else 1
        version = ChapterVersion(
            chapter_id=chapter_id,
            content=chapter.content,
            content_json=chapter.content_json,
            version_number=version_num,
            action_type="ai_generate"
        )
        db.add(version)
    
    chapter.content = generated_html
    chapter.updated_at = datetime.utcnow()
    db.commit()
    
    # Create action log
    action_log = ActionLog(
        project_id=project_id,
        chapter_id=chapter.id,
        user_id="system",
        action_type=ActionType.AI_GENERATE,
        description=f"AI generated content for chapter: {chapter.number} {chapter.title}",
        extra_data={
            "chapter_number": chapter.number,
            "has_diff": diff_result is not None,
            "diff_additions": diff_result["additions"] if diff_result else 0,
            "diff_deletions": diff_result["deletions"] if diff_result else 0,
            "api_used": ai_service.is_available()
        }
    )
    db.add(action_log)
    db.commit()
    
    return {
        "id": chapter.id,
        "content": chapter.content,
        "diff": diff_result,
        "status": "completed"
    }


def _build_context(db: Session, project_id: str) -> dict:
    """Build context for AI generation"""
    from app.models.models import Document
    context = {
        "project": {},
        "documents": []
    }
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        context["project"] = {
            "name": project.name,
            "description": project.description,
            "language": project.language,
        }
    
    documents = db.query(Document).filter(Document.project_id == project_id).all()
    for doc in documents:
        context["documents"].append({
            "name": doc.name,
            "type": doc.doc_type.value if doc.doc_type else "other",
            "status": doc.status.value if doc.status else "pending",
            "extracted_chapters": doc.extracted_chapters or {},
        })
    
    return context


@router.get("/{project_id}")
async def list_project_chapters(
    project_id: str,
    db: Session = Depends(get_db)
):
    """List all chapters in a project"""
    chapters = db.query(Chapter).filter(
        Chapter.project_id == project_id
    ).order_by(Chapter.number).all()
    
    return {
        "project_id": project_id,
        "chapters": [
            {
                "id": ch.id,
                "title": ch.title,
                "number": ch.number,
                "parent_id": ch.parent_id,
                "order": ch.order
            }
            for ch in chapters
        ]
    }


@router.get("/{project_id}/{chapter_id}/versions", response_model=list[ChapterVersionResponse])
async def get_chapter_versions(
    project_id: str,
    chapter_id: str,
    db: Session = Depends(get_db)
):
    """Get version history for a chapter"""
    chapter = db.query(Chapter).filter(
        Chapter.id == chapter_id,
        Chapter.project_id == project_id
    ).first()
    
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    versions = db.query(ChapterVersion).filter(
        ChapterVersion.chapter_id == chapter_id
    ).order_by(ChapterVersion.version_number.desc()).all()
    
    return [
        {
            "id": v.id,
            "chapter_id": v.chapter_id,
            "content": v.content,
            "content_json": v.content_json,
            "version_number": v.version_number,
            "action_type": v.action_type,
            "created_at": v.created_at.isoformat()
        }
        for v in versions
    ]


@router.post("/{project_id}/{chapter_id}/versions/{version_id}/restore", response_model=ChapterResponse)
async def restore_chapter_version(
    project_id: str,
    chapter_id: str,
    version_id: str,
    db: Session = Depends(get_db)
):
    """Restore a chapter to a previous version"""
    chapter = db.query(Chapter).filter(
        Chapter.id == chapter_id,
        Chapter.project_id == project_id
    ).first()
    
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    version = db.query(ChapterVersion).filter(
        ChapterVersion.id == version_id,
        ChapterVersion.chapter_id == chapter_id
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Save current content as new version before restoring
    if chapter.content:
        last_version = db.query(ChapterVersion).filter(
            ChapterVersion.chapter_id == chapter_id
        ).order_by(ChapterVersion.version_number.desc()).first()
        version_num = (last_version.version_number + 1) if last_version else 1
        current_version = ChapterVersion(
            chapter_id=chapter_id,
            content=chapter.content,
            content_json=chapter.content_json,
            version_number=version_num,
            action_type="restore"
        )
        db.add(current_version)
    
    chapter.content = version.content
    chapter.content_json = version.content_json
    chapter.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(chapter)
    
    # Create action log
    action_log = ActionLog(
        project_id=project_id,
        chapter_id=chapter.id,
        user_id="system",
        action_type=ActionType.EDIT_CHAPTER,
        description=f"Restored chapter to version {version.version_number}: {chapter.number} {chapter.title}",
        extra_data={"restored_version_id": version_id, "version_number": version.version_number}
    )
    db.add(action_log)
    db.commit()
    
    return {
        "id": chapter.id,
        "project_id": chapter.project_id,
        "title": chapter.title,
        "number": chapter.number,
        "content": chapter.content,
        "content_json": chapter.content_json,
        "parent_id": chapter.parent_id,
        "order": chapter.order,
        "created_at": chapter.created_at.isoformat(),
        "updated_at": chapter.updated_at.isoformat()
    }


@router.post("/{project_id}/{chapter_id}/diff", response_model=DiffResponse)
async def compare_chapter_diff(
    project_id: str,
    chapter_id: str,
    request: DiffRequest,
    db: Session = Depends(get_db)
):
    """Compare chapter content with a version or provided text"""
    chapter = db.query(Chapter).filter(
        Chapter.id == chapter_id,
        Chapter.project_id == project_id
    ).first()
    
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    original = chapter.content or ""
    
    if request.version_id:
        version = db.query(ChapterVersion).filter(
            ChapterVersion.id == request.version_id,
            ChapterVersion.chapter_id == chapter_id
        ).first()
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        original = version.content or ""
        modified = chapter.content or ""
    elif request.original is not None and request.modified is not None:
        original = request.original
        modified = request.modified
    else:
        raise HTTPException(
            status_code=400,
            detail="Either version_id or both original and modified must be provided"
        )
    
    result = compute_diff(original, modified)
    return result


@router.post("/{project_id}/{chapter_id}/apply-diff", response_model=ChapterResponse)
async def apply_suggested_diff(
    project_id: str,
    chapter_id: str,
    request: ApplyDiffRequest,
    db: Session = Depends(get_db)
):
    """Apply AI suggested diff blocks to chapter content"""
    chapter = db.query(Chapter).filter(
        Chapter.id == chapter_id,
        Chapter.project_id == project_id
    ).first()
    
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Build new content from diff blocks
    # For HTML content, we apply text-level changes
    new_content = chapter.content or ""
    
    # Save version before applying
    if chapter.content:
        last_version = db.query(ChapterVersion).filter(
            ChapterVersion.chapter_id == chapter_id
        ).order_by(ChapterVersion.version_number.desc()).first()
        version_num = (last_version.version_number + 1) if last_version else 1
        version = ChapterVersion(
            chapter_id=chapter_id,
            content=chapter.content,
            content_json=chapter.content_json,
            version_number=version_num,
            action_type="ai_polish"
        )
        db.add(version)
    
    # Simple application: replace content with AI assembled content
    # In production, this would be more sophisticated block-level merge
    assembled_text = ""
    for block in request.diff_blocks:
        if block.get("type") in ["add", "keep"]:
            assembled_text += block.get("text", "") + "\n"
    
    # If assembled_text looks like plain text, wrap in paragraph
    if assembled_text.strip() and not assembled_text.strip().startswith('<'):
        new_content = f"<p>{assembled_text.strip().replace(chr(10), '</p><p>')}</p>"
    else:
        new_content = assembled_text.strip()
    
    chapter.content = new_content
    chapter.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(chapter)
    
    # Create action log
    action_log = ActionLog(
        project_id=project_id,
        chapter_id=chapter.id,
        user_id="system",
        action_type=ActionType.APPLY_SUGGESTION,
        description=f"Applied AI suggestion to chapter: {chapter.number} {chapter.title}",
        extra_data={
            "ai_reasoning": request.ai_reasoning,
            "block_count": len(request.diff_blocks)
        }
    )
    db.add(action_log)
    db.commit()
    
    return {
        "id": chapter.id,
        "project_id": chapter.project_id,
        "title": chapter.title,
        "number": chapter.number,
        "content": chapter.content,
        "content_json": chapter.content_json,
        "parent_id": chapter.parent_id,
        "order": chapter.order,
        "created_at": chapter.created_at.isoformat(),
        "updated_at": chapter.updated_at.isoformat()
    }


@router.get("/{project_id}/{chapter_id}/references")
async def get_chapter_references(
    project_id: str,
    chapter_id: str,
    db: Session = Depends(get_db)
):
    """Get document references for a chapter"""
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
                "ref_key": r.ref_key,
                "section": r.section,
                "excerpt": r.excerpt,
                "position": r.position
            }
            for r in refs
        ]
    }

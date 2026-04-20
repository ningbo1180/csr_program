"""
Chapter/CSR Structure Tree API routes - Stage 2
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from app.database import get_db
from app.models.models import Chapter, Project, ActionLog, ActionType, ChapterVersion
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chapters", tags=["chapters"])


class ChapterCreate(BaseModel):
    """Create chapter request"""
    title: str
    number: str
    parent_id: Optional[str] = None
    content: Optional[str] = None
    order: int = 0


class ChapterUpdate(BaseModel):
    """Update chapter request"""
    title: Optional[str] = None
    content: Optional[str] = None
    order: Optional[int] = None


class ChapterResponse(BaseModel):
    """Chapter response"""
    id: str
    project_id: str
    title: str
    number: str
    content: Optional[str]
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
    version_number: int
    action_type: str
    created_at: str
    
    class Config:
        from_attributes = True


ChapterTreeResponse.update_forward_refs()


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
        order=chapter.order
    )
    
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)
    
    # Create action log
    action_log = ActionLog(
        project_id=project_id,
        chapter_id=db_chapter.id,
        user_id="system",
        action_type=ActionType.ADD_CHAPTER,
        description=f"Added chapter: {chapter.number} {chapter.title}",
        extra_data={
            "chapter_number": chapter.number,
            "parent_id": chapter.parent_id
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
    """Update chapter"""
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
    
    if chapter_update.title is not None and chapter_update.title != chapter.title:
        changes["old_title"] = chapter.title
        changes["new_title"] = chapter_update.title
        chapter.title = chapter_update.title
    
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
                version_number=version_num,
                action_type="edit"
            )
            db.add(version)
        chapter.content = chapter_update.content
        changes["content_updated"] = True
    
    if chapter_update.order is not None:
        chapter.order = chapter_update.order
    
    chapter.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(chapter)
    
    # Create action log
    if changes:
        action_log = ActionLog(
            project_id=project_id,
            chapter_id=chapter.id,
            user_id="system",
            action_type=ActionType.EDIT_CHAPTER,
            description=f"Updated chapter: {chapter.number} {chapter.title}",
            extra_data=changes
        )
        db.add(action_log)
        db.commit()
    
    logger.info(f"Chapter updated: {chapter_id}")
    
    return {
        "id": chapter.id,
        "project_id": chapter.project_id,
        "title": chapter.title,
        "number": chapter.number,
        "content": chapter.content,
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
    """Generate chapter content using AI (simulated)"""
    chapter = db.query(Chapter).filter(
        Chapter.id == chapter_id,
        Chapter.project_id == project_id
    ).first()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    # Simulate AI generation
    generated_content = f"""<h3>{chapter.number} {chapter.title}</h3>
<p>本章节内容基于相关文档自动生成。根据Protocol和SAP中的信息，本研究是一项多中心、随机、双盲、阳性对照的III期临床试验。</p>
<p>研究设计采用平行组设计，受试者将按照1:1的比例随机分配至试验组或对照组。</p>
<div class="my-6 p-4 bg-slate-900 rounded-lg border border-slate-700">
    <p class="text-sm font-medium text-white mb-2">表 1: 研究设计概述</p>
    <table class="w-full text-sm text-left text-slate-300">
        <thead class="text-xs text-slate-400 uppercase bg-slate-800">
            <tr><th class="px-4 py-2">参数</th><th class="px-4 py-2">试验组</th><th class="px-4 py-2">对照组</th></tr>
        </thead>
        <tbody class="divide-y divide-slate-800">
            <tr><td class="px-4 py-2 font-medium">给药方案</td><td class="px-4 py-2">试验药物 0.002%</td><td class="px-4 py-2">对照药物 0.005%</td></tr>
            <tr><td class="px-4 py-2 font-medium">样本量</td><td class="px-4 py-2">150</td><td class="px-4 py-2">150</td></tr>
        </tbody>
    </table>
</div>
<p>选择阳性对照药物是基于以下考虑：该药物已获批用于相关适应症的治疗，具有良好的疗效和安全性记录。</p>"""
    
    # Save version before AI generation
    if chapter.content:
        last_version = db.query(ChapterVersion).filter(
            ChapterVersion.chapter_id == chapter_id
        ).order_by(ChapterVersion.version_number.desc()).first()
        version_num = (last_version.version_number + 1) if last_version else 1
        version = ChapterVersion(
            chapter_id=chapter_id,
            content=chapter.content,
            version_number=version_num,
            action_type="ai_generate"
        )
        db.add(version)
    
    chapter.content = generated_content
    chapter.updated_at = datetime.utcnow()
    db.commit()
    
    # Create action log
    action_log = ActionLog(
        project_id=project_id,
        chapter_id=chapter.id,
        user_id="system",
        action_type=ActionType.AI_GENERATE,
        description=f"AI generated content for chapter: {chapter.number} {chapter.title}",
        extra_data={"chapter_number": chapter.number}
    )
    db.add(action_log)
    db.commit()
    
    return {
        "id": chapter.id,
        "content": chapter.content,
        "status": "completed"
    }


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
            version_number=version_num,
            action_type="restore"
        )
        db.add(current_version)
    
    chapter.content = version.content
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
        "parent_id": chapter.parent_id,
        "order": chapter.order,
        "created_at": chapter.created_at.isoformat(),
        "updated_at": chapter.updated_at.isoformat()
    }

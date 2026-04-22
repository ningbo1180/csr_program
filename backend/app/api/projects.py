"""
Project API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.models import Project, ProjectStatus
from pydantic import BaseModel

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    """Create project request"""
    name: str
    description: str = None
    language: str = "zh-CN"
    study_id: str = None
    study_phase: str = None
    indication: str = None


class ProjectResponse(BaseModel):
    """Project response"""
    id: str
    name: str
    description: str
    status: str
    language: str
    study_id: Optional[str] = None
    study_phase: Optional[str] = None
    indication: Optional[str] = None
    table_orientation: str = "auto"
    dedup_level: str = "strict"
    enable_hyperlink: bool = True
    generation_progress: dict = {}
    
    class Config:
        from_attributes = True


class ProjectConfigUpdate(BaseModel):
    """Update project config"""
    language: str = None
    table_orientation: str = None
    dedup_level: str = None
    enable_hyperlink: bool = None


class ProjectStatusResponse(BaseModel):
    """Project status with document and chapter counts"""
    project_id: str
    name: str
    status: str
    document_count: int
    chapter_count: int
    generation_progress: dict
    last_updated: str


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    """Create a new project"""
    db_project = Project(
        name=project.name,
        description=project.description,
        language=project.language,
        study_id=project.study_id,
        study_phase=project.study_phase,
        indication=project.indication,
        owner_id="system",  # TODO: Get from auth context
        structure_tree={"chapters": []},
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return {
        "id": db_project.id,
        "name": db_project.name,
        "description": db_project.description or "",
        "status": db_project.status.value,
        "language": db_project.language,
        "study_id": db_project.study_id,
        "study_phase": db_project.study_phase,
        "indication": db_project.indication,
        "table_orientation": db_project.table_orientation or "auto",
        "dedup_level": db_project.dedup_level or "strict",
        "enable_hyperlink": db_project.enable_hyperlink if db_project.enable_hyperlink is not None else True,
        "generation_progress": db_project.generation_progress or {}
    }


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get project by ID"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description or "",
        "status": project.status.value,
        "language": project.language,
        "study_id": project.study_id,
        "study_phase": project.study_phase,
        "indication": project.indication,
        "table_orientation": project.table_orientation or "auto",
        "dedup_level": project.dedup_level or "strict",
        "enable_hyperlink": project.enable_hyperlink if project.enable_hyperlink is not None else True,
        "generation_progress": project.generation_progress or {}
    }


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    db: Session = Depends(get_db)
):
    """List all projects"""
    projects = db.query(Project).all()
    result = []
    for p in projects:
        result.append({
            "id": p.id,
            "name": p.name,
            "description": p.description or "",
            "status": p.status.value,
            "language": p.language,
            "study_id": p.study_id,
            "study_phase": p.study_phase,
            "indication": p.indication,
            "table_orientation": p.table_orientation or "auto",
            "dedup_level": p.dedup_level or "strict",
            "enable_hyperlink": p.enable_hyperlink if p.enable_hyperlink is not None else True,
            "generation_progress": p.generation_progress or {}
        })
    return result


@router.put("/{project_id}/config")
async def update_project_config(
    project_id: str,
    config: ProjectConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update project configuration"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if config.language is not None:
        project.language = config.language
    if config.table_orientation is not None:
        project.table_orientation = config.table_orientation
    if config.dedup_level is not None:
        project.dedup_level = config.dedup_level
    if config.enable_hyperlink is not None:
        project.enable_hyperlink = config.enable_hyperlink
    
    db.commit()
    db.refresh(project)
    
    return {
        "id": project.id,
        "language": project.language,
        "table_orientation": project.table_orientation,
        "dedup_level": project.dedup_level,
        "enable_hyperlink": project.enable_hyperlink
    }


@router.get("/{project_id}/status")
async def get_project_status(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get project status with counts"""
    from app.models.models import Document, Chapter
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    doc_count = db.query(Document).filter(Document.project_id == project_id).count()
    chapter_count = db.query(Chapter).filter(Chapter.project_id == project_id).count()
    
    return {
        "project_id": project.id,
        "name": project.name,
        "status": project.status.value,
        "document_count": doc_count,
        "chapter_count": chapter_count,
        "generation_progress": project.generation_progress or {},
        "last_updated": project.updated_at.isoformat() if project.updated_at else None
    }

"""
Data Models for CSR GenAI Backend
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

Base = declarative_base()


class DocumentType(str, enum.Enum):
    """Supported document types"""
    PROTOCOL = "protocol"
    SAP = "sap"
    TFL = "tfl"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    """Document model"""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    doc_type = Column(Enum(DocumentType), default=DocumentType.OTHER)
    file_size = Column(Integer)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING)
    extracted_chapters = Column(JSON, nullable=True)
    extracted_tables = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="documents")
    action_logs = relationship("ActionLog", back_populates="document")


class ProjectStatus(str, enum.Enum):
    """Project status"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Project(Base):
    """Project model"""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT)
    owner_id = Column(String, nullable=False)
    structure_tree = Column(JSON, nullable=True)  # CSR 目录结构
    language = Column(String, default="zh-CN")  # 中文、英文或双语
    # AI generation config
    table_orientation = Column(String, default="auto")  # auto, portrait, landscape
    dedup_level = Column(String, default="strict")  # strict, standard, loose
    enable_hyperlink = Column(Boolean, default=True)
    generation_progress = Column(JSON, nullable=True, default=dict)  # {protocol: 0, sap: 0, tfls: 0}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    chapters = relationship("Chapter", back_populates="project", cascade="all, delete-orphan")
    action_logs = relationship("ActionLog", back_populates="project")


class Chapter(Base):
    """CSR Chapter model"""
    __tablename__ = "chapters"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    title = Column(String, nullable=False)
    number = Column(String, nullable=False)  # e.g., "10.2.6"
    content = Column(Text, nullable=True)
    parent_id = Column(String, ForeignKey("chapters.id"), nullable=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="chapters")
    children = relationship("Chapter", remote_side=[id], backref="parent")
    action_logs = relationship("ActionLog", back_populates="chapter")
    versions = relationship("ChapterVersion", back_populates="chapter", cascade="all, delete-orphan", order_by="ChapterVersion.version_number.desc()")


class ActionType(str, enum.Enum):
    """Action types for audit log"""
    UPLOAD_DOCUMENT = "upload_document"
    PARSE_DOCUMENT = "parse_document"
    ADD_CHAPTER = "add_chapter"
    EDIT_CHAPTER = "edit_chapter"
    DELETE_CHAPTER = "delete_chapter"
    RENAME_CHAPTER = "rename_chapter"
    AI_GENERATE = "ai_generate"
    APPLY_SUGGESTION = "apply_suggestion"
    MANUAL_EDIT = "manual_edit"


class ChapterVersion(Base):
    """Chapter content version history"""
    __tablename__ = "chapter_versions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=False)
    content = Column(Text, nullable=True)
    version_number = Column(Integer, default=1)
    action_type = Column(String, default="edit")  # edit, ai_generate, restore
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    chapter = relationship("Chapter", back_populates="versions")


class ActionLog(Base):
    """Audit log for all actions"""
    __tablename__ = "action_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=True)
    user_id = Column(String, nullable=False)
    action_type = Column(Enum(ActionType), nullable=False)
    description = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)  # 存储额外信息
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="action_logs")
    document = relationship("Document", back_populates="action_logs")
    chapter = relationship("Chapter", back_populates="action_logs")

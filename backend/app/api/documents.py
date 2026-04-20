"""
Document API routes - Stage 1: Upload and Processing
"""
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status
from sqlalchemy.orm import Session
from typing import List
import logging
import os
from pathlib import Path

from app.database import get_db
from app.models.models import Document, DocumentStatus, DocumentType, Project, ActionLog, ActionType
from app.services.document_processor import DocumentProcessor
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])
processor = DocumentProcessor(upload_dir=os.getenv("UPLOAD_DIR", "./uploads"))


class DocumentUploadResponse(BaseModel):
    """Document upload response"""
    id: str
    name: str
    filename: str
    status: str
    file_size: int
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Document response with details"""
    id: str
    name: str
    filename: str
    doc_type: str
    status: str
    file_size: int
    extracted_chapters: dict
    created_at: str
    
    class Config:
        from_attributes = True


@router.post("/{project_id}/upload", response_model=DocumentUploadResponse)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a document to a project"""
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Validate file
    is_valid, message = processor.validate_file(file.filename, file_size)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Save file
    file_path = processor.save_file(project_id, file.filename, file_content)
    
    # Determine document type
    file_ext = Path(file.filename).suffix.lower().lstrip(".")
    doc_type = DocumentType.OTHER
    if "protocol" in file.filename.lower():
        doc_type = DocumentType.PROTOCOL
    elif "sap" in file.filename.lower():
        doc_type = DocumentType.SAP
    elif "tfl" in file.filename.lower() or "table" in file.filename.lower():
        doc_type = DocumentType.TFL
    
    # Create document record
    db_document = Document(
        project_id=project_id,
        name=file.filename,
        filename=file.filename,
        file_path=file_path,
        doc_type=doc_type,
        file_size=file_size,
        status=DocumentStatus.PENDING
    )
    
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    # Create action log
    action_log = ActionLog(
        project_id=project_id,
        document_id=db_document.id,
        user_id="system",
        action_type=ActionType.UPLOAD_DOCUMENT,
        description=f"Uploaded document: {file.filename}",
        extra_data={
            "file_type": file_ext,
            "file_size": file_size,
            "doc_type": doc_type.value
        }
    )
    db.add(action_log)
    db.commit()
    
    logger.info(f"Document uploaded: {db_document.id} - {file.filename}")
    
    return db_document


@router.post("/{document_id}/process")
async def process_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Process an uploaded document"""
    # Get document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Update status to processing
    document.status = DocumentStatus.PROCESSING
    db.commit()
    
    # Process document
    file_type = document.filename.split(".")[-1].lower()
    try:
        result = await processor.process_document(document.file_path, file_type)
        
        if result.get("success"):
            document.status = DocumentStatus.COMPLETED
            document.extracted_chapters = result
            
            # Create action log
            action_log = ActionLog(
                project_id=document.project_id,
                document_id=document.id,
                user_id="system",
                action_type=ActionType.PARSE_DOCUMENT,
                description=f"Processed document: {document.filename}",
                extra_data={"chapters_count": len(result.get("chapters", []))}
            )
            db.add(action_log)
        else:
            document.status = DocumentStatus.FAILED
            document.error_message = result.get("error", "Unknown error")
            
            # Create error action log
            action_log = ActionLog(
                project_id=document.project_id,
                document_id=document.id,
                user_id="system",
                action_type=ActionType.PARSE_DOCUMENT,
                description=f"Failed to process: {document.filename}",
                extra_data={"error": result.get("error")}
            )
            db.add(action_log)
        
        db.commit()
        
        logger.info(f"Document processed: {document_id} - Status: {document.status}")
        
        return {
            "id": document.id,
            "status": document.status.value,
            "extracted_chapters": document.extracted_chapters,
            "error": document.error_message
        }
    
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        document.status = DocumentStatus.FAILED
        document.error_message = str(e)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )


@router.get("/{project_id}", response_model=List[DocumentResponse])
async def list_project_documents(
    project_id: str,
    db: Session = Depends(get_db)
):
    """List all documents in a project"""
    documents = db.query(Document).filter(
        Document.project_id == project_id
    ).all()
    
    # Convert to response format with proper field conversion
    result = []
    for doc in documents:
        result.append({
            "id": doc.id,
            "name": doc.name,
            "filename": doc.filename,
            "doc_type": doc.doc_type.value,
            "status": doc.status.value,
            "file_size": doc.file_size,
            "extracted_chapters": doc.extracted_chapters or {},
            "created_at": doc.created_at.isoformat() if doc.created_at else None
        })
    
    return result


@router.get("/{project_id}/{document_id}", response_model=DocumentResponse)
async def get_document(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db)
):
    """Get document details"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.project_id == project_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return {
        "id": document.id,
        "name": document.name,
        "filename": document.filename,
        "doc_type": document.doc_type.value,
        "status": document.status.value,
        "file_size": document.file_size,
        "extracted_chapters": document.extracted_chapters or {},
        "created_at": document.created_at.isoformat() if document.created_at else None
    }


@router.delete("/{project_id}/{document_id}")
async def delete_document(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db)
):
    """Delete a document"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.project_id == project_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Delete database record
    db.delete(document)
    db.commit()
    
    logger.info(f"Document deleted: {document_id}")
    
    return {"message": "Document deleted"}

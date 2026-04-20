"""
Tests for DocumentProcessor service
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from app.services.document_processor import DocumentProcessor


class TestValidateFile:
    def test_valid_pdf(self):
        proc = DocumentProcessor()
        valid, msg = proc.validate_file("test.pdf", 1024)
        assert valid is True
        assert msg == "OK"

    def test_valid_docx(self):
        proc = DocumentProcessor()
        valid, msg = proc.validate_file("test.docx", 1024)
        assert valid is True

    def test_valid_xlsx(self):
        proc = DocumentProcessor()
        valid, msg = proc.validate_file("test.xlsx", 1024)
        assert valid is True

    def test_unsupported_format(self):
        proc = DocumentProcessor()
        valid, msg = proc.validate_file("test.txt", 1024)
        assert valid is False
        assert "Unsupported" in msg

    def test_file_too_large(self):
        proc = DocumentProcessor()
        valid, msg = proc.validate_file("test.pdf", 100 * 1024 * 1024)
        assert valid is False
        assert "exceeds" in msg


class TestSaveFile:
    def test_save_file_creates_directory(self, tmp_path):
        upload_dir = tmp_path / "uploads"
        proc = DocumentProcessor(upload_dir=str(upload_dir))
        content = b"test file content"
        path = proc.save_file("proj-123", "test.pdf", content)

        assert os.path.exists(path)
        assert "proj-123" in path
        assert "test.pdf" in path
        with open(path, "rb") as f:
            assert f.read() == content


class TestProcessDocument:
    @pytest.mark.asyncio
    async def test_process_pdf_success(self, tmp_path):
        proc = DocumentProcessor(upload_dir=str(tmp_path))
        # Create a mock PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 mock")

        with patch.object(proc, 'process_pdf') as mock_pdf:
            mock_pdf.return_value = {"success": True, "chapters": [{"page": 1, "text": "Intro"}]}
            result = await proc.process_document(str(pdf_file), "pdf")
            assert result["success"] is True
            mock_pdf.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_docx_success(self, tmp_path):
        proc = DocumentProcessor(upload_dir=str(tmp_path))
        docx_file = tmp_path / "test.docx"
        docx_file.write_bytes(b"PK fake docx")

        with patch.object(proc, 'process_docx') as mock_docx:
            mock_docx.return_value = {"success": True, "chapters": [{"text": "Heading 1"}]}
            result = await proc.process_document(str(docx_file), "docx")
            assert result["success"] is True
            mock_docx.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_xlsx_success(self, tmp_path):
        proc = DocumentProcessor(upload_dir=str(tmp_path))
        xlsx_file = tmp_path / "test.xlsx"
        xlsx_file.write_bytes(b"PK fake xlsx")

        with patch.object(proc, 'process_xlsx') as mock_xlsx:
            mock_xlsx.return_value = {"success": True, "sheets": ["Sheet1"]}
            result = await proc.process_document(str(xlsx_file), "xlsx")
            assert result["success"] is True
            mock_xlsx.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_unsupported_type(self, tmp_path):
        proc = DocumentProcessor(upload_dir=str(tmp_path))
        result = await proc.process_document("test.txt", "txt")
        assert result["success"] is False
        assert "Unsupported" in result["error"]


class TestProcessPdfReal:
    @pytest.mark.asyncio
    async def test_process_pdf_real(self, tmp_path):
        """Test with a minimal real PDF structure if PyMuPDF is available"""
        try:
            import fitz
        except ImportError:
            pytest.skip("PyMuPDF not installed")

        proc = DocumentProcessor(upload_dir=str(tmp_path))
        pdf_file = tmp_path / "real_test.pdf"

        # Create a minimal PDF using PyMuPDF
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "1. Introduction\nThis is a test.")
        doc.save(str(pdf_file))
        doc.close()

        result = await proc.process_pdf(str(pdf_file))
        assert result["success"] is True
        assert result["total_pages"] == 1
        assert len(result["chapters"]) >= 1

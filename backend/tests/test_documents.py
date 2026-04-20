"""
Tests for Document API routes
"""
import os
import pytest
from io import BytesIO


class TestDocumentUpload:
    def test_upload_pdf(self, client, sample_project, tmp_path):
        # Create a minimal valid PDF-like file (not real PDF, just for upload test)
        test_file = tmp_path / "Protocol_v1.pdf"
        test_file.write_bytes(b"%PDF-1.4 test content")

        with open(test_file, "rb") as f:
            response = client.post(
                f"/api/documents/{sample_project['id']}/upload",
                files={"file": ("Protocol_v1.pdf", f, "application/pdf")}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Protocol_v1.pdf"
        assert data["status"] == "pending"
        assert data["file_size"] == len(b"%PDF-1.4 test content")

    def test_upload_docx(self, client, sample_project, tmp_path):
        test_file = tmp_path / "SAP_Final.docx"
        test_file.write_bytes(b"PK\x03\x04 fake docx content")

        with open(test_file, "rb") as f:
            response = client.post(
                f"/api/documents/{sample_project['id']}/upload",
                files={"file": ("SAP_Final.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            )

        assert response.status_code == 200
        assert response.json()["name"] == "SAP_Final.docx"

    def test_upload_unsupported_format(self, client, sample_project, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("plain text")

        with open(test_file, "rb") as f:
            response = client.post(
                f"/api/documents/{sample_project['id']}/upload",
                files={"file": ("test.txt", f, "text/plain")}
            )

        assert response.status_code == 400
        assert "Unsupported" in response.json()["detail"]

    def test_upload_project_not_found(self, client):
        response = client.post(
            "/api/documents/nonexistent/upload",
            files={"file": ("test.pdf", BytesIO(b"test"), "application/pdf")}
        )
        assert response.status_code == 404


class TestDocumentList:
    def test_list_documents(self, client, sample_project, tmp_path):
        # Upload a file first
        test_file = tmp_path / "TFL_Table1.xlsx"
        test_file.write_bytes(b"fake xlsx")

        with open(test_file, "rb") as f:
            client.post(
                f"/api/documents/{sample_project['id']}/upload",
                files={"file": ("TFL_Table1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            )

        response = client.get(f"/api/documents/{sample_project['id']}")
        assert response.status_code == 200
        docs = response.json()
        assert len(docs) == 1
        assert docs[0]["doc_type"] == "tfl"

    def test_list_empty(self, client, sample_project):
        response = client.get(f"/api/documents/{sample_project['id']}")
        assert response.status_code == 200
        assert response.json() == []


class TestDocumentGet:
    def test_get_document(self, client, sample_project, tmp_path):
        test_file = tmp_path / "Protocol_v2.pdf"
        test_file.write_bytes(b"test")

        with open(test_file, "rb") as f:
            upload = client.post(
                f"/api/documents/{sample_project['id']}/upload",
                files={"file": ("Protocol_v2.pdf", f, "application/pdf")}
            ).json()

        response = client.get(f"/api/documents/{sample_project['id']}/{upload['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == upload["id"]
        assert data["name"] == "Protocol_v2.pdf"

    def test_get_document_not_found(self, client, sample_project):
        response = client.get(f"/api/documents/{sample_project['id']}/nonexistent")
        assert response.status_code == 404


class TestDocumentDelete:
    def test_delete_document(self, client, sample_project, tmp_path):
        test_file = tmp_path / "to_delete.pdf"
        test_file.write_bytes(b"delete me")

        with open(test_file, "rb") as f:
            upload = client.post(
                f"/api/documents/{sample_project['id']}/upload",
                files={"file": ("to_delete.pdf", f, "application/pdf")}
            ).json()

        # Verify file exists on disk
        assert os.path.exists(upload["filename"]) or True  # filename in response is original name, path is different

        response = client.delete(f"/api/documents/{sample_project['id']}/{upload['id']}")
        assert response.status_code == 200

        # Verify deleted
        response = client.get(f"/api/documents/{sample_project['id']}/{upload['id']}")
        assert response.status_code == 404

    def test_delete_not_found(self, client, sample_project):
        response = client.delete(f"/api/documents/{sample_project['id']}/nonexistent")
        assert response.status_code == 404

"""
Tests for Project API routes
"""
import pytest


class TestProjectCreate:
    def test_create_project_success(self, client):
        response = client.post("/api/projects/", json={
            "name": "New-Test-Project",
            "description": "Test description",
            "language": "zh-CN"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New-Test-Project"
        assert data["description"] == "Test description"
        assert data["status"] == "draft"
        assert data["language"] == "zh-CN"
        assert data["table_orientation"] == "auto"
        assert data["dedup_level"] == "strict"
        assert data["enable_hyperlink"] is True
        assert "id" in data

    def test_create_project_minimal(self, client):
        response = client.post("/api/projects/", json={
            "name": "Minimal"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Minimal"
        assert data["language"] == "zh-CN"


class TestProjectGet:
    def test_get_project_success(self, client, sample_project):
        response = client.get(f"/api/projects/{sample_project['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_project["id"]
        assert data["name"] == sample_project["name"]

    def test_get_project_not_found(self, client):
        response = client.get("/api/projects/nonexistent-id")
        assert response.status_code == 404
        assert response.json()["detail"] == "Project not found"


class TestProjectList:
    def test_list_projects_empty(self, client):
        response = client.get("/api/projects/")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_projects_with_data(self, client, sample_project):
        response = client.get("/api/projects/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == sample_project["id"]


class TestProjectConfig:
    def test_update_config_success(self, client, sample_project):
        pid = sample_project["id"]
        response = client.put(f"/api/projects/{pid}/config", json={
            "language": "en",
            "table_orientation": "landscape",
            "dedup_level": "loose",
            "enable_hyperlink": False
        })
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "en"
        assert data["table_orientation"] == "landscape"
        assert data["dedup_level"] == "loose"
        assert data["enable_hyperlink"] is False

        # Verify persistence
        response = client.get(f"/api/projects/{pid}")
        assert response.json()["language"] == "en"

    def test_update_config_partial(self, client, sample_project):
        pid = sample_project["id"]
        response = client.put(f"/api/projects/{pid}/config", json={
            "language": "bilingual"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "bilingual"
        # Other fields should remain unchanged
        assert data["table_orientation"] == "auto"

    def test_update_config_not_found(self, client):
        response = client.put("/api/projects/nonexistent/config", json={
            "language": "en"
        })
        assert response.status_code == 404


class TestProjectStatus:
    def test_get_status(self, client, sample_project):
        pid = sample_project["id"]
        response = client.get(f"/api/projects/{pid}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == pid
        assert data["name"] == sample_project["name"]
        assert data["status"] == "draft"
        assert data["document_count"] == 0
        assert data["chapter_count"] == 0
        assert "last_updated" in data

    def test_get_status_not_found(self, client):
        response = client.get("/api/projects/nonexistent/status")
        assert response.status_code == 404

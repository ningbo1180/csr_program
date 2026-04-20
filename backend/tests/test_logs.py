"""
Tests for Action Log API routes
"""
import pytest


class TestLogsList:
    def test_logs_empty(self, client, sample_project):
        response = client.get(f"/api/logs/{sample_project['id']}")
        assert response.status_code == 200
        assert response.json() == []

    def test_logs_after_chapter_create(self, client, sample_project):
        # Creating a chapter triggers an action log
        client.post(f"/api/chapters/{sample_project['id']}", json={
            "title": "Test Chapter", "number": "1"
        })

        response = client.get(f"/api/logs/{sample_project['id']}")
        assert response.status_code == 200
        logs = response.json()
        assert len(logs) >= 1
        assert logs[0]["action_type"] == "add_chapter"
        assert "Test Chapter" in logs[0]["description"]
        assert logs[0]["project_id"] == sample_project["id"]

    def test_logs_pagination(self, client, sample_project):
        # Create multiple chapters to generate logs
        for i in range(5):
            client.post(f"/api/chapters/{sample_project['id']}", json={
                "title": f"Chapter {i}", "number": str(i)
            })

        response = client.get(f"/api/logs/{sample_project['id']}?limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_logs_filter_by_type(self, client, sample_project):
        client.post(f"/api/chapters/{sample_project['id']}", json={
            "title": "Test", "number": "1"
        })

        response = client.get(f"/api/logs/{sample_project['id']}?action_type=add_chapter")
        assert response.status_code == 200
        logs = response.json()
        assert all(log["action_type"] == "add_chapter" for log in logs)

    def test_logs_filter_invalid_type(self, client, sample_project):
        response = client.get(f"/api/logs/{sample_project['id']}?action_type=invalid_type")
        assert response.status_code == 400


class TestLogsSummary:
    def test_logs_summary(self, client, sample_project):
        # Create some activity
        client.post(f"/api/chapters/{sample_project['id']}", json={
            "title": "Ch1", "number": "1"
        })
        client.post(f"/api/chapters/{sample_project['id']}", json={
            "title": "Ch2", "number": "2"
        })

        response = client.get(f"/api/logs/{sample_project['id']}/summary?days=7")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == sample_project["id"]
        assert data["period_days"] == 7
        assert data["total_actions"] >= 2
        assert "add_chapter" in data["actions_by_type"]


class TestLogsSearch:
    def test_search_logs(self, client, sample_project):
        client.post(f"/api/chapters/{sample_project['id']}", json={
            "title": "UniqueSearchTitle", "number": "1"
        })

        response = client.get(f"/api/logs/{sample_project['id']}/search?keyword=UniqueSearchTitle")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == sample_project["id"]
        assert data["keyword"] == "UniqueSearchTitle"
        assert len(data["results"]) >= 1

    def test_search_no_results(self, client, sample_project):
        response = client.get(f"/api/logs/{sample_project['id']}/search?keyword=nonexistentxyz")
        assert response.status_code == 200
        assert len(response.json()["results"]) == 0

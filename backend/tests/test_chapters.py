"""
Tests for Chapter API routes
"""
import pytest


class TestChapterCreate:
    def test_create_chapter_success(self, client, sample_project):
        response = client.post(f"/api/chapters/{sample_project['id']}", json={
            "title": "试验目的",
            "number": "8",
            "content": "",
            "order": 1
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "试验目的"
        assert data["number"] == "8"
        assert data["project_id"] == sample_project["id"]
        assert data["parent_id"] is None

    def test_create_chapter_not_found_project(self, client):
        response = client.post("/api/chapters/nonexistent", json={
            "title": "Test",
            "number": "1"
        })
        assert response.status_code == 404

    def test_create_chapter_with_parent(self, client, sample_project, sample_chapter):
        response = client.post(f"/api/chapters/{sample_project['id']}", json={
            "title": "研究设计",
            "number": "10.2.1",
            "parent_id": sample_chapter["id"],
            "order": 0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["parent_id"] == sample_chapter["id"]

    def test_create_chapter_invalid_parent(self, client, sample_project):
        response = client.post(f"/api/chapters/{sample_project['id']}", json={
            "title": "Test",
            "number": "1",
            "parent_id": "nonexistent"
        })
        assert response.status_code == 400


class TestChapterGet:
    def test_get_chapter_success(self, client, sample_project, sample_chapter):
        response = client.get(f"/api/chapters/{sample_project['id']}/{sample_chapter['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_chapter["id"]
        assert data["title"] == sample_chapter["title"]

    def test_get_chapter_not_found(self, client, sample_project):
        response = client.get(f"/api/chapters/{sample_project['id']}/nonexistent")
        assert response.status_code == 404


class TestChapterTree:
    def test_tree_empty(self, client, sample_project):
        response = client.get(f"/api/chapters/{sample_project['id']}/tree")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == sample_project["id"]
        assert data["tree"] == []

    def test_tree_with_chapters(self, client, sample_project):
        # Create parent
        r1 = client.post(f"/api/chapters/{sample_project['id']}", json={
            "title": "研究计划", "number": "10", "order": 0
        })
        parent = r1.json()

        # Create child
        r2 = client.post(f"/api/chapters/{sample_project['id']}", json={
            "title": "研究设计讨论", "number": "10.2", "parent_id": parent["id"], "order": 0
        })
        child = r2.json()

        # Create grandchild
        r3 = client.post(f"/api/chapters/{sample_project['id']}", json={
            "title": "研究设计", "number": "10.2.1", "parent_id": child["id"], "order": 0
        })

        response = client.get(f"/api/chapters/{sample_project['id']}/tree")
        assert response.status_code == 200
        tree = response.json()["tree"]
        assert len(tree) == 1
        assert tree[0]["number"] == "10"
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["number"] == "10.2"
        assert len(tree[0]["children"][0]["children"]) == 1
        assert tree[0]["children"][0]["children"][0]["number"] == "10.2.1"

    def test_tree_not_found_project(self, client):
        response = client.get("/api/chapters/nonexistent/tree")
        assert response.status_code == 404


class TestChapterUpdate:
    def test_update_title(self, client, sample_project, sample_chapter):
        response = client.put(f"/api/chapters/{sample_project['id']}/{sample_chapter['id']}", json={
            "title": "Updated Title"
        })
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    def test_update_content(self, client, sample_project, sample_chapter):
        response = client.put(f"/api/chapters/{sample_project['id']}/{sample_chapter['id']}", json={
            "content": "<p>New content</p>"
        })
        assert response.status_code == 200
        assert response.json()["content"] == "<p>New content</p>"

    def test_update_not_found(self, client, sample_project):
        response = client.put(f"/api/chapters/{sample_project['id']}/nonexistent", json={
            "title": "X"
        })
        assert response.status_code == 404


class TestChapterDelete:
    def test_delete_chapter(self, client, sample_project, sample_chapter):
        response = client.delete(f"/api/chapters/{sample_project['id']}/{sample_chapter['id']}")
        assert response.status_code == 200
        assert response.json()["message"] == "Chapter deleted"

        # Verify deleted
        response = client.get(f"/api/chapters/{sample_project['id']}/{sample_chapter['id']}")
        assert response.status_code == 404

    def test_delete_recursive(self, client, sample_project):
        parent = client.post(f"/api/chapters/{sample_project['id']}", json={
            "title": "Parent", "number": "1"
        }).json()
        child = client.post(f"/api/chapters/{sample_project['id']}", json={
            "title": "Child", "number": "1.1", "parent_id": parent["id"]
        }).json()

        response = client.delete(f"/api/chapters/{sample_project['id']}/{parent['id']}")
        assert response.status_code == 200

        # Both parent and child should be gone
        assert client.get(f"/api/chapters/{sample_project['id']}/{parent['id']}").status_code == 404
        assert client.get(f"/api/chapters/{sample_project['id']}/{child['id']}").status_code == 404


class TestChapterGenerate:
    def test_generate_content(self, client, sample_project, sample_chapter):
        response = client.post(f"/api/chapters/{sample_project['id']}/{sample_chapter['id']}/generate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert len(data["content"]) > 100
        assert "<h3>" in data["content"]

        # Verify content persisted
        response = client.get(f"/api/chapters/{sample_project['id']}/{sample_chapter['id']}")
        assert response.json()["content"] == data["content"]

    def test_generate_not_found(self, client, sample_project):
        response = client.post(f"/api/chapters/{sample_project['id']}/nonexistent/generate")
        assert response.status_code == 404


class TestListChapters:
    def test_list_chapters(self, client, sample_project, sample_chapter):
        response = client.get(f"/api/chapters/{sample_project['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == sample_project["id"]
        assert len(data["chapters"]) == 1
        assert data["chapters"][0]["number"] == sample_chapter["number"]

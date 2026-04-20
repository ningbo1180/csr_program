"""
Integration tests for CSR GenAI full workflow
"""
import pytest
from io import BytesIO


@pytest.fixture
def full_project(client):
    """Setup a project with documents and chapters for integration tests"""
    # 1. Create project
    project = client.post("/api/projects/", json={
        "name": "Integration-Test-Project",
        "description": "Full workflow test",
        "language": "zh-CN"
    }).json()

    # 2. Update config
    client.put(f"/api/projects/{project['id']}/config", json={
        "language": "bilingual",
        "table_orientation": "landscape",
        "dedup_level": "standard"
    })

    return project


class TestFullWorkflow:
    def test_project_lifecycle(self, client, full_project):
        """Test: create project → verify config → check status"""
        pid = full_project["id"]

        # Verify config persisted
        project = client.get(f"/api/projects/{pid}").json()
        assert project["language"] == "bilingual"
        assert project["table_orientation"] == "landscape"
        assert project["dedup_level"] == "standard"

        # Verify initial status
        status = client.get(f"/api/projects/{pid}/status").json()
        assert status["document_count"] == 0
        assert status["chapter_count"] == 0

    def test_chapter_workflow(self, client, full_project):
        """Test: create chapters → build tree → update content → generate AI"""
        pid = full_project["id"]

        # Create chapter hierarchy
        sec10 = client.post(f"/api/chapters/{pid}", json={
            "title": "研究计划", "number": "10", "order": 0
        }).json()

        sec10_2 = client.post(f"/api/chapters/{pid}", json={
            "title": "研究设计讨论", "number": "10.2", "parent_id": sec10["id"], "order": 0
        }).json()

        sec10_2_1 = client.post(f"/api/chapters/{pid}", json={
            "title": "研究设计", "number": "10.2.1", "parent_id": sec10_2["id"], "order": 0
        }).json()

        # Verify tree structure
        tree = client.get(f"/api/chapters/{pid}/tree").json()["tree"]
        assert len(tree) == 1
        assert tree[0]["number"] == "10"
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["number"] == "10.2"
        assert len(tree[0]["children"][0]["children"]) == 1
        assert tree[0]["children"][0]["children"][0]["number"] == "10.2.1"

        # Update content
        client.put(f"/api/chapters/{pid}/{sec10_2['id']}", json={
            "content": "<p>Initial manual content</p>"
        })

        # AI generate
        result = client.post(f"/api/chapters/{pid}/{sec10_2['id']}/generate").json()
        assert result["status"] == "completed"
        assert len(result["content"]) > 100

        # Verify content persisted
        chapter = client.get(f"/api/chapters/{pid}/{sec10_2['id']}").json()
        assert "<h3>" in chapter["content"]

        # Verify status updated
        status = client.get(f"/api/projects/{pid}/status").json()
        assert status["chapter_count"] == 3

    def test_document_upload_workflow(self, client, full_project, tmp_path):
        """Test: upload document → list → verify type detection"""
        pid = full_project["id"]

        files = [
            ("Protocol_v2.3.pdf", b"%PDF test", "application/pdf"),
            ("SAP_Final.docx", b"PK fake docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            ("TFL_Table14.xlsx", b"PK fake xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ]

        for name, content, ctype in files:
            test_file = tmp_path / name
            test_file.write_bytes(content)
            with open(test_file, "rb") as f:
                response = client.post(
                    f"/api/documents/{pid}/upload",
                    files={"file": (name, f, ctype)}
                )
                assert response.status_code == 200

        # List documents
        docs = client.get(f"/api/documents/{pid}").json()
        assert len(docs) == 3

        # Verify type detection
        types = {d["doc_type"] for d in docs}
        assert "protocol" in types
        assert "sap" in types
        assert "tfl" in types

        # Verify status
        status = client.get(f"/api/projects/{pid}/status").json()
        assert status["document_count"] == 3

    def test_audit_log_workflow(self, client, full_project):
        """Test: all actions produce correct audit logs"""
        pid = full_project["id"]

        # Create chapter
        ch = client.post(f"/api/chapters/{pid}", json={
            "title": "AuditTest", "number": "99"
        }).json()

        # Update chapter
        client.put(f"/api/chapters/{pid}/{ch['id']}", json={
            "title": "AuditTestUpdated"
        })

        # Generate AI content
        client.post(f"/api/chapters/{pid}/{ch['id']}/generate")

        # Check logs
        logs = client.get(f"/api/logs/{pid}").json()
        assert len(logs) >= 3

        action_types = {log["action_type"] for log in logs}
        assert "add_chapter" in action_types
        assert "edit_chapter" in action_types
        assert "ai_generate" in action_types

        # Check summary
        summary = client.get(f"/api/logs/{pid}/summary?days=7").json()
        assert summary["total_actions"] >= 3
        assert "add_chapter" in summary["actions_by_type"]
        assert "edit_chapter" in summary["actions_by_type"]
        assert "ai_generate" in summary["actions_by_type"]

    def test_delete_cascade(self, client, full_project):
        """Test: delete parent chapter removes children and logs are preserved"""
        pid = full_project["id"]

        parent = client.post(f"/api/chapters/{pid}", json={
            "title": "Parent", "number": "1"
        }).json()

        child = client.post(f"/api/chapters/{pid}", json={
            "title": "Child", "number": "1.1", "parent_id": parent["id"]
        }).json()

        # Delete parent
        client.delete(f"/api/chapters/{pid}/{parent['id']}")

        # Verify both deleted
        assert client.get(f"/api/chapters/{pid}/{parent['id']}").status_code == 404
        assert client.get(f"/api/chapters/{pid}/{child['id']}").status_code == 404

        # Verify delete log exists
        logs = client.get(f"/api/logs/{pid}").json()
        delete_logs = [l for l in logs if l["action_type"] == "delete_chapter"]
        assert len(delete_logs) >= 1

    def test_end_to_end_csr_build(self, client, full_project, tmp_path):
        """Complete CSR build simulation: project → docs → structure → AI → status"""
        pid = full_project["id"]

        # Upload a document
        test_file = tmp_path / "Protocol.pdf"
        test_file.write_bytes(b"%PDF test")
        with open(test_file, "rb") as f:
            client.post(
                f"/api/documents/{pid}/upload",
                files={"file": ("Protocol.pdf", f, "application/pdf")}
            )

        # Build structure
        chapters = []
        for num, title in [("8", "试验目的"), ("10", "研究计划"), ("10.2", "研究设计讨论")]:
            parent_id = chapters[-1]["id"] if chapters and num.startswith(chapters[-1]["number"]) else None
            ch = client.post(f"/api/chapters/{pid}", json={
                "title": title, "number": num,
                "parent_id": parent_id, "order": 0
            }).json()
            chapters.append(ch)

        # AI generate for 10.2
        client.post(f"/api/chapters/{pid}/{chapters[2]['id']}/generate")

        # Final status check
        status = client.get(f"/api/projects/{pid}/status").json()
        assert status["document_count"] == 1
        assert status["chapter_count"] == 3

        # Final tree check
        tree = client.get(f"/api/chapters/{pid}/tree").json()["tree"]
        assert len(tree) == 2  # 8 and 10 at root level

        # Verify AI content
        ch = client.get(f"/api/chapters/{pid}/{chapters[2]['id']}").json()
        assert len(ch["content"]) > 100

        # Verify logs
        logs = client.get(f"/api/logs/{pid}").json()
        assert len(logs) >= 5  # upload + 3 chapter creates + ai_generate

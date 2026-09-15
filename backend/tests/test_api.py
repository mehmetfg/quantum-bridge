"""API ve boru hattı testleri: uçtan uca akış çalışıyor mu?"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.core.job_store import job_store
from app.core.models import STAGE_ORDER
from app.main import app


@pytest.fixture
def client():
    job_store.clear()
    with TestClient(app) as test_client:
        yield test_client
    job_store.clear()


class TestSystemEndpoints:
    def test_health(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_auth_status_reports_direct_entry(self, client):
        data = client.get("/api/auth/status").json()
        assert data["login_required"] is False
        assert data["user"]["id"] == "demo"

    def test_stages_are_listed_in_order(self, client):
        stages = client.get("/api/stages").json()
        assert [s["stage"] for s in stages] == [s.value for s in STAGE_ORDER]
        for stage in stages:
            assert stage["title"] and stage["summary"] and stage["why"]

    def test_backends_include_unavailable_future_targets(self, client):
        data = client.get("/api/backends").json()
        ids = {b["id"] for b in data["backends"]}
        assert data["default"] == "local-statevector"
        assert {"local-statevector", "qiskit-aer", "ibm-runtime"} <= ids
        available = [b for b in data["backends"] if b["available"]]
        assert len(available) == 1


class TestProblemEndpoints:
    def test_list_problems(self, client):
        problems = client.get("/api/problems").json()
        assert len(problems) == 5
        assert all(p["input_schema"] for p in problems)

    def test_get_single_problem(self, client):
        problem = client.get("/api/problems/grover-search").json()
        assert problem["id"] == "grover-search"
        assert problem["concepts"]

    def test_unknown_problem_returns_404(self, client):
        assert client.get("/api/problems/yok").status_code == 404


class TestJobPipeline:
    def test_full_pipeline_records_all_six_stages(self, client):
        response = client.post(
            "/api/jobs",
            json={
                "problem_id": "bernstein-vazirani",
                "input": {"secret": "1011"},
                "seed": 42,
            },
        )
        assert response.status_code == 200
        job = response.json()
        assert job["status"] == "COMPLETED"
        assert [e["stage"] for e in job["events"]] == [s.value for s in STAGE_ORDER]
        assert job["result"]["answer"] == "1011"
        assert job["result"]["verified"] is True

    def test_job_carries_circuit_and_qasm(self, client):
        job = client.post(
            "/api/jobs",
            json={"problem_id": "bell-state", "input": {"parties": 2}, "seed": 1},
        ).json()
        assert job["circuit"]["n_qubits"] == 2
        assert "OPENQASM 3.0;" in job["qasm"]
        assert job["circuit"]["metrics"]["depth"] >= 2

    def test_routing_decision_is_explained(self, client):
        job = client.post(
            "/api/jobs",
            json={"problem_id": "deutsch-jozsa", "input": {"n_bits": 3}, "seed": 7},
        ).json()
        assert job["routing"]["n_qubits"] == 4
        assert len(job["routing"]["reasoning"]) >= 3
        assert job["routing"]["rejected_alternatives"]

    def test_every_stage_explains_why_it_exists(self, client):
        job = client.post(
            "/api/jobs", json={"problem_id": "random-bits", "input": {}, "seed": 3}
        ).json()
        for event in job["events"]:
            assert event["why"], f"{event['stage']} aşamasının gerekçesi boş"
            assert event["details"], f"{event['stage']} aşamasının ayrıntısı boş"

    def test_grover_end_to_end(self, client):
        job = client.post(
            "/api/jobs",
            json={
                "problem_id": "grover-search",
                "input": {"items": ["elma", "armut", "kiraz", "muz"], "target": "kiraz"},
                "seed": 11,
            },
        ).json()
        assert job["result"]["answer"] == "kiraz"
        assert job["result"]["verified"] is True

    def test_noise_is_reflected_in_result(self, client):
        job = client.post(
            "/api/jobs",
            json={
                "problem_id": "bernstein-vazirani",
                "input": {"secret": "1101"},
                "noise_level": "high",
                "seed": 5,
            },
        ).json()
        assert job["status"] == "COMPLETED"
        assert job["raw_result"]["meta"]["noise"]["applied"] is True
        assert job["result"]["confidence"] < 1.0

    def test_invalid_input_fails_at_intake_stage(self, client):
        job = client.post(
            "/api/jobs",
            json={"problem_id": "bernstein-vazirani", "input": {"secret": "abc"}},
        ).json()
        assert job["status"] == "FAILED"
        assert job["events"][0]["stage"] == "INTAKE"
        assert job["events"][0]["status"] == "error"
        assert "geçersiz" in job["error"].lower()

    def test_unknown_problem_fails_cleanly(self, client):
        job = client.post("/api/jobs", json={"problem_id": "yok", "input": {}}).json()
        assert job["status"] == "FAILED"
        assert "Bilinmeyen problem" in job["error"]

    def test_unavailable_backend_is_rejected_with_guidance(self, client):
        job = client.post(
            "/api/jobs",
            json={"problem_id": "bell-state", "input": {}, "backend_id": "ibm-runtime"},
        ).json()
        assert job["status"] == "FAILED"
        assert "henüz baglanmadi" in job["error"] or "henüz bağlanmadı" in job["error"]

    def test_seed_makes_whole_pipeline_repeatable(self, client):
        payload = {"problem_id": "random-bits", "input": {"bit_count": 3}, "seed": 99}
        first = client.post("/api/jobs", json=payload).json()
        second = client.post("/api/jobs", json=payload).json()
        assert first["raw_result"]["counts"] == second["raw_result"]["counts"]


class TestJobRetrieval:
    def test_get_job_by_id(self, client):
        created = client.post(
            "/api/jobs", json={"problem_id": "bell-state", "input": {}, "seed": 1}
        ).json()
        fetched = client.get(f"/api/jobs/{created['id']}").json()
        assert fetched["id"] == created["id"]
        assert len(fetched["events"]) == 6

    def test_missing_job_returns_404(self, client):
        assert client.get("/api/jobs/yokboyle").status_code == 404

    def test_job_list_is_newest_first(self, client):
        client.post("/api/jobs", json={"problem_id": "bell-state", "input": {}, "seed": 1})
        client.post("/api/jobs", json={"problem_id": "random-bits", "input": {}, "seed": 1})
        jobs = client.get("/api/jobs").json()
        assert len(jobs) == 2
        assert jobs[0]["problem_id"] == "random-bits"
        assert jobs[0]["answer_label"]


class TestEventStream:
    def test_stream_replays_completed_job(self, client):
        created = client.post(
            "/api/jobs",
            json={"problem_id": "bell-state", "input": {}, "seed": 4},
        ).json()

        with client.stream("GET", f"/api/jobs/{created['id']}/events") as response:
            assert response.status_code == 200
            payloads = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    payloads.append(json.loads(line[6:]))
                    if payloads[-1]["type"] == "done":
                        break

        stages = [p["event"]["stage"] for p in payloads if p["type"] == "stage"]
        assert stages == [s.value for s in STAGE_ORDER]
        assert payloads[-1]["job"]["status"] == "COMPLETED"

    def test_stream_for_missing_job_returns_404(self, client):
        assert client.get("/api/jobs/yok/events").status_code == 404

    def test_background_mode_returns_immediately(self, client):
        response = client.post(
            "/api/jobs?stream=true",
            json={"problem_id": "bell-state", "input": {}, "seed": 2},
        )
        assert response.status_code == 200
        job = response.json()
        assert job["status"] in ("QUEUED", "RUNNING", "COMPLETED")

        with client.stream("GET", f"/api/jobs/{job['id']}/events") as stream:
            for line in stream.iter_lines():
                if line.startswith("data: ") and json.loads(line[6:])["type"] == "done":
                    break

        final = client.get(f"/api/jobs/{job['id']}").json()
        assert final["status"] == "COMPLETED"

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional

import pytest

from tonic_fabricate import AgentEvalsClient, AgentEvalsError


class ExpectedRequest:
    def __init__(
        self,
        method: str,
        path: str,
        *,
        response_json: Optional[Any] = None,
        response_body: bytes = b"",
        status: int = 200,
        response_content_type: str = "application/json",
    ):
        self.method = method
        self.path = path
        self.response_json = response_json
        self.response_body = response_body
        self.status = status
        self.response_content_type = response_content_type


class StubServer(ThreadingHTTPServer):
    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), StubHandler)
        self.expected: List[ExpectedRequest] = []
        self.requests: List[Dict[str, Any]] = []

    @property
    def url(self) -> str:
        host, port = self.server_address
        return f"http://{host}:{port}"

    def enqueue(
        self,
        method: str,
        path: str,
        *,
        response_json: Optional[Any] = None,
        response_body: bytes = b"",
        status: int = 200,
        response_content_type: str = "application/json",
    ) -> None:
        self.expected.append(
            ExpectedRequest(
                method,
                path,
                response_json=response_json,
                response_body=response_body,
                status=status,
                response_content_type=response_content_type,
            )
        )


class StubHandler(BaseHTTPRequestHandler):
    server: StubServer

    def do_GET(self) -> None:
        self._handle()

    def do_POST(self) -> None:
        self._handle()

    def do_PATCH(self) -> None:
        self._handle()

    def do_DELETE(self) -> None:
        self._handle()

    def do_PUT(self) -> None:
        self._handle()

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _handle(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        self.server.requests.append(
            {
                "method": self.command,
                "path": self.path,
                "headers": dict(self.headers),
                "body": body,
            }
        )

        if not self.server.expected:
            self.send_error(500, "Unexpected request")
            return

        expected = self.server.expected.pop(0)
        if self.command != expected.method or self.path != expected.path:
            self.send_error(
                500,
                f"Expected {expected.method} {expected.path}; "
                f"got {self.command} {self.path}",
            )
            return

        if expected.response_json is not None:
            response_body = json.dumps(expected.response_json).encode("utf-8")
        else:
            response_body = expected.response_body

        self.send_response(expected.status)
        self.send_header("Content-Type", expected.response_content_type)
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)


@pytest.fixture
def stub_server() -> Any:
    server = StubServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
        assert not server.expected
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


@pytest.fixture
def client(stub_server: StubServer) -> AgentEvalsClient:
    return AgentEvalsClient(
        api_key="test-key", api_url=f"{stub_server.url}/api/v1///"
    )


def request_json(request: Dict[str, Any]) -> Any:
    return json.loads(request["body"].decode("utf-8"))


def test_report_only_payloads(
    client: AgentEvalsClient, stub_server: StubServer
) -> None:
    stub_server.enqueue(
        "POST",
        "/api/v1/projects/project/runs",
        response_json={"id": "run", "status": "in_progress"},
        status=201,
    )
    stub_server.enqueue(
        "POST",
        "/api/v1/runs/run/trials",
        response_json={"id": "trial", "status": "completed"},
        status=202,
    )

    client.create_run("project", {"suite_name": "Local suite", "model": "gpt-x"})
    client.report_trial(
        "run",
        {
            "task": {"key": "users", "input": "Generate users", "tags": ["users"]},
            "grader_definitions": [
                {
                    "name": "quality",
                    "prompt": "Check the output.",
                    "tags": ["users"],
                }
            ],
            "transcript": {"messages": []},
            "cache_read_tokens": 10,
            "cache_write_5m_tokens": 20,
            "cache_write_1h_tokens": 30,
            "grade": True,
        },
    )

    assert request_json(stub_server.requests[0]) == {
        "suite_name": "Local suite",
        "model": "gpt-x",
    }
    assert request_json(stub_server.requests[1])["task"]["key"] == "users"
    assert request_json(stub_server.requests[1])["grader_definitions"][0][
        "prompt"
    ] == "Check the output."
    assert request_json(stub_server.requests[1])["cache_read_tokens"] == 10
    assert request_json(stub_server.requests[1])["cache_write_5m_tokens"] == 20
    assert request_json(stub_server.requests[1])["cache_write_1h_tokens"] == 30


def test_constructor_uses_environment_and_normalizes_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FABRICATE_API_KEY", "env-key")
    monkeypatch.setenv("FABRICATE_API_URL", "https://example.test/api/v1///")

    client = AgentEvalsClient()

    assert client.api_key == "env-key"
    assert client.api_url == "https://example.test/api/v1"


def test_constructor_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FABRICATE_API_KEY", raising=False)

    with pytest.raises(ValueError, match="api_key is required"):
        AgentEvalsClient()


def test_project_suite_and_task_methods(
    client: AgentEvalsClient, stub_server: StubServer
) -> None:
    stub_server.enqueue(
        "GET", "/api/v1/workspaces/My%20Workspace/projects", response_json=[]
    )
    stub_server.enqueue(
        "POST",
        "/api/v1/workspaces/My%20Workspace/projects",
        response_json={"id": "project-1"},
    )
    stub_server.enqueue("GET", "/api/v1/projects/project-1/suites", response_json=[])
    stub_server.enqueue(
        "POST",
        "/api/v1/projects/project-1/suites",
        response_json={"id": "suite-1"},
    )
    stub_server.enqueue("GET", "/api/v1/suites/suite-1/tasks", response_json=[])
    stub_server.enqueue(
        "POST",
        "/api/v1/suites/suite-1/tasks",
        response_json={"id": "task-1"},
    )

    assert client.list_projects("My Workspace") == []
    assert (
        client.find_or_create_project("My Workspace", {"name": "Agent project"})["id"]
        == "project-1"
    )
    assert client.list_suites("project-1") == []
    assert (
        client.find_or_create_suite("project-1", {"name": "Suite", "tags": ["smoke"]})[
            "id"
        ]
        == "suite-1"
    )
    assert client.list_tasks("suite-1") == []
    assert (
        client.upsert_task("suite-1", {"key": "task", "input": "Do the task"})["id"]
        == "task-1"
    )

    assert stub_server.requests[0]["headers"]["Authorization"] == "Bearer test-key"
    assert request_json(stub_server.requests[1]) == {"name": "Agent project"}
    assert request_json(stub_server.requests[3]) == {
        "name": "Suite",
        "tags": ["smoke"],
    }
    assert request_json(stub_server.requests[5]) == {
        "key": "task",
        "input": "Do the task",
    }


def test_find_suite_matches_id_or_case_insensitive_name_and_version(
    client: AgentEvalsClient, stub_server: StubServer
) -> None:
    suites = [
        {"id": "one", "suite_id": "p", "name": "Regression", "version": 1},
        {"id": "two", "suite_id": "p", "name": "Regression", "version": 2},
    ]
    for _ in range(3):
        stub_server.enqueue(
            "GET", "/api/v1/projects/project/suites", response_json=suites
        )

    assert client.find_suite("project", id="two") == suites[1]
    # Without a version selector, the highest-numbered matching version wins.
    assert client.find_suite("project", name="regression") == suites[1]
    assert (
        client.find_suite("project", name="REGRESSION", version=1) == suites[0]
    )


def test_create_suite_version_uses_the_source_version_endpoint(
    client: AgentEvalsClient, stub_server: StubServer
) -> None:
    stub_server.enqueue(
        "POST",
        "/api/v1/suites/source-version/versions",
        response_json={
            "id": "next-version",
            "suite_id": "parent-suite",
            "name": "Regression",
            "version": 2,
        },
        status=201,
    )

    suite = client.create_suite_version("source-version")

    assert suite["id"] == "next-version"
    assert suite["version"] == 2
    assert stub_server.requests[0]["headers"]["Authorization"] == "Bearer test-key"
    assert stub_server.requests[0]["body"] == b""


def test_fixture_methods_and_database_download(
    client: AgentEvalsClient, stub_server: StubServer
) -> None:
    stub_server.enqueue("GET", "/api/v1/projects/project/fixtures", response_json=[])
    stub_server.enqueue(
        "POST",
        "/api/v1/projects/project/fixtures",
        response_json={"id": "fixture"},
    )
    stub_server.enqueue(
        "GET", "/api/v1/fixtures/fixture", response_json={"id": "fixture"}
    )
    stub_server.enqueue(
        "PATCH",
        "/api/v1/fixtures/fixture",
        response_json={"id": "fixture", "name": "Updated"},
    )
    stub_server.enqueue(
        "GET",
        "/api/v1/fixtures/fixture/databases/database",
        response_body=b"SQLite format 3\x00",
        response_content_type="application/vnd.sqlite3",
    )
    stub_server.enqueue("DELETE", "/api/v1/fixtures/fixture", status=204)

    assert client.list_fixtures("project") == []
    assert (
        client.find_or_create_fixture("project", {"name": "Fixture", "entries": []})[
            "id"
        ]
        == "fixture"
    )
    assert client.get_fixture("fixture")["id"] == "fixture"
    assert client.update_fixture("fixture", {"name": "Updated"})["name"] == "Updated"
    assert client.download_fixture_database("fixture", "database").startswith(b"SQLite")
    assert client.delete_fixture("fixture") is None
    assert stub_server.requests[4]["headers"]["Accept"] == "application/vnd.sqlite3"


def test_grader_run_and_trial_methods(
    client: AgentEvalsClient, stub_server: StubServer
) -> None:
    stub_server.enqueue(
        "GET", "/api/v1/projects/project/grader_definitions", response_json=[]
    )
    stub_server.enqueue(
        "POST",
        "/api/v1/projects/project/grader_definitions",
        response_json={"id": "grader"},
    )
    stub_server.enqueue(
        "GET",
        "/api/v1/projects/project/runs?branch=feature%2Fagent",
        response_json=[],
    )
    stub_server.enqueue(
        "POST",
        "/api/v1/projects/project/runs",
        response_json={"id": "run"},
    )
    stub_server.enqueue(
        "GET",
        "/api/v1/runs/run",
        response_json={"id": "run", "trials": []},
    )
    stub_server.enqueue("PATCH", "/api/v1/runs/run", response_json={"id": "run"})
    stub_server.enqueue(
        "POST",
        "/api/v1/runs/run/trials",
        response_json={"id": "trial", "task_key": "task"},
        status=202,
    )
    stub_server.enqueue(
        "GET",
        "/api/v1/trials/trial",
        response_json={"id": "trial", "task_key": "task"},
    )

    assert client.list_grader_definitions("project") == []
    assert (
        client.find_or_create_grader_definition(
            "project", {"name": "Judge", "kind": "llm_judge"}
        )["id"]
        == "grader"
    )
    assert client.list_runs("project", branch="feature/agent") == []
    assert client.create_run("project", {"suite_id": "suite"})["id"] == "run"
    assert client.get_run("run")["trials"] == []
    assert client.update_run("run", {"status": "completed"})["id"] == "run"
    assert (
        client.report_trial(
            "run",
            {
                "task_key": "task",
                "transcript": {
                    "messages": [
                        {
                            "name": "agent",
                            "attributes": {"openinference.span.kind": "AGENT"},
                        }
                    ]
                },
                "grade": True,
            },
        )["id"]
        == "trial"
    )
    assert client.get_trial("trial")["id"] == "trial"

    assert request_json(stub_server.requests[5]) == {"status": "completed"}
    assert request_json(stub_server.requests[6])["grade"] is True


def test_list_runs_omits_empty_branch(
    client: AgentEvalsClient, stub_server: StubServer
) -> None:
    stub_server.enqueue("GET", "/api/v1/projects/project/runs", response_json=[])

    assert client.list_runs("project", branch="") == []


def test_http_errors_include_request_context(
    client: AgentEvalsClient, stub_server: StubServer
) -> None:
    stub_server.enqueue(
        "GET",
        "/api/v1/trials/missing",
        response_json={"error": "Not found"},
        status=404,
    )

    with pytest.raises(AgentEvalsError) as raised:
        client.get_trial("missing")

    error = raised.value
    assert error.status == 404
    assert error.method == "GET"
    assert error.path == "/trials/missing"
    assert '"error": "Not found"' in error.body


def test_wait_for_grading_polls_until_completed(
    client: AgentEvalsClient, stub_server: StubServer
) -> None:
    stub_server.enqueue(
        "GET",
        "/api/v1/trials/trial",
        response_json={"id": "trial", "grading": {"status": "pending"}},
    )
    stub_server.enqueue(
        "GET",
        "/api/v1/trials/trial",
        response_json={"id": "trial", "grading": {"status": "in_progress"}},
    )
    stub_server.enqueue(
        "GET",
        "/api/v1/trials/trial",
        response_json={"id": "trial", "grading": {"status": "completed"}},
    )

    trial = client.wait_for_grading("trial", interval_seconds=0, timeout_seconds=1)

    assert trial["grading"]["status"] == "completed"


@pytest.mark.parametrize("grading", [None, {"status": "failed"}])
def test_wait_for_grading_returns_terminal_or_ungraded_trial(
    client: AgentEvalsClient,
    stub_server: StubServer,
    grading: Optional[Dict[str, str]],
) -> None:
    response = {"id": "trial"}
    if grading is not None:
        response["grading"] = grading
    stub_server.enqueue("GET", "/api/v1/trials/trial", response_json=response)

    assert (
        client.wait_for_grading("trial", interval_seconds=0, timeout_seconds=1)["id"]
        == "trial"
    )


def test_wait_for_grading_times_out(
    client: AgentEvalsClient, stub_server: StubServer
) -> None:
    stub_server.enqueue(
        "GET",
        "/api/v1/trials/trial",
        response_json={"id": "trial", "grading": {"status": "in_progress"}},
    )

    with pytest.raises(TimeoutError, match="Timed out after 0s"):
        client.wait_for_grading("trial", interval_seconds=0, timeout_seconds=0)


def test_wait_for_grading_can_be_cancelled(
    client: AgentEvalsClient, stub_server: StubServer
) -> None:
    stub_server.enqueue(
        "GET",
        "/api/v1/trials/trial",
        response_json={"id": "trial", "grading": {"status": "in_progress"}},
    )
    cancel_event = threading.Event()
    cancel_event.set()

    with pytest.raises(RuntimeError, match="Aborted"):
        client.wait_for_grading(
            "trial",
            interval_seconds=0,
            timeout_seconds=1,
            cancel_event=cancel_event,
        )


def test_upload_attachment_mints_and_puts_bytes(
    client: AgentEvalsClient, stub_server: StubServer
) -> None:
    upload_url = f"{stub_server.url}/api/v1/agent_evals/uploads/upload"
    stub_server.enqueue(
        "POST",
        "/api/v1/workspaces/My%20Workspace/agent_evals/uploads",
        response_json={
            "upload_id": "upload",
            "upload_url": upload_url,
            "method": "PUT",
            "max_bytes": 100,
            "expires_at": "later",
            "instructions": "PUT bytes",
        },
        status=201,
    )
    stub_server.enqueue(
        "PUT",
        "/api/v1/agent_evals/uploads/upload",
        response_json={"upload_id": "upload", "status": "uploaded"},
    )

    upload_id = client.upload_attachment(
        "My Workspace",
        filename="result.csv",
        content_type="text/csv",
        data=b"a,b\n1,2\n",
    )

    assert upload_id == "upload"
    assert request_json(stub_server.requests[0]) == {
        "filename": "result.csv",
        "content_type": "text/csv",
    }
    assert stub_server.requests[1]["body"] == b"a,b\n1,2\n"
    assert stub_server.requests[1]["headers"]["Content-Type"] == "text/csv"
    assert stub_server.requests[1]["headers"]["Authorization"] == "Bearer test-key"


def test_upload_errors_use_absolute_url(
    client: AgentEvalsClient, stub_server: StubServer
) -> None:
    upload_url = f"{stub_server.url}/upload"
    stub_server.enqueue(
        "PUT",
        "/upload",
        response_json={"error": "expired"},
        status=409,
    )

    with pytest.raises(AgentEvalsError) as raised:
        client.put_upload_bytes(upload_url, b"data")

    assert raised.value.method == "PUT"
    assert raised.value.path == upload_url

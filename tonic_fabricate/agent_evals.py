"""Framework-agnostic client for Fabricate's Agent Evals API."""

from __future__ import annotations

import os
import time
from threading import Event
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    TypedDict,
    Union,
    cast,
)
from urllib.parse import quote

import requests

DEFAULT_API_URL = "https://fabricate.tonic.ai/api/v1"
DEFAULT_GRADING_INTERVAL_SECONDS = 3.0
DEFAULT_GRADING_TIMEOUT_SECONDS = 120.0

AgentEvalsRunStatus = Literal["in_progress", "completed", "failed", "timed_out"]
AgentEvalsClientRunStatus = Literal["in_progress", "completed", "failed"]
AgentEvalsTrialStatus = Literal["completed", "failed", "error"]
AgentEvalsGraderKind = Literal["llm_judge", "script"]
AgentEvalsFixtureEntryType = Literal["database", "table", "workflow", "mock_api"]


class OpenInferenceSpan(TypedDict):
    """One flattened OpenInference span in a trial transcript."""

    name: str
    attributes: Dict[str, Any]


class AgentEvalsProject(TypedDict):
    id: str
    name: str
    description: Optional[str]
    workspace_id: str


class AgentEvalsFixtureEntryDiagnostic(TypedDict):
    code: str
    message: str


class AgentEvalsFixtureEntry(TypedDict):
    id: str
    key: str
    type: AgentEvalsFixtureEntryType
    value: Dict[str, Any]
    position: int
    resource: Optional[Dict[str, Any]]
    diagnostic: Optional[AgentEvalsFixtureEntryDiagnostic]


class _AgentEvalsFixtureVersionRequired(TypedDict):
    id: str
    project_id: str
    fixture_id: str
    name: str
    version: int
    description: Optional[str]
    entries: List[AgentEvalsFixtureEntry]


class AgentEvalsFixtureVersion(_AgentEvalsFixtureVersionRequired, total=False):
    created_at: str
    updated_at: str


AgentEvalsFixture = AgentEvalsFixtureVersion


class AgentEvalsSuite(TypedDict):
    """A suite version; ``id`` is its version UUID and ``suite_id`` is its stable suite UUID."""

    id: str
    project_id: str
    suite_id: str
    name: str
    version: int
    description: Optional[str]
    tags: List[str]
    task_count: int
    default_fixture_id: Optional[str]
    default_fixture: Optional[AgentEvalsFixture]


class AgentEvalsTask(TypedDict):
    """A task scoped to one suite version via ``suite_id`` (not the stable suite UUID)."""

    id: str
    suite_id: str
    key: str
    input: str
    expected_output: Optional[str]
    tags: List[str]
    input_token_limit: Optional[int]
    output_token_limit: Optional[int]
    fixture_id: Optional[str]
    effective_fixture: Optional[AgentEvalsFixture]


class AgentEvalsGraderVersion(TypedDict):
    id: str
    project_id: str
    grader_id: str
    name: str
    version: int
    description: Optional[str]
    kind: AgentEvalsGraderKind
    prompt: Optional[str]
    code: Optional[str]
    model: Optional[str]
    tags: List[str]


AgentEvalsGraderDefinition = AgentEvalsGraderVersion


class AgentEvalsRun(TypedDict):
    """A run whose ``suite_id`` is the suite version UUID, not the stable suite UUID."""

    id: str
    project_id: str
    run_number: int
    suite_id: Optional[str]
    suite_linked: bool
    suite_name: Optional[str]
    suite_version: Optional[int]
    git_branch: Optional[str]
    git_sha: Optional[str]
    git_repo_url: Optional[str]
    model: Optional[str]
    name: Optional[str]
    status: AgentEvalsRunStatus
    started_at: Optional[str]
    completed_at: Optional[str]
    last_client_update_at: str
    aggregate_metrics: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    fixture_overrides: Sequence["AgentEvalsFixtureVersionOverride"]
    grader_overrides: Sequence["AgentEvalsGraderVersionOverride"]
    created_at: str


class _AgentEvalsAssertionRequired(TypedDict):
    assertion_name: str
    passed: Optional[bool]
    score: Optional[float]
    reasoning: Optional[str]


class AgentEvalsAssertion(_AgentEvalsAssertionRequired, total=False):
    id: str


class _AgentEvalsGraderRequired(TypedDict):
    grader_name: str
    passed: Optional[bool]
    assertions: List[AgentEvalsAssertion]


class AgentEvalsGrader(_AgentEvalsGraderRequired, total=False):
    id: str


AgentEvalsGradingStatus = Literal["pending", "in_progress", "completed", "failed"]


class AgentEvalsGrading(TypedDict):
    id: str
    status: AgentEvalsGradingStatus
    graders_total: int
    graders_completed: int
    error: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]


class AgentEvalsAttachment(TypedDict):
    id: str
    filename: str
    content_type: Optional[str]
    byte_size: int


class AgentEvalsTrialSummary(TypedDict):
    id: str
    run_id: str
    task_id: Optional[str]
    task_linked: bool
    task_key: str
    task_name: Optional[str]
    trial_number: int
    status: str
    passed: Optional[bool]
    cost: Optional[float]
    latency_ms: Optional[int]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    cache_read_tokens: Optional[int]
    cached_tokens: Optional[int]
    cache_write_5m_tokens: Optional[int]
    cache_write_1h_tokens: Optional[int]


class AgentEvalsTranscript(TypedDict):
    id: str
    messages: List[OpenInferenceSpan]


class AgentEvalsTrial(AgentEvalsTrialSummary, total=False):
    task_input: str
    task_expected_output: Optional[str]
    task_tags: List[str]
    grader_definitions_snapshot: List[AgentEvalsGraderVersion]
    transcript: Optional[AgentEvalsTranscript]
    prompt_context: Any
    fixture: Optional[AgentEvalsFixture]
    attachments: List[AgentEvalsAttachment]
    graders: List[AgentEvalsGrader]
    grading: Optional[AgentEvalsGrading]


class AgentEvalsRunWithTrials(AgentEvalsRun):
    trials: List[AgentEvalsTrialSummary]


class AgentEvalsFixtureEntryInput(TypedDict):
    key: str
    type: AgentEvalsFixtureEntryType
    value: Dict[str, Any]


class _FindOrCreateProjectInputRequired(TypedDict):
    name: str


class FindOrCreateProjectInput(_FindOrCreateProjectInputRequired, total=False):
    description: str


class _FindOrCreateSuiteInputRequired(TypedDict):
    name: str


class FindOrCreateSuiteInput(_FindOrCreateSuiteInputRequired, total=False):
    description: str
    tags: Sequence[str]
    default_fixture_id: str


class _UpsertTaskInputRequired(TypedDict):
    key: str
    input: str


class UpsertTaskInput(_UpsertTaskInputRequired, total=False):
    expected_output: str
    tags: Sequence[str]
    fixture_id: str
    input_token_limit: int
    output_token_limit: int


class _FixtureInputRequired(TypedDict):
    name: str


class FixtureInput(_FixtureInputRequired, total=False):
    description: str
    entries: Sequence[AgentEvalsFixtureEntryInput]


class AgentEvalsFixtureVersionOverride(TypedDict):
    """Select a Fixture Version for one Fixture when creating a run."""

    fixture_id: str
    fixture_version_id: str


class UpdateFixtureInput(TypedDict, total=False):
    name: str
    description: str
    entries: Sequence[AgentEvalsFixtureEntryInput]


class _FindOrCreateGraderDefinitionInputRequired(TypedDict):
    name: str


class FindOrCreateGraderDefinitionInput(
    _FindOrCreateGraderDefinitionInputRequired, total=False
):
    description: str
    kind: AgentEvalsGraderKind
    prompt: str
    code: str
    model: str
    tags: Sequence[str]


class AgentEvalsGraderVersionOverride(TypedDict):
    """Select a Grader Version for one Grader when creating a run."""

    grader_id: str
    grader_version_id: str


class CreateRunInput(TypedDict, total=False):
    """Choose ``suite_id`` for server-driven mode or ``suite_name`` for report-only mode."""

    suite_id: str
    suite_name: str
    git_branch: str
    git_sha: str
    git_repo_url: str
    model: str
    name: str
    status: AgentEvalsClientRunStatus
    metadata: Dict[str, Any]
    fixture_overrides: Sequence[AgentEvalsFixtureVersionOverride]
    grader_overrides: Sequence[AgentEvalsGraderVersionOverride]


class _ReportTrialAssertionInputRequired(TypedDict):
    assertion_name: str


class ReportTrialAssertionInput(_ReportTrialAssertionInputRequired, total=False):
    passed: bool
    score: float
    reasoning: str


class _ReportTrialGraderInputRequired(TypedDict):
    grader_name: str
    assertions: Sequence[ReportTrialAssertionInput]


class ReportTrialGraderInput(_ReportTrialGraderInputRequired):
    pass


class _ReportOnlyTaskInputRequired(TypedDict):
    key: str
    input: str


class ReportOnlyTaskInput(_ReportOnlyTaskInputRequired, total=False):
    name: str
    expected_output: str
    tags: Sequence[str]


class _ReportTrialInputRequired(TypedDict):
    transcript: Mapping[str, Sequence[OpenInferenceSpan]]


class ReportTrialInput(_ReportTrialInputRequired, total=False):
    task_key: str
    task: ReportOnlyTaskInput
    trial_number: int
    status: AgentEvalsTrialStatus
    cost: float
    latency_ms: int
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cached_tokens: int
    cache_write_5m_tokens: int
    cache_write_1h_tokens: int
    attachment_upload_ids: Sequence[str]
    grader_definitions: Sequence[FindOrCreateGraderDefinitionInput]
    graders: Sequence[ReportTrialGraderInput]
    grade: bool


class AgentEvalsUpload(TypedDict):
    upload_id: str
    upload_url: str
    method: str
    max_bytes: int
    expires_at: str
    instructions: str


class UpdateRunInput(TypedDict, total=False):
    status: AgentEvalsClientRunStatus
    metadata: Dict[str, Any]


class _CreateUploadInputRequired(TypedDict):
    filename: str


class CreateUploadInput(_CreateUploadInputRequired, total=False):
    content_type: str


JsonObject = Mapping[str, Any]
BytesLike = Union[bytes, bytearray, memoryview]


class AgentEvalsError(Exception):
    """A non-successful response from the Agent Evals API."""

    def __init__(self, status: int, method: str, path: str, body: str):
        self.status = status
        self.method = method
        self.path = path
        self.body = body
        super().__init__(
            f"Fabricate agent evals request {method} {path} "
            f"failed with {status}: {body}"
        )


def _encode(value: str) -> str:
    return quote(value, safe="")


class AgentEvalsClient:
    """Client for Fabricate's framework-agnostic Agent Evals API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        session: Optional[requests.Session] = None,
    ):
        resolved_api_key = api_key or os.environ.get("FABRICATE_API_KEY")
        if not resolved_api_key:
            raise ValueError(
                "api_key is required (set it explicitly or via FABRICATE_API_KEY)"
            )

        self.api_key = resolved_api_key
        self.api_url = (
            api_url or os.environ.get("FABRICATE_API_URL") or DEFAULT_API_URL
        ).rstrip("/")
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[JsonObject] = None,
        params: Optional[Mapping[str, Optional[str]]] = None,
    ) -> Any:
        search_params = {
            key: value
            for key, value in (params or {}).items()
            if value is not None and value != ""
        }
        response = self.session.request(
            method,
            f"{self.api_url}{path}",
            json=json,
            params=search_params or None,
        )
        if not response.ok:
            raise AgentEvalsError(
                response.status_code, method.upper(), path, response.text
            )
        if not response.content:
            return None
        return response.json()

    # Projects

    def list_projects(self, workspace: str) -> List[AgentEvalsProject]:
        return cast(
            List[AgentEvalsProject],
            self._request("GET", f"/workspaces/{_encode(workspace)}/projects"),
        )

    def find_or_create_project(
        self, workspace: str, input: FindOrCreateProjectInput
    ) -> AgentEvalsProject:
        return cast(
            AgentEvalsProject,
            self._request(
                "POST",
                f"/workspaces/{_encode(workspace)}/projects",
                json=input,
            ),
        )

    # Suites

    def list_suites(self, project_id: str) -> List[AgentEvalsSuite]:
        return cast(
            List[AgentEvalsSuite],
            self._request("GET", f"/projects/{_encode(project_id)}/suites"),
        )

    def find_or_create_suite(
        self, project_id: str, input: FindOrCreateSuiteInput
    ) -> AgentEvalsSuite:
        return cast(
            AgentEvalsSuite,
            self._request(
                "POST",
                f"/projects/{_encode(project_id)}/suites",
                json=input,
            ),
        )

    def find_suite(
        self,
        project_id: str,
        *,
        id: Optional[str] = None,
        name: Optional[str] = None,
        version: Optional[int] = None,
    ) -> Optional[AgentEvalsSuite]:
        """Find a suite version without creating it.

        When ``version`` is omitted the highest-numbered version of the matching
        suite is returned.
        """
        suites = self.list_suites(project_id)
        if id:
            return next((suite for suite in suites if suite["id"] == id), None)
        if name:
            wanted_name = name.casefold()
            named = [suite for suite in suites if suite["name"].casefold() == wanted_name]
            if version is not None:
                return next((suite for suite in named if suite.get("version") == version), None)
            return max(named, key=lambda suite: suite.get("version", 0), default=None)
        return None

    def create_suite_version(self, suite_id: str) -> AgentEvalsSuite:
        """Create the next version of a suite by copying the given version."""
        return cast(
            AgentEvalsSuite,
            self._request("POST", f"/suites/{_encode(suite_id)}/versions"),
        )

    # Tasks

    def list_tasks(self, suite_id: str) -> List[AgentEvalsTask]:
        return cast(
            List[AgentEvalsTask],
            self._request("GET", f"/suites/{_encode(suite_id)}/tasks"),
        )

    def upsert_task(self, suite_id: str, input: UpsertTaskInput) -> AgentEvalsTask:
        return cast(
            AgentEvalsTask,
            self._request("POST", f"/suites/{_encode(suite_id)}/tasks", json=input),
        )

    # Fixtures

    def list_fixtures(self, project_id: str) -> List[AgentEvalsFixtureVersion]:
        """List Fixture Versions; the API returns the latest version by default."""
        return cast(
            List[AgentEvalsFixtureVersion],
            self._request("GET", f"/projects/{_encode(project_id)}/fixtures"),
        )

    def find_or_create_fixture(
        self, project_id: str, input: FixtureInput
    ) -> AgentEvalsFixtureVersion:
        """Find or create a Fixture, returning its latest Fixture Version."""
        return cast(
            AgentEvalsFixtureVersion,
            self._request(
                "POST",
                f"/projects/{_encode(project_id)}/fixtures",
                json=input,
            ),
        )

    def get_fixture_version(self, fixture_version_id: str) -> AgentEvalsFixtureVersion:
        return cast(
            AgentEvalsFixtureVersion,
            self._request("GET", f"/fixtures/{_encode(fixture_version_id)}"),
        )

    def get_fixture(self, fixture_version_id: str) -> AgentEvalsFixtureVersion:
        """Deprecated alias for :meth:`get_fixture_version`."""
        return self.get_fixture_version(fixture_version_id)

    def create_fixture_version(
        self, fixture_version_id: str
    ) -> AgentEvalsFixtureVersion:
        """Create the next Fixture Version by copying the given version."""
        return cast(
            AgentEvalsFixtureVersion,
            self._request("POST", f"/fixtures/{_encode(fixture_version_id)}/versions"),
        )

    def update_fixture(
        self, fixture_id: str, input: UpdateFixtureInput
    ) -> AgentEvalsFixtureVersion:
        return cast(
            AgentEvalsFixtureVersion,
            self._request("PATCH", f"/fixtures/{_encode(fixture_id)}", json=input),
        )

    def delete_fixture(self, fixture_id: str) -> None:
        self._request("DELETE", f"/fixtures/{_encode(fixture_id)}")

    def download_fixture_database(self, fixture_id: str, database_id: str) -> bytes:
        """Download SQLite bytes for a database referenced by a fixture."""
        path = f"/fixtures/{_encode(fixture_id)}/databases/" f"{_encode(database_id)}"
        response = self.session.get(
            f"{self.api_url}{path}",
            headers={"Accept": "application/vnd.sqlite3"},
        )
        if not response.ok:
            raise AgentEvalsError(response.status_code, "GET", path, response.text)
        return cast(bytes, response.content)

    # Graders

    def list_graders(
        self, project_id: str
    ) -> List[AgentEvalsGraderVersion]:
        return cast(
            List[AgentEvalsGraderVersion],
            self._request(
                "GET",
                f"/projects/{_encode(project_id)}/grader_definitions",
            ),
        )

    def list_grader_definitions(
        self, project_id: str
    ) -> List[AgentEvalsGraderVersion]:
        """Deprecated alias for :meth:`list_graders`."""
        return self.list_graders(project_id)

    def find_or_create_grader(
        self,
        project_id: str,
        input: FindOrCreateGraderDefinitionInput,
    ) -> AgentEvalsGraderVersion:
        return cast(
            AgentEvalsGraderVersion,
            self._request(
                "POST",
                f"/projects/{_encode(project_id)}/grader_definitions",
                json=input,
            ),
        )

    def find_or_create_grader_definition(
        self,
        project_id: str,
        input: FindOrCreateGraderDefinitionInput,
    ) -> AgentEvalsGraderVersion:
        """Deprecated alias for :meth:`find_or_create_grader`."""
        return self.find_or_create_grader(project_id, input)

    def create_grader_version(
        self, grader_version_id: str
    ) -> AgentEvalsGraderVersion:
        """Create the next Grader Version by copying the given version."""
        return cast(
            AgentEvalsGraderVersion,
            self._request(
                "POST",
                f"/grader_definitions/{_encode(grader_version_id)}/versions",
            ),
        )

    # Runs

    def list_runs(
        self, project_id: str, *, branch: Optional[str] = None
    ) -> List[AgentEvalsRun]:
        return cast(
            List[AgentEvalsRun],
            self._request(
                "GET",
                f"/projects/{_encode(project_id)}/runs",
                params={"branch": branch},
            ),
        )

    def create_run(
        self, project_id: str, input: CreateRunInput
    ) -> AgentEvalsRun:
        return cast(
            AgentEvalsRun,
            self._request(
                "POST",
                f"/projects/{_encode(project_id)}/runs",
                json=input,
            ),
        )

    def get_run(self, run_id: str) -> AgentEvalsRunWithTrials:
        return cast(
            AgentEvalsRunWithTrials,
            self._request("GET", f"/runs/{_encode(run_id)}"),
        )

    def update_run(self, run_id: str, input: UpdateRunInput) -> AgentEvalsRun:
        return cast(
            AgentEvalsRun,
            self._request("PATCH", f"/runs/{_encode(run_id)}", json=input),
        )

    # Trials

    def report_trial(self, run_id: str, input: ReportTrialInput) -> AgentEvalsTrial:
        return cast(
            AgentEvalsTrial,
            self._request("POST", f"/runs/{_encode(run_id)}/trials", json=input),
        )

    def get_trial(self, trial_id: str) -> AgentEvalsTrial:
        return cast(
            AgentEvalsTrial,
            self._request("GET", f"/trials/{_encode(trial_id)}"),
        )

    def wait_for_grading(
        self,
        trial_id: str,
        *,
        interval_seconds: float = DEFAULT_GRADING_INTERVAL_SECONDS,
        timeout_seconds: float = DEFAULT_GRADING_TIMEOUT_SECONDS,
        cancel_event: Optional[Event] = None,
    ) -> AgentEvalsTrial:
        """Poll until asynchronous grading completes, fails, or times out."""
        deadline = time.monotonic() + timeout_seconds
        trial = self.get_trial(trial_id)
        grading = trial.get("grading")

        while grading and grading["status"] not in ("completed", "failed"):
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Timed out after {timeout_seconds:g}s waiting for "
                    f"trial {trial_id} grading."
                )

            if cancel_event:
                if cancel_event.wait(interval_seconds):
                    raise RuntimeError("Aborted")
            else:
                time.sleep(interval_seconds)

            trial = self.get_trial(trial_id)
            grading = trial.get("grading")

        return trial

    # Attachments

    def create_upload(
        self, workspace: str, input: CreateUploadInput
    ) -> AgentEvalsUpload:
        return cast(
            AgentEvalsUpload,
            self._request(
                "POST",
                f"/workspaces/{_encode(workspace)}/agent_evals/uploads",
                json=input,
            ),
        )

    def put_upload_bytes(
        self,
        upload_url: str,
        data: BytesLike,
        content_type: Optional[str] = None,
    ) -> None:
        headers = {"Content-Type": content_type} if content_type else None
        response = self.session.put(upload_url, data=bytes(data), headers=headers)
        if not response.ok:
            raise AgentEvalsError(
                response.status_code, "PUT", upload_url, response.text
            )

    def upload_attachment(
        self,
        workspace: str,
        *,
        filename: str,
        data: BytesLike,
        content_type: Optional[str] = None,
    ) -> str:
        upload_input: CreateUploadInput = {"filename": filename}
        if content_type:
            upload_input["content_type"] = content_type
        upload = self.create_upload(workspace, upload_input)
        self.put_upload_bytes(upload["upload_url"], data, content_type)
        return upload["upload_id"]


__all__ = [
    "AgentEvalsAssertion",
    "AgentEvalsAttachment",
    "AgentEvalsClient",
    "AgentEvalsError",
    "AgentEvalsFixture",
    "AgentEvalsFixtureVersion",
    "AgentEvalsFixtureEntry",
    "AgentEvalsFixtureEntryInput",
    "AgentEvalsFixtureEntryType",
    "AgentEvalsFixtureVersionOverride",
    "AgentEvalsGrader",
    "AgentEvalsGraderDefinition",
    "AgentEvalsGraderKind",
    "AgentEvalsGraderVersion",
    "AgentEvalsGraderVersionOverride",
    "AgentEvalsGrading",
    "AgentEvalsGradingStatus",
    "AgentEvalsProject",
    "AgentEvalsClientRunStatus",
    "AgentEvalsRun",
    "AgentEvalsRunStatus",
    "AgentEvalsRunWithTrials",
    "AgentEvalsSuite",
    "AgentEvalsTask",
    "AgentEvalsTrial",
    "AgentEvalsTrialStatus",
    "AgentEvalsTrialSummary",
    "AgentEvalsUpload",
    "CreateUploadInput",
    "CreateRunInput",
    "FindOrCreateProjectInput",
    "FindOrCreateGraderDefinitionInput",
    "FindOrCreateSuiteInput",
    "FixtureInput",
    "OpenInferenceSpan",
    "ReportTrialInput",
    "ReportOnlyTaskInput",
    "UpdateFixtureInput",
    "UpdateRunInput",
    "UpsertTaskInput",
]

# Fabricate Client

The official [Fabricate](https://www.tonic.ai/products/fabricate) client package for Python.

## Installation

```bash
pip install tonic-fabricate
```

## Usage

### Report-only Agent Evals

Client-owned tasks and grader prompts can be reported without creating
Fabricate definitions:

```python
run = client.create_run(project_id, {"suite_name": "Git-defined evals", "model": model})
client.report_trial(
    run["id"],
    {
        "task": {"key": "users", "input": "Generate 100 users", "tags": ["users"]},
        "grader_definitions": [
            {"name": "quality", "prompt": "Inspect the attached data.", "tags": ["users"]}
        ],
        "transcript": {"messages": spans},
        "attachment_upload_ids": upload_ids,
        "grade": True,
    },
)
```

Trial token metrics include `cache_read_tokens`, `cache_write_5m_tokens`, and
`cache_write_1h_tokens`. Fabricate can derive them from equivalent
`llm.token_count.prompt_details.*` OpenInference attributes.

To generate and download data from Fabricate:

```python
from tonic_fabricate import generate

generate(
    # The workspace to use
    workspace='Default',

    # The name of the database to generate
    database='ecommerce',

    # The format to generate. Should be one of:
    # - 'sql'
    # - 'sqlite'
    # - 'csv'
    # - 'jsonl'
    # - 'xml'
    format='sql',

    # The destination to save the data
    dest='./data',

    # Optional: Overwrite the destination if it exists
    overwrite=True,

    # Optional: Generate a single table
    # entity='Customers',
)
```

To push data to an existing database:

```python
from tonic_fabricate import generate
import os

generate(
    # The workspace to use
    workspace='Default',

    # The name of the database in Fabricate
    database='ecommerce',

    # The connection details for the target database
    connection={
        # The host of the target database
        'host': 'host.example.com',

        # The port of the target database
        'port': 5432,

        # The name of the target database
        'database_name': 'ecommerce',

        # The username for the target database
        'username': os.environ.get('FABRICATE_DATABASE_USERNAME'),

        # The password for the target database
        'password': os.environ.get('FABRICATE_DATABASE_PASSWORD'),

        # Whether to use TLS for the connection
        'tls': True,
    },
)
```

## Progress Tracking

You can track the progress of data generation using a callback function:

```python
from tonic_fabricate import generate

def on_progress(data):
    phase = data.get('phase', '')
    percent = data.get('percentComplete', 0)
    status = data.get('status', '')

    phase_text = f"[{phase}] " if phase else ""
    status_text = f", {status}" if status else ""
    print(f"{phase_text}{percent}% complete{status_text}...")

generate(
    workspace='Default',
    database='ecommerce',
    format='sql',
    dest='./data',
    on_progress=on_progress
)
```

## Environment Variables

The client will automatically use the following environment variables if they are set:

- `FABRICATE_API_KEY`: Your Fabricate API key
- `FABRICATE_API_URL`: The Fabricate API URL (defaults to https://fabricate.tonic.ai/api/v1)

## Workflows

Fabricate supports workflows that can perform custom operations and generate files. To run a workflow:

```python
from tonic_fabricate import run_workflow

result = run_workflow(
    # The workspace to use
    workspace='Default',

    # The name of the database
    database='my_database',

    # The name of the workflow to run
    workflow='my_workflow',

    # Optional: Parameters to pass to the workflow
    params={
        'message': 'Hello, world!',
    },
)

# Access the workflow result
print(f"Result: {result.result}")

# Download generated files if any
if result.task.files:
    for file in result.task.files:
        print(f"File: {file.name} ({file.size} bytes)")
        result.download_file(file.id, f"./output/{file.name}")

    # Or download all files at once
    result.download_all_files('./output')
```

### Workflow Progress Tracking

```python
from tonic_fabricate import run_workflow

def on_progress(data):
    status = data.get('status', '')
    message = data.get('message', '')
    print(f"[{status}] {message}")

result = run_workflow(
    workspace='Default',
    database='my_database',
    workflow='my_workflow',
    on_progress=on_progress
)
```

### Workflow File Downloads

You can also download workflow files directly using `download_workflow_file`:

```python
from tonic_fabricate import download_workflow_file

download_workflow_file(
    task_id='your-task-id',
    file_id=123,
    dest_path='./output/file.txt'
)
```

## Agent Evals

`AgentEvalsClient` runs any Python agent against evaluation suites managed in
Fabricate. It is framework-independent: invoke your agent however you prefer,
then report its execution as flattened
[OpenInference](https://github.com/Arize-ai/openinference) spans.

```python
from tonic_fabricate import AgentEvalsClient

client = AgentEvalsClient()

# Fabricate is the source of truth for the suite and its tasks.
suite = client.find_suite(
    project_id="your-project-id",
    name="Agent Eval Tasks",
)
if suite is None:
    raise RuntimeError("Suite not found")

tasks = client.list_tasks(suite["id"])
run = client.create_run(
    "your-project-id",
    {
        "suite_id": suite["id"],
        "model": "gpt-5-mini",
        "git_branch": "feature/my-agent",
    },
)

for task in tasks:
    # Replace this span with the OpenInference spans captured from your agent.
    transcript = [
        {
            "name": "my-agent",
            "attributes": {
                "openinference.span.kind": "AGENT",
                "input.value": task["input"],
            },
        }
    ]
    reported = client.report_trial(
        run["id"],
        {
            "task_key": task["key"],
            "transcript": {"messages": transcript},
            "grade": True,
        },
    )
    graded = client.wait_for_grading(reported["id"])
    print(task["key"], "PASS" if graded["passed"] else "FAIL")

client.update_run(run["id"], {"status": "completed"})
```

The client reads `FABRICATE_API_KEY` and `FABRICATE_API_URL` by default.
`wait_for_grading` polls every three seconds and times out after two minutes;
both values are configurable.

`find_suite(project_id, name="Agent Eval Tasks")` selects the latest version.
Pin a CI run with `version=2`, or pass a suite **version** UUID with `id=...`.
Use that version UUID (`suite["id"]`) for `list_tasks` and `create_run`; do
not use the stable suite UUID in `suite["suite_id"]`. To snapshot a version's
metadata and tasks into the next version, call
`client.create_suite_version(suite["id"])`.

### Attachments

Upload a file before reporting a trial, then reference its upload ID:

```python
upload_id = client.upload_attachment(
    "Default",
    filename="payments.csv",
    content_type="text/csv",
    data=csv_bytes,
)

client.report_trial(
    run["id"],
    {
        "task_key": "payments-csv",
        "transcript": {"messages": transcript},
        "attachment_upload_ids": [upload_id],
        "grade": True,
    },
)
```

### Fixture Versions, Grader Versions, and management APIs

Tasks expose their resolved Fixture Version as `effective_fixture`. Database
Fixture Version entries can be materialized as SQLite bytes:

```python
sqlite_bytes = client.download_fixture_database(
    fixture_id=task["effective_fixture"]["id"],
    database_id=database_entry["value"]["database_id"],
)
```

Fixtures and Graders each have independently numbered versions. The
`list_fixtures` and `list_graders` APIs return the latest version by default;
use `create_fixture_version(fixture_version_id)` or
`create_grader_version(grader_version_id)` to copy a mutable version into the
next version. Pin a run's selected inputs with structured override lists:

```python
client.create_run(
    project_id,
    {
        "suite_id": suite["id"],
        "fixture_overrides": [
            {
                "fixture_id": "fixture-uuid",
                "fixture_version_id": "fixture-version-uuid",
            }
        ],
        "grader_overrides": [
            {
                "grader_id": "grader-uuid",
                "grader_version_id": "grader-version-uuid",
            }
        ],
    },
)
```

The run snapshots its resolved Fixture Version manifests and Grader Version
rubrics at creation, so subsequent edits do not change history.
`list_grader_definitions` and `find_or_create_grader_definition` remain
deprecated aliases for endpoint compatibility.

## Error Handling

The client raises appropriate exceptions for various error conditions:

```python
from tonic_fabricate import generate, run_workflow

try:
    generate(
        workspace='Default',
        database='ecommerce',
        format='sql',
        dest='./data'
    )
except ValueError as e:
    print(f"Invalid parameters: {e}")
except Exception as e:
    print(f"Generation failed: {e}")

try:
    result = run_workflow(
        workspace='Default',
        database='my_database',
        workflow='my_workflow'
    )
except ValueError as e:
    print(f"Invalid parameters: {e}")
except Exception as e:
    print(f"Workflow failed: {e}")
```

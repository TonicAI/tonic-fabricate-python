# Fabricate Client

The official [Fabricate](https://www.tonic.ai/products/fabricate) client package for Python.

## Installation

```bash
pip install tonic-fabricate
```

## Usage

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

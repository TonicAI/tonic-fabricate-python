# Development Guide

This guide covers how to set up and test the package locally before publishing.

## Setup

### Create a Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows
```

### Install in Development Mode

With the virtual environment activated, install the package with dev dependencies:

```bash
# Install in editable/development mode with dev dependencies
pip install -e ".[dev]"
```

This installs the package along with `python-dotenv` (for `.env` file support), `pytest`, `mypy`, `black`, and `flake8`.

### Environment Variables

Set the following environment variables for testing:

```bash
export FABRICATE_API_KEY="your-api-key"
export FABRICATE_API_URL="https://fabricate.tonic.ai/api/v1"  # or your local instance
```

Or create a `.env` file (requires `python-dotenv`):

```
FABRICATE_API_KEY=your-api-key
FABRICATE_API_URL=https://fabricate.tonic.ai/api/v1
```

## Testing

### Quick Import Test

Verify the module imports correctly:

```bash
python -c "from tonic_fabricate import generate, run_workflow, WorkflowResult; print('All imports work!')"
```

### Run the Examples

The examples test the actual API calls:

```bash
# Test the generate function
python examples/download.py

# Test the workflow function
python examples/workflow.py
```

### Interactive Testing

```python
from tonic_fabricate import run_workflow
import os

result = run_workflow(
    database='your_database',
    workspace='your_workspace',
    workflow='your_workflow',
    api_url=os.environ.get('FABRICATE_API_URL'),
    on_progress=lambda p: print(p)
)
print(result.result)
```

## Code Quality

### Install Dev Dependencies

```bash
pip install -r requirements-dev.txt
```

### Type Checking

```bash
mypy tonic_fabricate/
```

### Linting

```bash
flake8 tonic_fabricate/
```

### Formatting

```bash
# Check formatting
black --check tonic_fabricate/

# Auto-format
black tonic_fabricate/
```

## Pre-Publish Testing

Before publishing to production PyPI, test with TestPyPI:

```bash
# Publish to TestPyPI
./publish-test.sh

# Install from TestPyPI to verify
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ tonic-fabricate==1.1.0

# Test the installed package
python -c "from tonic_fabricate import generate, run_workflow; print('Package works!')"
```

## Publishing

See [publishing.md](publishing.md) for detailed publishing instructions.

### Quick Reference

```bash
# Test publish
./publish-test.sh

# Production publish (after testing)
./publish.sh
```

## Deactivating the Virtual Environment

When you're done developing:

```bash
deactivate
```

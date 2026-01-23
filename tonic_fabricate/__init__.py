"""
Tonic Fabricate - The official Fabricate client for Python.
"""

from .client import (
    generate,
    run_workflow,
    download_workflow_file,
    WorkflowFile,
    WorkflowTask,
    WorkflowResult,
)

__version__ = "1.1.0"

__all__ = [
    "generate",
    "run_workflow",
    "download_workflow_file",
    "WorkflowFile",
    "WorkflowTask",
    "WorkflowResult",
] 
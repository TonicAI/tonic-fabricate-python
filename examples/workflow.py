#!/usr/bin/env python3
"""
Example script for running a workflow in Fabricate.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

from tonic_fabricate import run_workflow

def on_progress(data):
    """Progress callback function."""
    status = data.get('status', '')
    message = data.get('message', '')
    print(f"[{status}] {message}")

if __name__ == "__main__":
    print("Starting workflow...")

    # Prepare arguments
    kwargs = {
        'database': 'agent_api_test',
        'workspace': 'API',
        'workflow': 'file',
        'params': {
            'message': 'Hello, world!',
        },
        'on_progress': on_progress,
    }

    # Add api_url if available
    api_url = os.environ.get('FABRICATE_API_URL')
    if api_url:
        kwargs['api_url'] = api_url

    # Run the workflow
    workflow_result = run_workflow(**kwargs)

    print(f"Workflow result: {workflow_result.result}")

    # List and download files if any were generated
    if workflow_result.task.files:
        print(f"\nWorkflow generated {len(workflow_result.task.files)} file(s):")

        dest_dir = './tmp/workflow_output'

        for file in workflow_result.task.files:
            print(f"  - {file.name} ({file.content_type}, {file.size} bytes, id: {file.id})")

            # Download a specific file by id
            workflow_result.download_file(file.id, f"{dest_dir}/{file.name}")

        # Or, download all files to a directory
        # print('\nDownloading all files...')
        # workflow_result.download_all_files(dest_dir)
        # print(f'Files downloaded to {dest_dir}/')

    print("Done.")

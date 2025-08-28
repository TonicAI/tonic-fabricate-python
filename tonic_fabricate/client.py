import os
import time
import zipfile
import shutil
from pathlib import Path
from typing import Optional, Callable, Dict, Any, Union
import requests


def generate(
    api_key: Optional[str] = None,
    api_url: str = "https://fabricate.tonic.ai/api/v1",
    database: Optional[str] = None,
    workspace: Optional[str] = None,
    entity: Optional[str] = None,
    format: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
    on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
    dest: Optional[str] = None,
    unzip: bool = True,
    overwrite: bool = False,
    connection: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Generates data for a given database.
    
    Args:
        api_key: The API key for authentication. Defaults to FABRICATE_API_KEY env var.
        api_url: The API URL. Defaults to https://fabricate.tonic.ai/api/v1
        database: The name of the database to generate (required)
        workspace: The workspace to use (required)
        entity: Optional single entity/table to generate
        format: The output format (sql, sqlite, csv, jsonl, xml)
        overrides: Optional override parameters
        on_progress: Optional progress callback function
        dest: Destination path for downloaded files (required unless connection provided)
        unzip: Whether to unzip downloaded files (default: True)
        overwrite: Whether to overwrite existing destination (default: False)
        connection: Database connection details for direct push
        
    Raises:
        ValueError: If required parameters are missing or invalid
        requests.HTTPError: If API requests fail
        Exception: If task execution fails
    """
    # Get API key from parameter or environment
    if api_key is None:
        api_key = os.environ.get('FABRICATE_API_KEY')
    
    # Validate required parameters
    if not api_key:
        raise ValueError('api_key is required')
    
    if not database:
        raise ValueError('database is required')
    
    if not workspace:
        raise ValueError('workspace is required')
    
    if not format and not connection:
        raise ValueError('format or connection is required')
    
    if format and connection:
        raise ValueError('format and connection cannot both be provided')
    
    if not dest and not connection:
        raise ValueError('dest is required unless connection is provided')
    
    if dest and Path(dest).exists() and not overwrite:
        raise ValueError('dest already exists')
    
    # Create the generation task
    headers = {'Authorization': f'Bearer {api_key}'}
    payload = {
        'format': format,
        'connection': connection,
        'database': database,
        'entity': entity,
        'overrides': overrides,
        'workspace': workspace
    }
    
    try:
        response = requests.post(
            f'{api_url}/generate_tasks',
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        task = response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.headers.get('content-type') == 'application/json':
            error_data = e.response.json()
            raise Exception(error_data.get('error', str(e)))
        else:
            raise e
    
    if task.get('error'):
        raise Exception(task['error'])
    
    # Poll until completion
    task = _poll(task['id'], api_url, api_key, on_progress)
    
    data_url = task.get('data_url')
    error = task.get('error')
    
    if error:
        print(f'Fabricate API returned an error: {error}')
        raise Exception(error)
    
    # Download data if not pushing to connection
    if connection is None and dest is not None and data_url is not None:
        temp_path = f'{dest}.tmp'
        
        try:
            # Download to temp location first
            _download(data_url, temp_path)
            
            if unzip and task.get('content_type') == 'application/zip':
                _unzip_file(temp_path, dest)
            else:
                # Move temp file to final destination
                Path(temp_path).rename(dest)
        finally:
            # Clean up temp file if it exists
            temp_file = Path(temp_path)
            if temp_file.exists():
                temp_file.unlink()


def _poll(
    task_id: str,
    api_url: str,
    api_key: str,
    on_progress: Optional[Callable[[Dict[str, Any]], None]] = None
) -> Dict[str, Any]:
    """
    Polls the generate task API until the task is completed.
    
    Args:
        task_id: The ID of the task to poll
        api_url: The API URL
        api_key: The API key
        on_progress: Optional progress callback
        
    Returns:
        The completed task object
        
    Raises:
        Exception: If task fails or API returns an error
    """
    headers = {'Authorization': f'Bearer {api_key}'}
    last_progress = None
    last_context = None
    
    while True:
        response = requests.get(
            f'{api_url}/generate_tasks/{task_id}',
            headers=headers
        )
        response.raise_for_status()
        task = response.json()
        
        if task.get('completed'):
            _update_progress({'progress': 100}, on_progress, last_progress, last_context)
            return task
        elif task.get('error'):
            raise Exception(task['error'])
        else:
            last_progress, last_context = _update_progress(
                task, on_progress, last_progress, last_context
            )
            time.sleep(1)


def _update_progress(
    task: Dict[str, Any],
    on_progress: Optional[Callable[[Dict[str, Any]], None]],
    last_progress: Optional[Any],
    last_context: Optional[str]
) -> tuple:
    """
    Updates progress if callback is provided and progress has changed.
    
    Args:
        task: The task object containing progress information
        on_progress: Optional progress callback
        last_progress: The last reported progress value
        last_context: The last reported context
        
    Returns:
        Tuple of (current_progress, current_context)
    """
    if not on_progress:
        return last_progress, last_context
    
    current_progress = task.get('progress')
    current_context = task.get('context')
    
    if current_progress != last_progress or current_context != last_context:
        progress_data = {
            'percentComplete': current_progress,
            'status': current_context,
            'phase': task.get('phase')
        }
        on_progress(progress_data)
        return current_progress, current_context
    
    return last_progress, last_context


def _unzip_file(zip_path: str, target_dir: str) -> None:
    """
    Unzips a file to a target directory.
    
    Args:
        zip_path: Path to the zip file
        target_dir: Target directory to extract to
    """
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(target_dir)


def _download(url: str, dest_path: str) -> None:
    """
    Downloads a file from a URL and saves it to a path.
    
    Args:
        url: The URL to download from
        dest_path: The path to save the file to
    """
    # Ensure the directory exists
    dest_file = Path(dest_path)
    dest_dir = dest_file.parent
    
    if dest_dir != Path('.'):
        # Remove directory if it exists
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        
        # Create directory
        dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Download the file
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk) 
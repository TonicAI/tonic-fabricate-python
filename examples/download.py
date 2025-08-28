#!/usr/bin/env python3
"""
Example script for downloading data from Fabricate.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tonic_fabricate import generate

# Load environment variables if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def on_progress(data):
    """Progress callback function."""
    phase = data.get('phase', '')
    percent = data.get('percentComplete', 0)
    status = data.get('status', '')
    
    phase_text = f"[{phase}] " if phase else ""
    status_text = f", {status}" if status else ""
    print(f"{phase_text}{percent}% complete{status_text}...")

if __name__ == "__main__":
    print("starting...")

    # Prepare arguments
    kwargs = {
        'database': 'XML',
        'workspace': 'Default',
        'format': 'xml',
        'dest': './tmp/xml',
        'overwrite': True,
        'on_progress': on_progress,
        # Uncomment to generate a single table
        # 'entity': 'Customers',
    }
    
    # Add api_url if available
    api_url = os.environ.get('FABRICATE_API_URL')
    if api_url:
        kwargs['api_url'] = api_url

    generate(**kwargs)

    print("done.") 
#!/usr/bin/env python
import os
import sys
import django
import warnings

# Suppress pydantic warnings
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core._api.deprecation")

# Get backend directory
backend_dir = r'c:\Users\wael\Desktop\FinalVersionpfe\LeaCall-BI\backend'
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

# Set Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'ETL_Project.settings'

# Setup Django  
django.setup()

# Import and run server
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    print(f"Starting Django server from {backend_dir}")
    print(f"PYTHONPATH: {sys.path[0]}")
    print(f"DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    try:
        execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

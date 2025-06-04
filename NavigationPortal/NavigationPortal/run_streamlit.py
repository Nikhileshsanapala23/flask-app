#!/usr/bin/env python3
import subprocess
import sys
import os
import logging
import time

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("streamlit_launcher.log"),
        logging.StreamHandler()
    ]
)

def run_direct():
    """Run a system command directly to test for import errors"""
    try:
        logging.info("Testing direct import of streamlit")
        result = subprocess.run(
            ["python", "-c", "import streamlit; print(f'Streamlit version: {streamlit.__version__}')"],
            capture_output=True,
            text=True
        )
        
        logging.info(f"Import test stdout: {result.stdout}")
        if result.stderr:
            logging.error(f"Import test stderr: {result.stderr}")
            
        logging.info("Testing imports for other dependencies")
        tests = [
            "import pandas; print(f'Pandas version: {pandas.__version__}')",
            "import plotly; print(f'Plotly version: {plotly.__version__}')",
            "import bcrypt; print('Bcrypt imported successfully')",
            "import psycopg2; print(f'Psycopg2 version: {psycopg2.__version__}')"
        ]
        
        for test in tests:
            result = subprocess.run(
                ["python", "-c", test],
                capture_output=True,
                text=True
            )
            logging.info(f"Test output: {result.stdout.strip()}")
            if result.stderr:
                logging.error(f"Test error: {result.stderr.strip()}")
    except Exception as e:
        logging.error(f"Error in direct tests: {str(e)}")

def run_streamlit():
    """Run the Streamlit application with proper error handling"""
    try:
        logging.info("Starting Streamlit application")
        
        # Check environment variables
        db_url = os.environ.get("DATABASE_URL")
        logging.info(f"DATABASE_URL exists: {db_url is not None}")
        
        # Try direct import testing
        run_direct()
        
        # Run streamlit directly with system call to capture output
        result = subprocess.run(
            ["streamlit", "run", "streamlit_interface.py", "--server.port=8501", 
             "--server.address=0.0.0.0", "--server.headless=true"],
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            logging.info(f"Streamlit output: {result.stdout}")
        
        if result.stderr:
            logging.error(f"Streamlit error: {result.stderr}")
            
        logging.info(f"Streamlit exit code: {result.returncode}")
        
    except Exception as e:
        logging.error(f"Error running Streamlit: {str(e)}")
        
if __name__ == "__main__":
    print("Starting Streamlit diagnostic launcher")
    run_streamlit()
    print("Finished Streamlit diagnostic run")
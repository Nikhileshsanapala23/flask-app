#!/bin/bash
echo "Starting Streamlit application..."
# Ensure we're stopping any previous instances
pkill -f streamlit || true
# Run streamlit with proper port binding
streamlit run streamlit_interface.py --server.port=8501 --server.address=0.0.0.0

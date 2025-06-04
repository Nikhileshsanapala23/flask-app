#!/bin/bash

# Start the Flask app
echo "Starting Flask application..."
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app &
FLASK_PID=$!
echo "Flask application running with PID $FLASK_PID"

# Wait a bit to make sure Flask is up
sleep 3

# Start the Streamlit app
echo "Starting Streamlit application..."
streamlit run streamlit_interface.py --server.port=8501 --server.address=0.0.0.0 &
STREAMLIT_PID=$!
echo "Streamlit application running with PID $STREAMLIT_PID"

# Function to handle termination
cleanup() {
    echo "Stopping applications..."
    kill $FLASK_PID $STREAMLIT_PID
    exit 0
}

# Register the cleanup function for various signals
trap cleanup SIGINT SIGTERM

# Keep the script running
echo "Both applications are running. Press Ctrl+C to stop."
wait
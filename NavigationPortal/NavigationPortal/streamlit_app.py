import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
import time
import bcrypt
import datetime
import threading
import random
from datetime import datetime, timedelta
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.colored_header import colored_header
from streamlit_extras.stateful_button import button
import plotly.graph_objects as go
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="JSON Downloader Portal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database setup
def get_db_connection():
    """Connect to the PostgreSQL database defined in the environment variables"""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

def init_db():
    """Initialize database tables if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables only if they don't exist
    # Reusing the existing schema from our Flask application
    
    # Since we're using an existing database from the Flask app,
    # we don't need to create tables here - they should already exist.
    # We'll just check if we can connect and query the tables.
    
    try:
        # Test query to see if tables exist
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        # Check if admin user exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = true")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            # Create admin user
            password_hash = bcrypt.hashpw("admin".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, is_admin) VALUES (%s, %s, %s, %s)",
                ("admin", "admin@example.com", password_hash, True)
            )
            conn.commit()
            
        # Close cursor and connection
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        # If there's an error, the tables might not exist or there might be another problem
        print(f"Database initialization error: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False

# Initialize the database
init_db()

# Helper functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_user_by_username(username):
    """Get user details by username using PostgreSQL"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    except Exception as e:
        print(f"Error getting user by username: {e}")
        cursor.close()
        conn.close()
        return None

def get_portals():
    conn = sqlite3.connect('json_downloader.db')
    c = conn.cursor()
    c.execute("SELECT * FROM portals")
    portals = c.fetchall()
    conn.close()
    return [{'id': p[0], 'name': p[1], 'url': p[2], 'description': p[3], 'created_at': p[4]} for p in portals]

def get_credentials_by_user(user_id):
    conn = sqlite3.connect('json_downloader.db')
    c = conn.cursor()
    c.execute('''
    SELECT c.id, c.user_id, c.portal_id, c.username, c.password_hash, c.created_at, c.updated_at, p.name, p.url
    FROM credentials c
    JOIN portals p ON c.portal_id = p.id
    WHERE c.user_id = ?
    ''', (user_id,))
    credentials = c.fetchall()
    conn.close()
    return [{
        'id': c[0],
        'user_id': c[1],
        'portal_id': c[2],
        'username': c[3],
        'password_hash': c[4],
        'created_at': c[5],
        'updated_at': c[6],
        'portal_name': c[7],
        'portal_url': c[8]
    } for c in credentials]

def get_downloads_by_user(user_id):
    conn = sqlite3.connect('json_downloader.db')
    c = conn.cursor()
    c.execute('''
    SELECT d.id, d.user_id, d.portal_id, d.credential_id, d.facility_username, d.download_type,
           d.start_date, d.end_date, d.status, d.progress, d.file_path, d.error_message,
           d.created_at, d.updated_at, p.name as portal_name, c.username as credential_username
    FROM downloads d
    JOIN portals p ON d.portal_id = p.id
    JOIN credentials c ON d.credential_id = c.id
    WHERE d.user_id = ?
    ORDER BY d.created_at DESC
    ''', (user_id,))
    downloads = c.fetchall()
    conn.close()
    return [{
        'id': d[0],
        'user_id': d[1],
        'portal_id': d[2],
        'credential_id': d[3],
        'facility_username': d[4],
        'download_type': d[5],
        'start_date': d[6],
        'end_date': d[7],
        'status': d[8],
        'progress': d[9],
        'file_path': d[10],
        'error_message': d[11],
        'created_at': d[12],
        'updated_at': d[13],
        'portal_name': d[14],
        'credential_username': d[15]
    } for d in downloads]

def fetch_json_from_portal(portal_url, username, password, start_date, end_date, download_type='submission', facility_username=None):
    """
    Simulate fetching JSON data from a portal
    In a real application, this would make actual API calls
    """
    # Simulate API processing time
    time.sleep(random.uniform(1.5, 3.5))
    
    # Generate mock data based on the parameters
    # In a real application, this would be the actual data from the API
    mock_data = {
        "portal_url": portal_url,
        "download_type": download_type,
        "facility_username": facility_username or username,
        "date_range": {
            "start_date": start_date,
            "end_date": end_date
        },
        "timestamp": datetime.now().isoformat(),
        "items": []
    }
    
    # Parse dates
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Generate some mock items
    date_range = (end - start).days + 1
    for i in range(min(date_range, 10)):  # Generate up to 10 items
        current_date = start + timedelta(days=i)
        
        if download_type == 'submission':
            # Generate mock submission data
            mock_data["items"].append({
                "id": f"SUB{random.randint(1000, 9999)}",
                "date": current_date.isoformat(),
                "status": random.choice(["Submitted", "Processed", "Pending"]),
                "amount": round(random.uniform(100, 5000), 2),
                "facility": facility_username or username,
                "items_count": random.randint(5, 50)
            })
        else:  # remittance
            # Generate mock remittance data
            mock_data["items"].append({
                "id": f"REM{random.randint(1000, 9999)}",
                "date": current_date.isoformat(),
                "status": random.choice(["Paid", "Pending", "Rejected"]),
                "amount": round(random.uniform(500, 10000), 2),
                "facility": facility_username or username,
                "payment_method": random.choice(["ACH", "Check", "Wire"]),
                "transaction_id": f"TX{random.randint(10000, 99999)}"
            })
    
    return mock_data

def schedule_download(user_id, portal_id, credential_id, facility_username, download_type, start_date, end_date):
    """Schedule a new download and return its ID"""
    conn = sqlite3.connect('json_downloader.db')
    c = conn.cursor()
    c.execute('''
    INSERT INTO downloads 
    (user_id, portal_id, credential_id, facility_username, download_type, start_date, end_date)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, portal_id, credential_id, facility_username, download_type, start_date, end_date))
    
    download_id = c.lastrowid
    conn.commit()
    conn.close()
    
    # Start a thread to process the download
    thread = threading.Thread(target=process_download, args=(download_id,))
    thread.daemon = True
    thread.start()
    
    return download_id

def process_download(download_id):
    """Process a scheduled download in a background thread"""
    conn = sqlite3.connect('json_downloader.db')
    c = conn.cursor()
    
    # Get download details
    c.execute('''
    SELECT d.id, d.portal_id, d.credential_id, d.facility_username, d.download_type,
           d.start_date, d.end_date, p.url, c.username, c.password_hash
    FROM downloads d
    JOIN portals p ON d.portal_id = p.id
    JOIN credentials c ON d.credential_id = c.id
    WHERE d.id = ?
    ''', (download_id,))
    download = c.fetchone()
    
    if not download:
        conn.close()
        return
    
    # Update status to in_progress
    c.execute("UPDATE downloads SET status = 'in_progress', progress = 5 WHERE id = ?", (download_id,))
    conn.commit()
    
    try:
        # Extract download details
        portal_url = download[7]
        username = download[8]
        password_hash = download[9]
        facility_username = download[3]
        download_type = download[4]
        start_date = download[5]
        end_date = download[6]
        
        # Simulate progress updates
        progress_steps = [10, 20, 30, 40, 50, 60, 70, 80, 90]
        for progress in progress_steps:
            time.sleep(random.uniform(0.5, 1.5))  # Simulate processing time
            c.execute("UPDATE downloads SET progress = ? WHERE id = ?", (progress, download_id))
            conn.commit()
        
        # Fetch data from portal (simulated)
        json_data = fetch_json_from_portal(
            portal_url, 
            username, 
            "password",  # In a real app, we'd decrypt the stored password
            start_date, 
            end_date,
            download_type,
            facility_username
        )
        
        # Create downloads directory if it doesn't exist
        os.makedirs('static/downloads', exist_ok=True)
        
        # Save the downloaded data to a file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{download_type}_{download_id}_{timestamp}.json"
        filepath = os.path.join('static/downloads', filename)
        
        with open(filepath, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        # Update download record
        c.execute('''
        UPDATE downloads 
        SET status = 'completed', progress = 100, file_path = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
        ''', (filepath, download_id))
        
    except Exception as e:
        # Handle errors
        c.execute('''
        UPDATE downloads 
        SET status = 'failed', error_message = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
        ''', (str(e), download_id))
    
    conn.commit()
    conn.close()

def get_download_status(download_id):
    """Get the current status of a download"""
    conn = sqlite3.connect('json_downloader.db')
    c = conn.cursor()
    c.execute('''
    SELECT status, progress, created_at, updated_at, file_path, error_message, download_type, facility_username
    FROM downloads
    WHERE id = ?
    ''', (download_id,))
    download = c.fetchone()
    conn.close()
    
    if not download:
        return None
    
    # Calculate estimated completion time if in progress
    estimated_completion = None
    if download[0] == 'in_progress' and download[1] > 0:
        created_at = datetime.strptime(download[2], '%Y-%m-%d %H:%M:%S')
        updated_at = datetime.strptime(download[3], '%Y-%m-%d %H:%M:%S')
        elapsed_seconds = (updated_at - created_at).total_seconds()
        if elapsed_seconds > 0 and download[1] > 0:
            seconds_remaining = (elapsed_seconds / download[1]) * (100 - download[1])
            minutes_remaining = int(seconds_remaining / 60)
            if minutes_remaining > 0:
                estimated_completion = f"About {minutes_remaining} minute(s)"
            else:
                estimated_completion = "Less than a minute"
    
    return {
        'status': download[0],
        'progress': download[1],
        'created_at': download[2],
        'updated_at': download[3],
        'file_path': download[4],
        'error_message': download[5],
        'estimated_completion': estimated_completion,
        'download_type': download[6],
        'facility_username': download[7]
    }

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'current_download_id' not in st.session_state:
    st.session_state.current_download_id = None
if 'section' not in st.session_state:
    st.session_state.section = 'login'

# CSS styling
st.markdown("""
<style>
    .main-header {
        color: #1E3A8A;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 2rem;
        text-align: center;
    }
    .section-header {
        color: #1E3A8A;
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .portal-card {
        background-color: #F3F4F6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .download-card {
        background-color: #F3F4F6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .success-text {
        color: #059669;
        font-weight: 600;
    }
    .error-text {
        color: #DC2626;
        font-weight: 600;
    }
    .info-text {
        color: #2563EB;
        font-weight: 600;
    }
    .progress-container {
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 4px 4px 0 0;
        border: 1px solid #E5E7EB;
        border-bottom: none;
        padding: 10px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #F3F4F6;
        border-bottom: 2px solid #2563EB;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
if st.session_state.logged_in:
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    
    # Navigation options
    if st.sidebar.button("📥 Download Operations"):
        st.session_state.section = 'download_operation'
    
    if st.sidebar.button("📜 Download History"):
        st.session_state.section = 'download_history'
    
    if st.sidebar.button("🔑 Credential Management"):
        st.session_state.section = 'credentials'
    
    # Admin options
    if st.session_state.is_admin:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Admin Options")
        
        if st.sidebar.button("👤 User Management"):
            st.session_state.section = 'user_management'
        
        if st.sidebar.button("🌐 Portal Configuration"):
            st.session_state.section = 'portal_config'
    
    # Logout
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.is_admin = False
        st.session_state.section = 'login'
        st.rerun()

# Main content based on selected section
if not st.session_state.logged_in:
    # Login/Register sections
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.markdown("<h1 class='main-header'>JSON Downloader Portal</h1>", unsafe_allow_html=True)
        st.markdown("<h2 class='section-header'>Login</h2>", unsafe_allow_html=True)
        
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="login_button"):
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                user = get_user_by_username(username)
                if user and check_password(password, user['password_hash']):
                    st.session_state.logged_in = True
                    st.session_state.user_id = user['id']
                    st.session_state.username = user['username']
                    st.session_state.is_admin = bool(user['is_admin'])
                    st.session_state.section = 'download_operation'
                    st.success("Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
    
    with tab2:
        st.markdown("<h1 class='main-header'>JSON Downloader Portal</h1>", unsafe_allow_html=True)
        st.markdown("<h2 class='section-header'>Register</h2>", unsafe_allow_html=True)
        
        new_username = st.text_input("Username", key="reg_username")
        new_email = st.text_input("Email", key="reg_email")
        new_password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
        
        if st.button("Register", key="register_button"):
            if not new_username or not new_email or not new_password or not confirm_password:
                st.error("Please fill out all fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                # Check if username exists
                existing_user = get_user_by_username(new_username)
                if existing_user:
                    st.error("Username already exists.")
                else:
                    # Check if this is the first user (make them admin)
                    conn = sqlite3.connect('json_downloader.db')
                    c = conn.cursor()
                    c.execute("SELECT COUNT(*) FROM users")
                    user_count = c.fetchone()[0]
                    
                    # Hash password
                    password_hash = hash_password(new_password)
                    
                    # Insert new user
                    is_admin = 1 if user_count == 0 else 0
                    c.execute(
                        "INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
                        (new_username, new_email, password_hash, is_admin)
                    )
                    
                    new_user_id = c.lastrowid
                    conn.commit()
                    conn.close()
                    
                    st.success("Registration successful! You can now log in.")
                    
                    # Auto-login
                    st.session_state.logged_in = True
                    st.session_state.user_id = new_user_id
                    st.session_state.username = new_username
                    st.session_state.is_admin = bool(is_admin)
                    st.session_state.section = 'download_operation'
                    time.sleep(1)
                    st.rerun()

elif st.session_state.section == 'download_operation':
    st.markdown("<h1 class='main-header'>JSON Downloader Portal</h1>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-header'>Download Operations</h2>", unsafe_allow_html=True)
    
    # Get user credentials
    user_credentials = get_credentials_by_user(st.session_state.user_id)
    
    if not user_credentials:
        st.warning("You don't have any credentials stored. Please add credentials first.")
        if st.button("Go to Credential Management"):
            st.session_state.section = 'credentials'
            st.rerun()
    else:
        # Download operation tabs
        download_tab1, download_tab2 = st.tabs(["Submission", "Remittance"])
        
        with download_tab1:
            st.markdown("<h3>Submission Download Parameters</h3>", unsafe_allow_html=True)
            
            # Portal selection
            credential_options = {f"{cred['portal_name']} ({cred['username']})": cred['id'] for cred in user_credentials}
            selected_credential = st.selectbox(
                "Select Portal & Credential", 
                options=list(credential_options.keys()),
                key="submission_credential"
            )
            selected_credential_id = credential_options[selected_credential]
            
            # Get selected credential details
            selected_cred = next((c for c in user_credentials if c['id'] == selected_credential_id), None)
            
            # Facility username field (prefilled with credential username)
            facility_username = st.text_input(
                "Facility Username", 
                value=selected_cred['username'] if selected_cred else "",
                help="Auto-populated from credential, but can be changed if needed.",
                key="submission_facility"
            )
            
            # Date selection
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date", 
                    value=datetime.now() - timedelta(days=7),
                    key="submission_start_date"
                )
            with col2:
                end_date = st.date_input(
                    "End Date", 
                    value=datetime.now(),
                    key="submission_end_date"
                )
            
            st.info("The system will download Submission data for the specified facility and date range.")
            
            if st.button("Schedule Submission Download", type="primary"):
                if start_date > end_date:
                    st.error("Start date cannot be after end date.")
                else:
                    download_id = schedule_download(
                        st.session_state.user_id,
                        selected_cred['portal_id'],
                        selected_credential_id,
                        facility_username,
                        'submission',
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d')
                    )
                    
                    st.session_state.current_download_id = download_id
                    st.success(f"Download scheduled successfully! Download ID: {download_id}")
        
        with download_tab2:
            st.markdown("<h3>Remittance Download Parameters</h3>", unsafe_allow_html=True)
            
            # Portal selection
            credential_options = {f"{cred['portal_name']} ({cred['username']})": cred['id'] for cred in user_credentials}
            selected_credential = st.selectbox(
                "Select Portal & Credential", 
                options=list(credential_options.keys()),
                key="remittance_credential"
            )
            selected_credential_id = credential_options[selected_credential]
            
            # Get selected credential details
            selected_cred = next((c for c in user_credentials if c['id'] == selected_credential_id), None)
            
            # Facility username field (prefilled with credential username)
            facility_username = st.text_input(
                "Facility Username", 
                value=selected_cred['username'] if selected_cred else "",
                help="Auto-populated from credential, but can be changed if needed.",
                key="remittance_facility"
            )
            
            # Date selection
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date", 
                    value=datetime.now() - timedelta(days=7),
                    key="remittance_start_date"
                )
            with col2:
                end_date = st.date_input(
                    "End Date", 
                    value=datetime.now(),
                    key="remittance_end_date"
                )
            
            st.info("The system will download Remittance data for the specified facility and date range.")
            
            if st.button("Schedule Remittance Download", type="primary"):
                if start_date > end_date:
                    st.error("Start date cannot be after end date.")
                else:
                    download_id = schedule_download(
                        st.session_state.user_id,
                        selected_cred['portal_id'],
                        selected_credential_id,
                        facility_username,
                        'remittance',
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d')
                    )
                    
                    st.session_state.current_download_id = download_id
                    st.success(f"Download scheduled successfully! Download ID: {download_id}")
        
        # Progress tracking section (show if there's an active download)
        if st.session_state.current_download_id:
            st.markdown("---")
            st.markdown("<h3>Download Progress</h3>", unsafe_allow_html=True)
            
            download_status = get_download_status(st.session_state.current_download_id)
            
            if download_status:
                # Display download info
                download_type = download_status['download_type'].capitalize()
                facility = download_status['facility_username']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"Processing {download_type} download for facility: {facility}")
                with col2:
                    st.info(f"Started at: {download_status['created_at']}")
                
                # Progress bar
                progress = download_status['progress']
                status_text = ""
                
                if download_status['status'] == 'scheduled':
                    status_text = "Scheduled and waiting to begin..."
                    bar_color = "blue"
                elif download_status['status'] == 'in_progress':
                    status_text = f"In progress... {download_status['estimated_completion'] or 'Calculating time remaining...'}"
                    bar_color = "blue"
                elif download_status['status'] == 'completed':
                    status_text = "Completed successfully!"
                    bar_color = "green"
                    progress = 100
                elif download_status['status'] == 'failed':
                    status_text = f"Failed: {download_status['error_message'] or 'Unknown error'}"
                    bar_color = "red"
                    progress = 100
                
                st.progress(progress / 100, text=f"{progress}% - {status_text}")
                
                # File download link (if completed)
                if download_status['status'] == 'completed' and download_status['file_path']:
                    if os.path.exists(download_status['file_path']):
                        with open(download_status['file_path'], 'r') as f:
                            file_data = f.read()
                        
                        st.download_button(
                            label=f"Download {download_type} Data",
                            data=file_data,
                            file_name=os.path.basename(download_status['file_path']),
                            mime="application/json",
                        )
                
                # Refresh and history buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Refresh Status"):
                        st.rerun()
                with col2:
                    if st.button("View All Downloads"):
                        st.session_state.section = 'download_history'
                        st.rerun()

elif st.session_state.section == 'download_history':
    st.markdown("<h1 class='main-header'>JSON Downloader Portal</h1>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-header'>Download History</h2>", unsafe_allow_html=True)
    
    # Get user downloads
    user_downloads = get_downloads_by_user(st.session_state.user_id)
    
    if not user_downloads:
        st.info("You haven't scheduled any downloads yet.")
    else:
        # Create a DataFrame for display
        df = pd.DataFrame(user_downloads)
        
        # Create download type filter
        download_types = ["All"] + sorted(df['download_type'].unique().tolist())
        selected_type = st.selectbox("Filter by Download Type", download_types)
        
        # Create status filter
        statuses = ["All"] + sorted(df['status'].unique().tolist())
        selected_status = st.selectbox("Filter by Status", statuses)
        
        # Apply filters
        filtered_df = df.copy()
        if selected_type != "All":
            filtered_df = filtered_df[filtered_df['download_type'] == selected_type]
        if selected_status != "All":
            filtered_df = filtered_df[filtered_df['status'] == selected_status]
        
        # Display download history
        if filtered_df.empty:
            st.info("No downloads match the selected filters.")
        else:
            # Display summary statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Downloads", len(filtered_df))
            with col2:
                completed = len(filtered_df[filtered_df['status'] == 'completed'])
                st.metric("Completed", completed)
            with col3:
                failed = len(filtered_df[filtered_df['status'] == 'failed'])
                st.metric("Failed", failed)
            
            # Create download history table
            for index, download in filtered_df.iterrows():
                with st.expander(f"{download['download_type'].capitalize()} - {download['portal_name']} - {download['created_at']}", expanded=index==0):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Portal:** {download['portal_name']}")
                        st.markdown(f"**Type:** {download['download_type'].capitalize()}")
                        st.markdown(f"**Facility:** {download['facility_username']}")
                    
                    with col2:
                        st.markdown(f"**Status:** {download['status'].capitalize()}")
                        st.markdown(f"**Date Range:** {download['start_date']} to {download['end_date']}")
                        st.markdown(f"**Created:** {download['created_at']}")
                    
                    # Progress bar
                    if download['status'] == 'in_progress':
                        st.progress(download['progress'] / 100, text=f"{download['progress']}%")
                    elif download['status'] == 'completed':
                        st.progress(1.0, text="100% - Completed")
                    elif download['status'] == 'failed':
                        st.error(f"Error: {download['error_message']}")
                    
                    # File download for completed downloads
                    if download['status'] == 'completed' and download['file_path']:
                        if os.path.exists(download['file_path']):
                            with open(download['file_path'], 'r') as f:
                                file_data = f.read()
                            
                            st.download_button(
                                label="Download JSON Data",
                                data=file_data,
                                file_name=os.path.basename(download['file_path']),
                                mime="application/json",
                                key=f"download_{download['id']}"
                            )
            
            # Visualization
            st.markdown("---")
            st.markdown("### Download Statistics")
            
            # Status chart
            status_counts = filtered_df['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            
            fig1 = px.pie(
                status_counts, 
                values='Count', 
                names='Status', 
                title='Downloads by Status',
                color='Status',
                color_discrete_map={
                    'completed': '#10B981',
                    'in_progress': '#3B82F6',
                    'scheduled': '#F59E0B',
                    'failed': '#EF4444'
                }
            )
            
            # Type chart
            type_counts = filtered_df['download_type'].value_counts().reset_index()
            type_counts.columns = ['Type', 'Count']
            
            fig2 = px.bar(
                type_counts, 
                x='Type', 
                y='Count', 
                title='Downloads by Type',
                color='Type'
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig1, use_container_width=True)
            with col2:
                st.plotly_chart(fig2, use_container_width=True)

elif st.session_state.section == 'credentials':
    st.markdown("<h1 class='main-header'>JSON Downloader Portal</h1>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-header'>Credential Management</h2>", unsafe_allow_html=True)
    
    # Get user credentials
    user_credentials = get_credentials_by_user(st.session_state.user_id)
    
    # Get available portals
    portals = get_portals()
    
    if not portals:
        st.warning("No portals are available. Please ask an administrator to add portals first.")
    else:
        # Add new credential form
        with st.expander("Add New Credential", expanded=not user_credentials):
            st.markdown("<h3>Add New Portal Credential</h3>", unsafe_allow_html=True)
            
            # Portal selection
            portal_options = {p['name']: p['id'] for p in portals}
            selected_portal = st.selectbox("Select Portal", options=list(portal_options.keys()))
            portal_id = portal_options[selected_portal]
            
            # Get selected portal details
            selected_portal_obj = next((p for p in portals if p['id'] == portal_id), None)
            if selected_portal_obj:
                st.info(f"Portal URL: {selected_portal_obj['url']}")
            
            # Credential details
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            if st.button("Save Credential"):
                if not username or not password:
                    st.error("Please enter both username and password.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    # Check if credential already exists for this portal
                    conn = sqlite3.connect('json_downloader.db')
                    c = conn.cursor()
                    c.execute(
                        "SELECT id FROM credentials WHERE user_id = ? AND portal_id = ?",
                        (st.session_state.user_id, portal_id)
                    )
                    existing = c.fetchone()
                    
                    if existing:
                        st.error("You already have credentials for this portal. Please edit the existing credential instead.")
                    else:
                        # Hash password
                        password_hash = hash_password(password)
                        
                        # Insert new credential
                        c.execute(
                            "INSERT INTO credentials (user_id, portal_id, username, password_hash) VALUES (?, ?, ?, ?)",
                            (st.session_state.user_id, portal_id, username, password_hash)
                        )
                        
                        conn.commit()
                        conn.close()
                        
                        st.success("Credential saved successfully!")
                        time.sleep(1)
                        st.rerun()
        
        # Existing credentials
        if user_credentials:
            st.markdown("<h3>Your Portal Credentials</h3>", unsafe_allow_html=True)
            
            for cred in user_credentials:
                with st.container():
                    st.markdown(
                        f"""
                        <div class="portal-card">
                            <h4>{cred['portal_name']}</h4>
                            <p><strong>URL:</strong> {cred['portal_url']}</p>
                            <p><strong>Username:</strong> {cred['username']}</p>
                            <p><strong>Last Updated:</strong> {cred['updated_at']}</p>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Edit", key=f"edit_{cred['id']}"):
                            # Show edit form for this credential
                            st.session_state[f"edit_mode_{cred['id']}"] = True
                    
                    with col2:
                        if st.button("Delete", key=f"delete_{cred['id']}"):
                            conn = sqlite3.connect('json_downloader.db')
                            c = conn.cursor()
                            c.execute("DELETE FROM credentials WHERE id = ?", (cred['id'],))
                            conn.commit()
                            conn.close()
                            st.success(f"Credential for {cred['portal_name']} deleted.")
                            time.sleep(1)
                            st.rerun()
                    
                    # Edit form (shown if edit button was clicked)
                    if st.session_state.get(f"edit_mode_{cred['id']}", False):
                        st.markdown("<h4>Edit Credential</h4>", unsafe_allow_html=True)
                        
                        new_username = st.text_input("New Username", value=cred['username'], key=f"new_username_{cred['id']}")
                        new_password = st.text_input("New Password (leave blank to keep current)", type="password", key=f"new_pw_{cred['id']}")
                        confirm_new_password = st.text_input("Confirm New Password", type="password", key=f"confirm_pw_{cred['id']}")
                        
                        update_col1, update_col2 = st.columns(2)
                        with update_col1:
                            if st.button("Update", key=f"update_{cred['id']}"):
                                conn = sqlite3.connect('json_downloader.db')
                                c = conn.cursor()
                                
                                if new_password:
                                    if new_password != confirm_new_password:
                                        st.error("Passwords do not match.")
                                    else:
                                        # Update username and password
                                        password_hash = hash_password(new_password)
                                        c.execute(
                                            "UPDATE credentials SET username = ?, password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                                            (new_username, password_hash, cred['id'])
                                        )
                                else:
                                    # Update username only
                                    c.execute(
                                        "UPDATE credentials SET username = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                                        (new_username, cred['id'])
                                    )
                                
                                conn.commit()
                                conn.close()
                                
                                st.success("Credential updated successfully!")
                                st.session_state[f"edit_mode_{cred['id']}"] = False
                                time.sleep(1)
                                st.rerun()
                        
                        with update_col2:
                            if st.button("Cancel", key=f"cancel_{cred['id']}"):
                                st.session_state[f"edit_mode_{cred['id']}"] = False
                                st.rerun()
                    
                    st.markdown("---")
        else:
            st.info("You don't have any credentials yet. Add a new credential to get started.")

elif st.session_state.section == 'portal_config' and st.session_state.is_admin:
    st.markdown("<h1 class='main-header'>JSON Downloader Portal</h1>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-header'>Portal Configuration</h2>", unsafe_allow_html=True)
    
    # Get portals
    portals = get_portals()
    
    # Add new portal form
    with st.expander("Add New Portal", expanded=not portals):
        st.markdown("<h3>Add New Portal</h3>", unsafe_allow_html=True)
        
        portal_name = st.text_input("Portal Name", key="new_portal_name")
        portal_url = st.text_input("Portal URL", key="new_portal_url")
        portal_description = st.text_area("Description (Optional)", key="new_portal_desc")
        
        if st.button("Add Portal"):
            if not portal_name or not portal_url:
                st.error("Please enter both portal name and URL.")
            else:
                conn = sqlite3.connect('json_downloader.db')
                c = conn.cursor()
                c.execute(
                    "INSERT INTO portals (name, url, description) VALUES (?, ?, ?)",
                    (portal_name, portal_url, portal_description)
                )
                conn.commit()
                conn.close()
                
                st.success("Portal added successfully!")
                time.sleep(1)
                st.rerun()
    
    # Existing portals
    if portals:
        st.markdown("<h3>Existing Portals</h3>", unsafe_allow_html=True)
        
        for portal in portals:
            with st.container():
                st.markdown(
                    f"""
                    <div class="portal-card">
                        <h4>{portal['name']}</h4>
                        <p><strong>URL:</strong> {portal['url']}</p>
                        <p><strong>Description:</strong> {portal['description'] or 'No description'}</p>
                        <p><strong>Created:</strong> {portal['created_at']}</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Edit", key=f"edit_portal_{portal['id']}"):
                        st.session_state[f"edit_portal_mode_{portal['id']}"] = True
                
                with col2:
                    if st.button("Delete", key=f"delete_portal_{portal['id']}"):
                        # Check if portal has credentials or downloads
                        conn = sqlite3.connect('json_downloader.db')
                        c = conn.cursor()
                        c.execute("SELECT COUNT(*) FROM credentials WHERE portal_id = ?", (portal['id'],))
                        cred_count = c.fetchone()[0]
                        
                        c.execute("SELECT COUNT(*) FROM downloads WHERE portal_id = ?", (portal['id'],))
                        download_count = c.fetchone()[0]
                        
                        if cred_count > 0 or download_count > 0:
                            st.error(f"Cannot delete portal. It has {cred_count} credentials and {download_count} downloads associated with it.")
                        else:
                            c.execute("DELETE FROM portals WHERE id = ?", (portal['id'],))
                            conn.commit()
                            st.success(f"Portal {portal['name']} deleted.")
                            time.sleep(1)
                            st.rerun()
                        
                        conn.close()
                
                # Edit form
                if st.session_state.get(f"edit_portal_mode_{portal['id']}", False):
                    st.markdown("<h4>Edit Portal</h4>", unsafe_allow_html=True)
                    
                    new_name = st.text_input("Portal Name", value=portal['name'], key=f"edit_name_{portal['id']}")
                    new_url = st.text_input("Portal URL", value=portal['url'], key=f"edit_url_{portal['id']}")
                    new_desc = st.text_area("Description", value=portal['description'] or "", key=f"edit_desc_{portal['id']}")
                    
                    update_col1, update_col2 = st.columns(2)
                    with update_col1:
                        if st.button("Update Portal", key=f"update_portal_{portal['id']}"):
                            if not new_name or not new_url:
                                st.error("Portal name and URL are required.")
                            else:
                                conn = sqlite3.connect('json_downloader.db')
                                c = conn.cursor()
                                c.execute(
                                    "UPDATE portals SET name = ?, url = ?, description = ? WHERE id = ?",
                                    (new_name, new_url, new_desc, portal['id'])
                                )
                                conn.commit()
                                conn.close()
                                
                                st.success("Portal updated successfully!")
                                st.session_state[f"edit_portal_mode_{portal['id']}"] = False
                                time.sleep(1)
                                st.rerun()
                    
                    with update_col2:
                        if st.button("Cancel Edit", key=f"cancel_portal_{portal['id']}"):
                            st.session_state[f"edit_portal_mode_{portal['id']}"] = False
                            st.rerun()
                
                st.markdown("---")
    else:
        st.info("No portals have been added yet. Add a new portal to get started.")

elif st.session_state.section == 'user_management' and st.session_state.is_admin:
    st.markdown("<h1 class='main-header'>JSON Downloader Portal</h1>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-header'>User Management</h2>", unsafe_allow_html=True)
    
    # Get all users
    conn = sqlite3.connect('json_downloader.db')
    c = conn.cursor()
    c.execute("SELECT id, username, email, is_admin, created_at FROM users ORDER BY created_at DESC")
    users = c.fetchall()
    conn.close()
    
    # Add new user form
    with st.expander("Add New User"):
        st.markdown("<h3>Add New User</h3>", unsafe_allow_html=True)
        
        new_username = st.text_input("Username", key="admin_new_username")
        new_email = st.text_input("Email", key="admin_new_email")
        new_password = st.text_input("Password", type="password", key="admin_new_password")
        is_admin = st.checkbox("Admin Privileges", key="admin_new_is_admin")
        
        if st.button("Add User"):
            if not new_username or not new_email or not new_password:
                st.error("Please fill out all required fields.")
            else:
                # Check if username exists
                conn = sqlite3.connect('json_downloader.db')
                c = conn.cursor()
                c.execute("SELECT id FROM users WHERE username = ?", (new_username,))
                existing = c.fetchone()
                
                if existing:
                    st.error("Username already exists.")
                else:
                    # Hash password
                    password_hash = hash_password(new_password)
                    
                    # Insert new user
                    c.execute(
                        "INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
                        (new_username, new_email, password_hash, 1 if is_admin else 0)
                    )
                    
                    conn.commit()
                    conn.close()
                    
                    st.success("User added successfully!")
                    time.sleep(1)
                    st.rerun()
    
    # Display user list
    st.markdown("<h3>User List</h3>", unsafe_allow_html=True)
    
    if users:
        for user in users:
            user_id, username, email, is_admin, created_at = user
            
            with st.container():
                st.markdown(
                    f"""
                    <div class="portal-card">
                        <h4>{username} {'(Admin)' if is_admin else ''}</h4>
                        <p><strong>Email:</strong> {email}</p>
                        <p><strong>Created:</strong> {created_at}</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Toggle Admin", key=f"toggle_{user_id}"):
                        # Cannot remove admin from yourself
                        if user_id == st.session_state.user_id and is_admin:
                            st.error("You cannot remove admin privileges from yourself.")
                        else:
                            conn = sqlite3.connect('json_downloader.db')
                            c = conn.cursor()
                            c.execute(
                                "UPDATE users SET is_admin = ? WHERE id = ?",
                                (0 if is_admin else 1, user_id)
                            )
                            conn.commit()
                            conn.close()
                            
                            st.success(f"Admin privileges {'removed from' if is_admin else 'granted to'} {username}.")
                            time.sleep(1)
                            st.rerun()
                
                with col2:
                    if st.button("Delete User", key=f"delete_user_{user_id}"):
                        # Cannot delete yourself
                        if user_id == st.session_state.user_id:
                            st.error("You cannot delete your own account.")
                        else:
                            conn = sqlite3.connect('json_downloader.db')
                            c = conn.cursor()
                            
                            # Delete user and cascade (delete credentials and downloads)
                            c.execute("DELETE FROM downloads WHERE user_id = ?", (user_id,))
                            c.execute("DELETE FROM credentials WHERE user_id = ?", (user_id,))
                            c.execute("DELETE FROM users WHERE id = ?", (user_id,))
                            
                            conn.commit()
                            conn.close()
                            
                            st.success(f"User {username} deleted successfully.")
                            time.sleep(1)
                            st.rerun()
                
                st.markdown("---")
    else:
        st.info("No users found.")

# Add an instructions section at the bottom of the main page
if st.session_state.section == 'download_operation':
    st.markdown("---")
    with st.expander("Instructions", expanded=False):
        st.markdown("""
        ## JSON Downloader Portal Instructions
        
        ### Getting Started
        1. **Register an account** if you don't have one already.
        2. **Add credentials** for the portals you need to access.
        3. **Schedule downloads** by selecting the appropriate portal and date range.
        
        ### Download Process
        1. Select the appropriate tab (Submission or Remittance) for the data you need.
        2. Choose the portal you wish to use for the download.
        3. The facility username will be auto-populated from your credential, but can be changed if needed.
        4. Specify the start and end dates for the data you want to download.
        5. Click "Schedule Download" to queue the job.
        6. The download progress will be displayed and updated automatically.
        7. View detailed history in the Download History page.
        
        ### Administrator Functions
        If you have administrator privileges:
        1. **Manage portals** - Add, edit, or remove portal configurations.
        2. **Manage users** - Add new users, grant/revoke admin privileges, or delete user accounts.
        """)
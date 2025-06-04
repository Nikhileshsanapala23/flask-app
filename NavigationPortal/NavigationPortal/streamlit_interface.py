import streamlit as st
import os
import psycopg2
import bcrypt
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor
import sys

# Add extra logging for debugging
import logging
logging.basicConfig(level=logging.INFO)
logging.info("Starting Streamlit application...")
logging.info(f"Python version: {sys.version}")
logging.info(f"Current directory: {os.getcwd()}")
logging.info(f"Environment variables: DATABASE_URL exists: {'DATABASE_URL' in os.environ}")

# Set page configuration
st.set_page_config(
    page_title="JSON Downloader Portal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection function
def get_db_connection():
    """Connect to the PostgreSQL database defined in the environment variables"""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

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
        st.error(f"Database error: {e}")
        cursor.close()
        conn.close()
        return None

def get_portals():
    """Get all portals from the database"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("SELECT * FROM portals ORDER BY name")
        portals = cursor.fetchall()
        cursor.close()
        conn.close()
        return portals
    except Exception as e:
        st.error(f"Error getting portals: {e}")
        cursor.close()
        conn.close()
        return []

def get_credentials_by_user(user_id):
    """Get credentials for a specific user"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
        SELECT c.*, p.name as portal_name, p.url as portal_url 
        FROM credentials c
        JOIN portals p ON c.portal_id = p.id
        WHERE c.user_id = %s
        """, (user_id,))
        credentials = cursor.fetchall()
        cursor.close()
        conn.close()
        return credentials
    except Exception as e:
        st.error(f"Error getting credentials: {e}")
        cursor.close()
        conn.close()
        return []

def get_downloads_by_user(user_id):
    """Get download history for a specific user"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
        SELECT d.*, p.name as portal_name, c.username as credential_username
        FROM downloads d
        JOIN portals p ON d.portal_id = p.id
        JOIN credentials c ON d.credential_id = c.id
        WHERE d.user_id = %s
        ORDER BY d.created_at DESC
        """, (user_id,))
        downloads = cursor.fetchall()
        cursor.close()
        conn.close()
        return downloads
    except Exception as e:
        st.error(f"Error getting downloads: {e}")
        cursor.close()
        conn.close()
        return []

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
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
    .card {
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
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
    
    with tab2:
        st.markdown("<h1 class='main-header'>JSON Downloader Portal</h1>", unsafe_allow_html=True)
        st.markdown("<h2 class='section-header'>Register</h2>", unsafe_allow_html=True)
        
        st.warning("Registration is temporarily disabled in this Streamlit version. Please use the main application to register.")

else:
    # User is logged in, show appropriate section
    if st.session_state.section == 'download_operation':
        st.markdown("<h1 class='main-header'>JSON Downloader Portal</h1>", unsafe_allow_html=True)
        st.markdown("<h2 class='section-header'>Download Operations</h2>", unsafe_allow_html=True)
        
        st.info("This is a Streamlit interface for the JSON Downloader Portal.")
        st.write("The full functionality is available in the main Flask application.")
        
        # Show a summary of available portals and credentials
        portals = get_portals()
        credentials = get_credentials_by_user(st.session_state.user_id)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Available Portals")
            if portals:
                for portal in portals:
                    with st.expander(portal['name']):
                        st.write(f"URL: {portal['url']}")
                        if portal['description']:
                            st.write(f"Description: {portal['description']}")
            else:
                st.warning("No portals available.")
        
        with col2:
            st.subheader("Your Credentials")
            if credentials:
                for cred in credentials:
                    st.write(f"Portal: {cred['portal_name']}")
                    st.write(f"Username: {cred['username']}")
                    st.write("---")
            else:
                st.warning("No credentials configured.")
    
    elif st.session_state.section == 'download_history':
        st.markdown("<h1 class='main-header'>JSON Downloader Portal</h1>", unsafe_allow_html=True)
        st.markdown("<h2 class='section-header'>Download History</h2>", unsafe_allow_html=True)
        
        downloads = get_downloads_by_user(st.session_state.user_id)
        
        if downloads:
            # Create a DataFrame for better display
            df = pd.DataFrame(downloads)
            
            # Format datetime columns
            for col in ['created_at', 'updated_at', 'start_date', 'end_date']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col])
            
            # Create a summary table
            summary_df = df[['id', 'portal_name', 'download_type', 'status', 'progress', 'created_at']]
            summary_df = summary_df.rename(columns={
                'id': 'ID',
                'portal_name': 'Portal',
                'download_type': 'Type',
                'status': 'Status',
                'progress': 'Progress',
                'created_at': 'Created'
            })
            
            st.dataframe(summary_df)
            
            # Create a visualization of download types
            if len(df) > 0:
                st.subheader("Download Types")
                type_counts = df['download_type'].value_counts().reset_index()
                type_counts.columns = ['Download Type', 'Count']
                
                fig = px.pie(type_counts, values='Count', names='Download Type', 
                            title='Downloads by Type')
                st.plotly_chart(fig)
                
                # Show download status breakdown
                st.subheader("Download Status")
                status_counts = df['status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                
                fig = px.bar(status_counts, x='Status', y='Count', 
                            title='Downloads by Status')
                st.plotly_chart(fig)
        else:
            st.info("No download history available.")
            
    elif st.session_state.section == 'user_management' and st.session_state.is_admin:
        st.markdown("<h1 class='main-header'>JSON Downloader Portal</h1>", unsafe_allow_html=True)
        st.markdown("<h2 class='section-header'>User Management</h2>", unsafe_allow_html=True)
        
        st.info("This feature is only available in the main application.")
        
    elif st.session_state.section == 'portal_config' and st.session_state.is_admin:
        st.markdown("<h1 class='main-header'>JSON Downloader Portal</h1>", unsafe_allow_html=True)
        st.markdown("<h2 class='section-header'>Portal Configuration</h2>", unsafe_allow_html=True)
        
        st.info("Portal configuration is only available in the main application.")
        
    elif st.session_state.section == 'credentials':
        st.markdown("<h1 class='main-header'>JSON Downloader Portal</h1>", unsafe_allow_html=True)
        st.markdown("<h2 class='section-header'>Credential Management</h2>", unsafe_allow_html=True)
        
        st.info("Credential management is only available in the main application.")
        
    # Footer with links to main application
    st.markdown("---")
    st.write("This is a simplified Streamlit interface. For full functionality, please use the main application.")
    if st.button("Go to Main Application"):
        st.write("Navigating to the main application... This would redirect to the Flask application in a production environment.")
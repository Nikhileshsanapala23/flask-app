from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    credentials = db.relationship('Credential', backref='user', lazy=True, cascade="all, delete-orphan")
    downloads = db.relationship('Download', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Portal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    credentials = db.relationship('Credential', backref='portal', lazy=True, cascade="all, delete-orphan")
    downloads = db.relationship('Download', backref='portal', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Portal {self.name}>'


class Credential(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    portal_id = db.Column(db.Integer, db.ForeignKey('portal.id'), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def get_password(self):
        # In a real application, this should be more secure
        # This is only for the demo purposes
        return self.password_hash

    def __repr__(self):
        return f'<Credential {self.username} for portal {self.portal_id}>'


class Download(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    portal_id = db.Column(db.Integer, db.ForeignKey('portal.id'), nullable=False)
    credential_id = db.Column(db.Integer, db.ForeignKey('credential.id'), nullable=False)
    facility_username = db.Column(db.String(100), nullable=True)
    download_type = db.Column(db.String(20), default='submission')  # submission, remittance
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in_progress, completed, failed
    progress = db.Column(db.Integer, default=0)  # Progress percentage (0-100)
    file_path = db.Column(db.String(255), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    credential = db.relationship('Credential', backref='downloads')

    def __repr__(self):
        return f'<Download for portal {self.portal_id} ({self.status})>'

"""
User model for authentication and permissions
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index
from sqlalchemy.orm import relationship
from flask_login import UserMixin
import bcrypt
from .base import Base


class User(Base, UserMixin):
    """
    Application users with authentication and permission settings

    Implements two-tier permission system:
    - Tier 1: has_confidential_access (business data confidentiality)
    - Tier 2: is_ned_team (internal team notes access)

    Schema matches 02_DATABASE_SCHEMA.md specification exactly
    """
    __tablename__ = 'users'

    # Primary Key
    user_id = Column(Integer, primary_key=True, autoincrement=True)

    # Authentication Fields
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(120))

    # Permission flags (two independent tiers)
    has_confidential_access = Column(Boolean, default=False, nullable=False)
    is_ned_team = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    # Account status
    created_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True, nullable=False)

    # Database selection preferences (per-user session DB selection)
    last_db_path = Column(String(500))
    last_db_display_name = Column(String(200))

    # Indexes (as specified in schema)
    __table_args__ = (
        Index('idx_users_username', 'username', unique=True),
        Index('idx_users_email', 'email', unique=True),
        Index('idx_users_active', 'is_active'),
    )

    # Flask-Login required methods
    def get_id(self):
        """Return user ID as string for Flask-Login"""
        return str(self.user_id)

    @property
    def is_authenticated(self):
        """Check if user is authenticated"""
        return True

    @property
    def is_anonymous(self):
        """Check if user is anonymous"""
        return False

    # Password methods
    def set_password(self, password):
        """
        Hash and set password using bcrypt

        Args:
            password: Plain text password
        """
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password):
        """
        Verify password using bcrypt

        Args:
            password: Plain text password to check

        Returns:
            Boolean: True if password matches
        """
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.now()

    # Permission helper methods
    def can_view_confidential(self):
        """Check if user can view confidential business data (Tier 1)"""
        return self.has_confidential_access or self.is_admin

    def can_view_ned_content(self):
        """Check if user can view NED Team internal notes (Tier 2)"""
        return self.is_ned_team or self.is_admin

    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.is_admin

    def can_manage_snapshots(self):
        """Check if user can create/restore database snapshots"""
        return self.is_admin

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self, include_sensitive=False):
        """
        Convert user to dictionary

        Args:
            include_sensitive: If False, exclude sensitive fields

        Returns:
            Dictionary representation of user
        """
        data = {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'has_confidential_access': self.has_confidential_access,
            'is_ned_team': self.is_ned_team,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }

        # Never include password hash
        return data

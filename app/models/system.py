"""
System configuration models
Matches 02_DATABASE_SCHEMA.md specification exactly
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Index
from .base import Base


class SystemSetting(Base):
    """
    Store configurable application settings

    Schema from 02_DATABASE_SCHEMA.md - System_Settings table
    Note: Does NOT use TimestampMixin - uses simple modified_by/modified_date
    """
    __tablename__ = 'system_settings'

    # Primary Key
    setting_id = Column(Integer, primary_key=True, autoincrement=True)

    # Setting Identification
    setting_name = Column(Text, unique=True, nullable=False)

    # Setting Value and Type
    setting_value = Column(Text)
    setting_type = Column(Text)  # integer, boolean, text, date
    description = Column(Text)

    # Audit fields
    modified_by = Column(Integer, ForeignKey('users.user_id'))
    modified_date = Column(DateTime)

    # Indexes (as specified in schema)
    __table_args__ = (
        Index('idx_system_settings_name', 'setting_name', unique=True),
    )

    def __repr__(self):
        return f'<SystemSetting {self.setting_name}={self.setting_value}>'

    def to_dict(self):
        return {
            'setting_id': self.setting_id,
            'setting_name': self.setting_name,
            'setting_value': self.setting_value,
            'setting_type': self.setting_type,
            'description': self.description,
            'modified_by': self.modified_by,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
        }

    def get_typed_value(self):
        """
        Get setting value converted to appropriate type

        Returns:
            Value converted to correct Python type based on setting_type
        """
        if not self.setting_value:
            return None

        if self.setting_type == 'integer':
            try:
                return int(self.setting_value)
            except (ValueError, TypeError):
                return None
        elif self.setting_type == 'boolean':
            return self.setting_value.lower() in ('true', '1', 'yes', 'on')
        elif self.setting_type == 'date':
            try:
                from dateutil.parser import parse
                return parse(self.setting_value)
            except:
                return None
        else:  # text
            return self.setting_value


class SchemaVersion(Base):
    """
    Track database schema version for migrations

    Schema from 02_DATABASE_SCHEMA.md - Schema_Version table
    Note: Does NOT use TimestampMixin - simple append-only table
    """
    __tablename__ = 'schema_version'

    # Primary Key (version number itself)
    version = Column(Integer, primary_key=True)

    # Migration Information
    applied_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    applied_by = Column(Text)  # 'system', username, etc.
    description = Column(Text)

    def __repr__(self):
        return f'<SchemaVersion {self.version}>'

    def to_dict(self):
        return {
            'version': self.version,
            'applied_date': self.applied_date.isoformat() if self.applied_date else None,
            'applied_by': self.applied_by,
            'description': self.description,
        }

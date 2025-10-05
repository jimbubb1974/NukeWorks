"""
Database Snapshot model for backup management
Matches 02_DATABASE_SCHEMA.md specification exactly
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, Boolean, ForeignKey, Index
from .base import Base


class DatabaseSnapshot(Base):
    """
    Track database backup/snapshot metadata

    Schema from 02_DATABASE_SCHEMA.md - Database_Snapshots table
    Note: Does NOT use TimestampMixin - snapshot_timestamp serves that purpose
    """
    __tablename__ = 'database_snapshots'

    # Primary Key
    snapshot_id = Column(Integer, primary_key=True, autoincrement=True)

    # When and By Whom
    snapshot_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey('users.user_id'))  # NULL if automated

    # Snapshot Classification
    snapshot_type = Column(Text)  # MANUAL, AUTOMATED_DAILY, AUTOMATED_WEEKLY

    # File Information
    file_path = Column(Text, nullable=False)
    description = Column(Text)
    snapshot_size_bytes = Column(Integer)

    # Retention
    is_retained = Column(Boolean, default=False, nullable=False)  # Prevent auto-delete

    # Indexes (as specified in schema)
    __table_args__ = (
        Index('idx_snapshots_timestamp', 'snapshot_timestamp'),
        Index('idx_snapshots_type', 'snapshot_type'),
        Index('idx_snapshots_retained', 'is_retained'),
    )

    def __repr__(self):
        return f'<DatabaseSnapshot {self.snapshot_type} at {self.snapshot_timestamp}>'

    def to_dict(self):
        return {
            'snapshot_id': self.snapshot_id,
            'snapshot_timestamp': self.snapshot_timestamp.isoformat() if self.snapshot_timestamp else None,
            'created_by_user_id': self.created_by_user_id,
            'snapshot_type': self.snapshot_type,
            'file_path': self.file_path,
            'description': self.description,
            'snapshot_size_bytes': self.snapshot_size_bytes,
            'is_retained': self.is_retained,
        }

"""
Audit Log model for tracking all data changes
Matches 02_DATABASE_SCHEMA.md specification exactly
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Index
from .base import Base


class AuditLog(Base):
    """
    Track all CREATE, UPDATE, DELETE operations

    Schema from 02_DATABASE_SCHEMA.md - Audit_Log table
    Note: Does NOT use TimestampMixin - this IS the audit trail
    """
    __tablename__ = 'audit_log'

    # Primary Key
    log_id = Column(Integer, primary_key=True, autoincrement=True)

    # Who and When
    user_id = Column(Integer, ForeignKey('users.user_id'))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # What Operation
    action = Column(Text, nullable=False)  # CREATE, UPDATE, DELETE

    # Which Record
    table_name = Column(Text, nullable=False)
    record_id = Column(Integer)

    # What Changed
    field_name = Column(Text)
    old_value = Column(Text)
    new_value = Column(Text)

    # Optional notes
    notes = Column(Text)

    # Indexes (as specified in schema)
    __table_args__ = (
        Index('idx_audit_log_user', 'user_id'),
        Index('idx_audit_log_timestamp', 'timestamp'),
        Index('idx_audit_log_action', 'action'),
        Index('idx_audit_log_table', 'table_name'),
        Index('idx_audit_log_record', 'table_name', 'record_id'),
    )

    def __repr__(self):
        return f'<AuditLog {self.action} {self.table_name}:{self.record_id} by user {self.user_id}>'

    def to_dict(self):
        return {
            'log_id': self.log_id,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'action': self.action,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'field_name': self.field_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'notes': self.notes,
        }

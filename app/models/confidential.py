"""
Confidential Field Flags model for Tier 1 permissions
Matches 02_DATABASE_SCHEMA.md specification exactly
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Text, Boolean, DateTime, ForeignKey, Index
from .base import Base


class ConfidentialFieldFlag(Base):
    """
    Mark specific fields as confidential on a per-record basis

    Schema from 02_DATABASE_SCHEMA.md - Confidential_Field_Flags table
    Note: Does NOT use TimestampMixin - uses simple marked_by/marked_date
    """
    __tablename__ = 'confidential_field_flags'

    # Primary Key
    flag_id = Column(Integer, primary_key=True, autoincrement=True)

    # Which field is confidential
    table_name = Column(Text, nullable=False)
    record_id = Column(Integer, nullable=False)
    field_name = Column(Text, nullable=False)

    # Confidentiality flag
    is_confidential = Column(Boolean, default=True, nullable=False)

    # Audit fields
    marked_by = Column(Integer, ForeignKey('users.user_id'))
    marked_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes (as specified in schema)
    __table_args__ = (
        Index('idx_conf_flags_table_record', 'table_name', 'record_id'),
        Index('idx_conf_flags_field', 'field_name'),
    )

    def __repr__(self):
        return f'<ConfidentialFieldFlag {self.table_name}.{self.field_name} for record {self.record_id}>'

    def to_dict(self):
        return {
            'flag_id': self.flag_id,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'field_name': self.field_name,
            'is_confidential': self.is_confidential,
            'marked_by': self.marked_by,
            'marked_date': self.marked_date.isoformat() if self.marked_date else None,
        }

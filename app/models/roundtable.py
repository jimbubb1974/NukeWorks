"""
Roundtable History model (NED Team only)
Matches 02_DATABASE_SCHEMA.md specification exactly
"""
from sqlalchemy import Column, Integer, Text, Date, ForeignKey, Index
from .base import Base


class RoundtableHistory(Base):
    """
    Internal meeting notes about clients (NED Team only access)
    Limited to N most recent entries per entity (configurable via System Settings)

    Schema from 02_DATABASE_SCHEMA.md - Roundtable_History table
    Note: Does NOT use TimestampMixin - uses simpler audit fields
    """
    __tablename__ = 'roundtable_history'

    # Primary Key
    history_id = Column(Integer, primary_key=True, autoincrement=True)

    # Polymorphic Entity Reference
    entity_type = Column(Text, nullable=False)  # Owner, Project, etc.
    entity_id = Column(Integer, nullable=False)

    # Meeting Information
    meeting_date = Column(Date, nullable=False)
    discussion = Column(Text)
    action_items = Column(Text)

    # CRM-specific fields (added in migration 003)
    next_steps = Column(Text)  # Next steps for this client
    client_near_term_focus = Column(Text)  # What the client is focusing on
    mpr_work_targets = Column(Text)  # MPR's goals/targets for this client

    # Audit fields (simpler than TimestampMixin - entries are append-only)
    created_by = Column(Integer, ForeignKey('users.user_id'))
    created_date = Column(Date, nullable=False)

    # Indexes (as specified in schema)
    __table_args__ = (
        Index('idx_roundtable_entity', 'entity_type', 'entity_id'),
        Index('idx_roundtable_meeting_date', 'meeting_date'),
    )

    def __repr__(self):
        return f'<RoundtableHistory {self.entity_type}:{self.entity_id} on {self.meeting_date}>'

    def to_dict(self):
        """Convert to dictionary (only accessible to NED Team)"""
        return {
            'history_id': self.history_id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'meeting_date': self.meeting_date.isoformat() if self.meeting_date else None,
            'discussion': self.discussion,
            'action_items': self.action_items,
            'next_steps': self.next_steps,
            'client_near_term_focus': self.client_near_term_focus,
            'mpr_work_targets': self.mpr_work_targets,
            'created_by': self.created_by,
            'created_date': self.created_date.isoformat() if self.created_date else None,
        }

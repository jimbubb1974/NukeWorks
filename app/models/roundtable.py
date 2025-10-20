"""
Roundtable History model (NED Team only)
Matches 02_DATABASE_SCHEMA.md specification exactly

NOTE: All discussion/notes fields are encrypted (NED Team only access).
"""
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Index, LargeBinary
from datetime import datetime
from .base import Base
from app.utils.encryption import EncryptedField


class RoundtableHistory(Base):
    """
    Internal meeting notes about clients (NED Team only access)
    Limited to N most recent entries per entity (configurable via System Settings)

    Schema from 02_DATABASE_SCHEMA.md - Roundtable_History table
    Note: Does NOT use TimestampMixin - uses simpler audit fields

    NOTE: All content fields are encrypted (NED Team only access).
    """
    __tablename__ = 'roundtable_history'

    # Primary Key
    history_id = Column(Integer, primary_key=True, autoincrement=True)

    # Polymorphic Entity Reference (plain text - needed for queries)
    entity_type = Column(Text, nullable=False)  # Owner, Project, etc.
    entity_id = Column(Integer, nullable=False)

    # Encrypted NED Team fields (all meeting content)
    _discussion_encrypted = Column('discussion_encrypted', LargeBinary)
    _action_items_encrypted = Column('action_items_encrypted', LargeBinary)
    _next_steps_encrypted = Column('next_steps_encrypted', LargeBinary)
    _client_near_term_focus_encrypted = Column('client_near_term_focus_encrypted', LargeBinary)
    _mpr_work_targets_encrypted = Column('mpr_work_targets_encrypted', LargeBinary)
    _client_strategic_objectives_encrypted = Column('client_strategic_objectives_encrypted', LargeBinary)

    # Properties with automatic encryption/decryption
    discussion = EncryptedField('_discussion_encrypted', 'ned_team', '[NED Team Only]')
    action_items = EncryptedField('_action_items_encrypted', 'ned_team', '[NED Team Only]')
    next_steps = EncryptedField('_next_steps_encrypted', 'ned_team', '[NED Team Only]')
    client_near_term_focus = EncryptedField('_client_near_term_focus_encrypted', 'ned_team', '[NED Team Only]')
    mpr_work_targets = EncryptedField('_mpr_work_targets_encrypted', 'ned_team', '[NED Team Only]')
    client_strategic_objectives = EncryptedField('_client_strategic_objectives_encrypted', 'ned_team', '[NED Team Only]')

    # Audit fields (plain text - simpler than TimestampMixin - entries are append-only)
    created_by = Column(Integer, ForeignKey('users.user_id'))
    created_timestamp = Column(DateTime, nullable=False, default=datetime.now)

    # Indexes (as specified in schema)
    __table_args__ = (
        Index('idx_roundtable_entity', 'entity_type', 'entity_id'),
        Index('idx_roundtable_created', 'created_timestamp'),
    )

    def __repr__(self):
        return f'<RoundtableHistory {self.entity_type}:{self.entity_id} at {self.created_timestamp}>'

    def to_dict(self):
        """Convert to dictionary (only accessible to NED Team)"""
        return {
            'history_id': self.history_id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'discussion': self.discussion,
            'action_items': self.action_items,
            'next_steps': self.next_steps,
            'client_near_term_focus': self.client_near_term_focus,
            'mpr_work_targets': self.mpr_work_targets,
            'client_strategic_objectives': self.client_strategic_objectives,
            'created_by': self.created_by,
            'created_timestamp': self.created_timestamp.isoformat() if self.created_timestamp else None,
        }

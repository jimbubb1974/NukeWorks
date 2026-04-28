"""
Research workflow models — import runs and staged review queue.
"""
import json
from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Index
from .base import Base


class ResearchImportRun(Base):
    __tablename__ = 'research_import_runs'

    run_id         = Column(Integer, primary_key=True, autoincrement=True)
    run_name       = Column(Text, nullable=False)
    created_at     = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by     = Column(Integer, ForeignKey('users.user_id'))
    status         = Column(Text, nullable=False, default='in_progress')
    chunk_count    = Column(Integer, nullable=False, default=1)
    total_items    = Column(Integer, nullable=False, default=0)
    accepted_items = Column(Integer, nullable=False, default=0)
    skipped_items  = Column(Integer, nullable=False, default=0)

    @property
    def pending_items(self):
        return self.total_items - self.accepted_items - self.skipped_items

    @property
    def is_complete(self):
        return self.status == 'complete'


class ResearchQueueItem(Base):
    __tablename__ = 'research_queue_items'
    __table_args__ = (
        Index('idx_research_queue_run', 'run_id'),
        Index('idx_research_queue_status', 'run_id', 'status'),
    )

    item_id       = Column(Integer, primary_key=True, autoincrement=True)
    run_id        = Column(Integer, ForeignKey('research_import_runs.run_id'), nullable=False)
    entity_type   = Column(Text, nullable=False)   # company, project, relationship
    entity_db_id  = Column(Integer)                # null for new entities
    entity_name   = Column(Text, nullable=False)
    change_type   = Column(Text, nullable=False)   # new, update, conflict
    proposed_data = Column(Text, nullable=False)   # JSON blob
    current_data  = Column(Text)                   # JSON blob, null for new entities
    changed_fields = Column(Text)                  # JSON array of field names
    source_urls   = Column(Text)                   # JSON array of URLs
    status        = Column(Text, nullable=False, default='pending')
    reviewed_at   = Column(DateTime)
    reviewed_by   = Column(Integer, ForeignKey('users.user_id'))
    review_notes  = Column(Text)

    def get_proposed(self):
        return json.loads(self.proposed_data) if self.proposed_data else {}

    def get_current(self):
        return json.loads(self.current_data) if self.current_data else {}

    def get_changed_fields(self):
        return json.loads(self.changed_fields) if self.changed_fields else []

    def get_source_urls(self):
        return json.loads(self.source_urls) if self.source_urls else []

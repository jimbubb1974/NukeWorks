"""
Company document attachments. File bytes live on disk; this holds metadata.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from .base import Base

ACCESS_LEVELS = ('standard', 'confidential', 'ned')
CATEGORIES = ('Org Chart', 'Presentation', 'Contract', 'Report', 'Other')


class CompanyDocument(Base):
    __tablename__ = 'company_documents'
    __table_args__ = (
        Index('idx_company_documents_company', 'company_id', 'is_deleted'),
    )

    document_id       = Column(Integer, primary_key=True, autoincrement=True)
    company_id        = Column(Integer, ForeignKey('companies.company_id'), nullable=False)
    title             = Column(Text, nullable=False)
    description       = Column(Text)
    category          = Column(Text)
    access_level      = Column(Text, nullable=False, default='standard')  # standard | confidential | ned
    original_filename = Column(Text, nullable=False)
    stored_filename   = Column(Text, nullable=False, unique=True)
    mime_type         = Column(Text)
    size_bytes        = Column(Integer, nullable=False, default=0)
    sha256            = Column(Text)
    uploaded_by       = Column(Integer, ForeignKey('users.user_id'))
    uploaded_at       = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_deleted        = Column(Integer, nullable=False, default=0)
    deleted_at        = Column(DateTime)
    deleted_by        = Column(Integer, ForeignKey('users.user_id'))

    company  = relationship('Company', backref='documents')
    uploader = relationship('User', foreign_keys=[uploaded_by])

    @property
    def is_image(self):
        return (self.mime_type or '').startswith('image/')

    @property
    def is_pdf(self):
        return self.mime_type == 'application/pdf'

    @property
    def is_inline(self):
        return self.is_image or self.is_pdf

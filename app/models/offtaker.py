"""Energy off-taker model"""
from sqlalchemy import Column, Integer, Text, Index
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Offtaker(Base, TimestampMixin):
    """Organizations purchasing energy output (e.g., Amazon, Google)."""

    __tablename__ = 'offtakers'

    offtaker_id = Column(Integer, primary_key=True, autoincrement=True)
    organization_name = Column(Text, nullable=False)
    sector = Column(Text)
    notes = Column(Text)

    __table_args__ = (
        Index('idx_offtaker_name', 'organization_name'),
    )

    project_relationships = relationship(
        'ProjectOfftakerRelationship',
        back_populates='offtaker',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Offtaker {self.organization_name}>'

    def to_dict(self):
        return {
            'offtaker_id': self.offtaker_id,
            'organization_name': self.organization_name,
            'sector': self.sector,
            'notes': self.notes,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
            'created_by': self.created_by,
            'modified_by': self.modified_by,
        }

"""Personnel relationship models for linking internal and external personnel."""
from sqlalchemy import Column, Integer, Text, Boolean, Index, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class PersonnelRelationship(Base, TimestampMixin):
    """Relationship between internal and external personnel."""
    __tablename__ = 'personnel_relationships'
    
    relationship_id = Column(Integer, primary_key=True, autoincrement=True)
    internal_personnel_id = Column(Integer, ForeignKey('internal_personnel.personnel_id'), nullable=False)
    external_personnel_id = Column(Integer, ForeignKey('external_personnel.personnel_id'), nullable=False)
    relationship_type = Column(Text)  # e.g., 'Primary Contact', 'Technical Contact', 'Business Contact'
    notes = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_personnel_relationships_internal', 'internal_personnel_id'),
        Index('idx_personnel_relationships_external', 'external_personnel_id'),
        Index('idx_personnel_relationships_type', 'relationship_type'),
        Index('idx_personnel_relationships_active', 'is_active'),
    )
    
    # Relationships
    internal_personnel = relationship('InternalPersonnel', back_populates='external_relationships')
    external_personnel = relationship('ExternalPersonnel', back_populates='internal_relationships')
    
    def to_dict(self):
        return {
            'relationship_id': self.relationship_id,
            'internal_personnel_id': self.internal_personnel_id,
            'external_personnel_id': self.external_personnel_id,
            'relationship_type': self.relationship_type,
            'notes': self.notes,
            'is_active': self.is_active,
            'internal_personnel_name': self.internal_personnel.full_name if self.internal_personnel else None,
            'external_personnel_name': self.external_personnel.full_name if self.external_personnel else None,
        }

"""
Constructor model
Matches 02_DATABASE_SCHEMA.md specification exactly
"""
from sqlalchemy import Column, Integer, Text, Index
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Constructor(Base, TimestampMixin):
    """
    Construction companies that build nuclear facilities

    Schema from 02_DATABASE_SCHEMA.md - Constructors table
    """
    __tablename__ = 'constructors'

    # Primary Key
    constructor_id = Column(Integer, primary_key=True, autoincrement=True)

    # Fields
    company_name = Column(Text, nullable=False)
    notes = Column(Text)

    # Indexes (as specified in schema)
    __table_args__ = (
        Index('idx_constructors_name', 'company_name'),
    )

    # Relationships
    project_relationships = relationship(
        'ProjectConstructorRelationship',
        back_populates='constructor',
        cascade='all, delete-orphan'
    )

    vendor_preferences = relationship(
        'VendorPreferredConstructor',
        back_populates='constructor',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Constructor {self.company_name}>'

    def to_dict(self):
        return {
            'constructor_id': self.constructor_id,
            'company_name': self.company_name,
            'notes': self.notes,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
            'created_by': self.created_by,
            'modified_by': self.modified_by,
        }

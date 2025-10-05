"""
Personnel model
Matches 02_DATABASE_SCHEMA.md specification exactly
"""
from sqlalchemy import Column, Integer, Text, Boolean, Index
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Personnel(Base, TimestampMixin):
    """
    People - both internal team members and external contacts

    Schema from 02_DATABASE_SCHEMA.md - Personnel table
    """
    __tablename__ = 'personnel'

    # Primary Key
    personnel_id = Column(Integer, primary_key=True, autoincrement=True)

    # Required Fields
    full_name = Column(Text, nullable=False)

    # Contact Information
    email = Column(Text)
    phone = Column(Text)
    role = Column(Text)  # Job title/role

    # Personnel Classification
    personnel_type = Column(Text)  # Internal, Client_Contact, Vendor_Contact, etc.

    # For external contacts - link to organization
    organization_id = Column(Integer)  # Generic ID (no FK constraint - polymorphic)
    organization_type = Column(Text)  # Owner, Vendor, Constructor, Operator

    # Status and Notes
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text)

    # Indexes (as specified in schema)
    __table_args__ = (
        Index('idx_personnel_name', 'full_name'),
        Index('idx_personnel_type', 'personnel_type'),
        Index('idx_personnel_email', 'email'),
        Index('idx_personnel_active', 'is_active'),
    )

    # Relationships
    entity_relationships = relationship(
        'PersonnelEntityRelationship',
        back_populates='person',
        cascade='all, delete-orphan'
    )

    team_assignments = relationship(
        'EntityTeamMember',
        back_populates='person',
        cascade='all, delete-orphan'
    )

    contact_logs_as_contactor = relationship(
        'ContactLog',
        foreign_keys='ContactLog.contacted_by',
        backref='contacted_by_person'
    )

    contact_logs_as_contact = relationship(
        'ContactLog',
        foreign_keys='ContactLog.contact_person_id',
        backref='contact_person'
    )

    def __repr__(self):
        return f'<Personnel {self.full_name}>'

    def to_dict(self):
        return {
            'personnel_id': self.personnel_id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'personnel_type': self.personnel_type,
            'organization_id': self.organization_id,
            'organization_type': self.organization_type,
            'is_active': self.is_active,
            'notes': self.notes,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
            'created_by': self.created_by,
            'modified_by': self.modified_by,
        }

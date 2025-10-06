"""
External Personnel model
For people who work for other companies
"""
from sqlalchemy import Column, Integer, Text, Boolean, Index, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class ExternalPersonnel(Base, TimestampMixin):
    """
    External contacts who work for other companies
    """
    __tablename__ = 'external_personnel'

    # Primary Key
    personnel_id = Column(Integer, primary_key=True, autoincrement=True)

    # Required Fields
    full_name = Column(Text, nullable=False)
    email = Column(Text)
    phone = Column(Text)
    role = Column(Text)  # Job title/role at their company

    # Company Relationship
    company_id = Column(Integer, ForeignKey('companies.company_id'), nullable=False)

    # Contact Classification
    contact_type = Column(Text)  # Primary, Secondary, Technical, etc.

    # Status and Notes
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text)

    # Indexes
    __table_args__ = (
        Index('idx_external_personnel_name', 'full_name'),
        Index('idx_external_personnel_email', 'email'),
        Index('idx_external_personnel_active', 'is_active'),
        Index('idx_external_personnel_company', 'company_id'),
        Index('idx_external_personnel_type', 'contact_type'),
    )

    # Relationships
    company = relationship('Company', back_populates='external_personnel')
    
    # Note: PersonnelEntityRelationship will be updated separately
    # entity_relationships = relationship(
    #     'PersonnelEntityRelationship',
    #     back_populates='person',
    #     cascade='all, delete-orphan'
    # )

    # Note: ContactLog relationships will be updated separately
    # contact_logs_as_contact = relationship(
    #     'ContactLog',
    #     foreign_keys='ContactLog.contact_person_id',
    #     backref='contact_person'
    # )

    def __repr__(self):
        return f'<ExternalPersonnel {self.full_name}>'

    def to_dict(self):
        return {
            'personnel_id': self.personnel_id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'company_id': self.company_id,
            'company_name': self.company.company_name if self.company else None,
            'contact_type': self.contact_type,
            'is_active': self.is_active,
            'notes': self.notes,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
            'created_by': self.created_by,
            'modified_by': self.modified_by,
        }

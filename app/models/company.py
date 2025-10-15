"""Unified company and relationship models for refactor

NOTE: ClientProfile and InternalExternalLink contain encrypted NED Team fields.
"""
from sqlalchemy import (
    Column,
    Integer,
    Text,
    Boolean,
    Date,
    ForeignKey,
    UniqueConstraint,
    Index,
    LargeBinary,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin
from app.utils.encryption import EncryptedField


class Company(Base, TimestampMixin):
    """Core company record, replacing role-specific tables."""

    __tablename__ = 'companies'

    company_id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(Text, nullable=False)
    company_type = Column(Text)  # Utility, IPP, Vendor, Constructor, etc.
    website = Column(Text)
    headquarters_country = Column(Text)
    is_mpr_client = Column(Boolean, default=False, nullable=False)
    is_internal = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)

    __table_args__ = (
        UniqueConstraint('company_name', name='uq_companies_name'),
        Index('idx_companies_name', 'company_name'),
        Index('idx_companies_type', 'company_type'),
        Index('idx_companies_mpr_client', 'is_mpr_client'),
    )

    # Relationships
    client_profile = relationship(
        'ClientProfile',
        uselist=False,
        back_populates='company',
        cascade='all, delete-orphan'
    )

    role_assignments = relationship(
        'CompanyRoleAssignment',
        back_populates='company',
        cascade='all, delete-orphan'
    )

    affiliations = relationship(
        'PersonCompanyAffiliation',
        back_populates='company',
        cascade='all, delete-orphan'
    )

    # products = relationship(  # Removed in Phase 4 cleanup - Product model no longer exists
    #     'Product',
    #     back_populates='company',
    #     cascade='all, delete-orphan'
    # )

    external_personnel = relationship(
        'ExternalPersonnel',
        back_populates='company',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f'<Company {self.company_name}>'

    def to_dict(self):
        """Serialize basic company fields (for future API use)."""
        return {
            'company_id': self.company_id,
            'company_name': self.company_name,
            'company_type': self.company_type,
            'website': self.website,
            'headquarters_country': self.headquarters_country,
            'is_mpr_client': self.is_mpr_client,
            'is_internal': self.is_internal,
            'notes': self.notes,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
            'created_by': self.created_by,
            'modified_by': self.modified_by,
        }


class CompanyRole(Base, TimestampMixin):
    """Catalog of available company roles (vendor, constructor, operator, etc.)."""

    __tablename__ = 'company_roles'

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_code = Column(Text, nullable=False, unique=True)
    role_label = Column(Text, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)

    assignments = relationship(
        'CompanyRoleAssignment',
        back_populates='role'
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f'<CompanyRole {self.role_code}>'


class CompanyRoleAssignment(Base, TimestampMixin):
    """Contextual role assignment for a company (optionally tied to a project or other entity)."""

    __tablename__ = 'company_role_assignments'

    assignment_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.company_id'), nullable=False)
    role_id = Column(Integer, ForeignKey('company_roles.role_id'), nullable=False)

    context_type = Column(Text)  # e.g., Project, Opportunity, Global
    context_id = Column(Integer)  # ID of the related entity when applicable
    is_primary = Column(Boolean, default=False, nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    is_confidential = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)

    __table_args__ = (
        UniqueConstraint('company_id', 'role_id', 'context_type', 'context_id', name='uq_company_role_context'),
        Index('idx_company_role_company', 'company_id'),
        Index('idx_company_role_role', 'role_id'),
        Index('idx_company_role_context', 'context_type', 'context_id'),
        Index('idx_company_role_primary', 'is_primary'),
    )

    company = relationship('Company', back_populates='role_assignments')
    role = relationship('CompanyRole', back_populates='assignments')

    def __repr__(self) -> str:  # pragma: no cover
        return f'<CompanyRoleAssignment company:{self.company_id} role:{self.role_id}>'


class ClientProfile(Base, TimestampMixin):
    """Extended CRM view for MPR clients.

    NOTE: Relationship assessment fields are encrypted (NED Team only access).
    """

    __tablename__ = 'client_profiles'

    company_id = Column(Integer, ForeignKey('companies.company_id'), primary_key=True)

    # Encrypted NED Team fields (internal relationship assessments)
    _relationship_strength_encrypted = Column('relationship_strength_encrypted', LargeBinary)
    _relationship_notes_encrypted = Column('relationship_notes_encrypted', LargeBinary)
    _client_priority_encrypted = Column('client_priority_encrypted', LargeBinary)
    _client_status_encrypted = Column('client_status_encrypted', LargeBinary)

    # Properties with automatic encryption/decryption
    relationship_strength = EncryptedField('_relationship_strength_encrypted', 'ned_team', '[NED Team Only]')
    relationship_notes = EncryptedField('_relationship_notes_encrypted', 'ned_team', '[NED Team Only]')
    client_priority = EncryptedField('_client_priority_encrypted', 'ned_team', '[NED Team Only]')
    client_status = EncryptedField('_client_status_encrypted', 'ned_team', '[NED Team Only]')

    # Plain text fields (contact tracking)
    last_contact_date = Column(Date)
    last_contact_type = Column(Text)
    last_contact_by = Column(Integer, ForeignKey('personnel.personnel_id'))
    next_planned_contact_date = Column(Date)
    next_planned_contact_type = Column(Text)
    next_planned_contact_assigned_to = Column(Integer, ForeignKey('personnel.personnel_id'))

    company = relationship('Company', back_populates='client_profile')
    last_contacted_by_person = relationship(
        'Personnel',
        foreign_keys=[last_contact_by],
        backref='client_profiles_last_contacted'
    )
    next_contact_assigned_person = relationship(
        'Personnel',
        foreign_keys=[next_planned_contact_assigned_to],
        backref='client_profiles_assigned_next_contact'
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f'<ClientProfile company:{self.company_id}>'


class PersonCompanyAffiliation(Base, TimestampMixin):
    """Normalized link between personnel and companies."""

    __tablename__ = 'person_company_affiliations'

    affiliation_id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(Integer, ForeignKey('personnel.personnel_id'), nullable=False)
    company_id = Column(Integer, ForeignKey('companies.company_id'), nullable=False)
    title = Column(Text)
    department = Column(Text)
    is_primary = Column(Boolean, default=False, nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    notes = Column(Text)

    __table_args__ = (
        UniqueConstraint('person_id', 'company_id', 'title', 'start_date', name='uq_person_company_role'),
        Index('idx_person_company_person', 'person_id'),
        Index('idx_person_company_company', 'company_id'),
        Index('idx_person_company_primary', 'is_primary'),
    )

    person = relationship('Personnel', backref='company_affiliations')
    company = relationship('Company', back_populates='affiliations')

    def __repr__(self) -> str:  # pragma: no cover
        return f'<PersonCompanyAffiliation person:{self.person_id} company:{self.company_id}>'


class InternalExternalLink(Base, TimestampMixin):
    """Relationship mapping between internal personnel and external contacts.

    NOTE: Relationship assessments are encrypted (NED Team only access).
    """

    __tablename__ = 'internal_external_links'

    link_id = Column(Integer, primary_key=True, autoincrement=True)
    internal_person_id = Column(Integer, ForeignKey('personnel.personnel_id'), nullable=False)
    external_person_id = Column(Integer, ForeignKey('personnel.personnel_id'), nullable=False)
    company_id = Column(Integer, ForeignKey('companies.company_id'))
    relationship_type = Column(Text)

    # Encrypted NED Team fields (internal assessments)
    _relationship_strength_encrypted = Column('relationship_strength_encrypted', LargeBinary)
    _notes_encrypted = Column('notes_encrypted', LargeBinary)

    # Properties with automatic encryption/decryption
    relationship_strength = EncryptedField('_relationship_strength_encrypted', 'ned_team', '[NED Team Only]')
    notes = EncryptedField('_notes_encrypted', 'ned_team', '[NED Team Only]')

    __table_args__ = (
        UniqueConstraint('internal_person_id', 'external_person_id', 'company_id', name='uq_internal_external_company'),
        Index('idx_internal_external_internal', 'internal_person_id'),
        Index('idx_internal_external_external', 'external_person_id'),
        Index('idx_internal_external_company', 'company_id'),
    )

    internal_person = relationship(
        'Personnel',
        foreign_keys=[internal_person_id],
        backref='external_relationships'
    )
    external_person = relationship(
        'Personnel',
        foreign_keys=[external_person_id],
        backref='internal_relationships'
    )
    company = relationship('Company')

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f'<InternalExternalLink internal:{self.internal_person_id} '
            f'external:{self.external_person_id} company:{self.company_id}>'
        )

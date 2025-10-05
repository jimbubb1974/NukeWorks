"""
Junction tables for many-to-many relationships
Matches 03_DATABASE_RELATIONSHIPS.md specification exactly

All junction tables include:
- is_confidential flag for Tier 1 permissions
- Proper foreign keys with constraints
- Indexes as specified
- Audit fields via TimestampMixin
"""
from sqlalchemy import Column, Integer, Text, Date, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class VendorSupplierRelationship(Base, TimestampMixin):
    """
    Track which vendors supply components to other vendors

    Schema from 03_DATABASE_RELATIONSHIPS.md
    """
    __tablename__ = 'vendor_supplier_relationships'

    # Primary Key
    relationship_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    vendor_id = Column(Integer, ForeignKey('technology_vendors.vendor_id'), nullable=False)
    supplier_id = Column(Integer, ForeignKey('technology_vendors.vendor_id'), nullable=False)

    # Fields
    component_type = Column(Text)  # major_component, minor_component, etc.
    is_confidential = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)

    # Indexes and Constraints (as specified in schema)
    __table_args__ = (
        Index('idx_vendor_supplier_vendor', 'vendor_id'),
        Index('idx_vendor_supplier_supplier', 'supplier_id'),
        Index('idx_vendor_supplier_conf', 'is_confidential'),
        UniqueConstraint('vendor_id', 'supplier_id', name='uq_vendor_supplier'),
    )

    # Relationships
    vendor = relationship('TechnologyVendor', foreign_keys=[vendor_id], back_populates='supplier_relationships')
    supplier = relationship('TechnologyVendor', foreign_keys=[supplier_id], back_populates='as_supplier_relationships')

    def __repr__(self):
        return f'<VendorSupplierRelationship vendor:{self.vendor_id} supplier:{self.supplier_id}>'


class OwnerVendorRelationship(Base, TimestampMixin):
    """
    Track agreements between owners/developers and technology vendors

    Schema from 03_DATABASE_RELATIONSHIPS.md
    """
    __tablename__ = 'owner_vendor_relationships'

    # Primary Key
    relationship_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    owner_id = Column(Integer, ForeignKey('owners_developers.owner_id'), nullable=False)
    vendor_id = Column(Integer, ForeignKey('technology_vendors.vendor_id'), nullable=False)

    # Fields
    relationship_type = Column(Text)  # MOU, Development_Agreement, Delivery_Contract
    is_confidential = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)

    # Indexes and Constraints (as specified in schema)
    __table_args__ = (
        Index('idx_owner_vendor_owner', 'owner_id'),
        Index('idx_owner_vendor_vendor', 'vendor_id'),
        Index('idx_owner_vendor_type', 'relationship_type'),
        Index('idx_owner_vendor_conf', 'is_confidential'),
        UniqueConstraint('owner_id', 'vendor_id', 'relationship_type', name='uq_owner_vendor_type'),
    )

    # Relationships
    owner = relationship('OwnerDeveloper', back_populates='vendor_relationships')
    vendor = relationship('TechnologyVendor', back_populates='owner_relationships')

    def __repr__(self):
        return f'<OwnerVendorRelationship owner:{self.owner_id} vendor:{self.vendor_id}>'


class ProjectVendorRelationship(Base, TimestampMixin):
    """
    Track which technology vendors are involved in projects

    Schema from 03_DATABASE_RELATIONSHIPS.md
    """
    __tablename__ = 'project_vendor_relationships'

    # Primary Key
    relationship_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)
    vendor_id = Column(Integer, ForeignKey('technology_vendors.vendor_id'), nullable=False)

    # Fields
    is_confidential = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)

    # Indexes and Constraints (as specified in schema)
    __table_args__ = (
        Index('idx_project_vendor_project', 'project_id'),
        Index('idx_project_vendor_vendor', 'vendor_id'),
        Index('idx_project_vendor_conf', 'is_confidential'),
        UniqueConstraint('project_id', 'vendor_id', name='uq_project_vendor'),
    )

    # Relationships
    project = relationship('Project', back_populates='vendor_relationships')
    vendor = relationship('TechnologyVendor', back_populates='project_relationships')

    def __repr__(self):
        return f'<ProjectVendorRelationship project:{self.project_id} vendor:{self.vendor_id}>'


class ProjectConstructorRelationship(Base, TimestampMixin):
    """
    Track which construction companies are building projects

    Schema from 03_DATABASE_RELATIONSHIPS.md
    """
    __tablename__ = 'project_constructor_relationships'

    # Primary Key
    relationship_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)
    constructor_id = Column(Integer, ForeignKey('constructors.constructor_id'), nullable=False)

    # Fields
    is_confidential = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)

    # Indexes and Constraints (as specified in schema)
    __table_args__ = (
        Index('idx_project_constructor_project', 'project_id'),
        Index('idx_project_constructor_constructor', 'constructor_id'),
        Index('idx_project_constructor_conf', 'is_confidential'),
        UniqueConstraint('project_id', 'constructor_id', name='uq_project_constructor'),
    )

    # Relationships
    project = relationship('Project', back_populates='constructor_relationships')
    constructor = relationship('Constructor', back_populates='project_relationships')

    def __repr__(self):
        return f'<ProjectConstructorRelationship project:{self.project_id} constructor:{self.constructor_id}>'


class ProjectOperatorRelationship(Base, TimestampMixin):
    """
    Track which companies will operate projects

    Schema from 03_DATABASE_RELATIONSHIPS.md
    """
    __tablename__ = 'project_operator_relationships'

    # Primary Key
    relationship_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)
    operator_id = Column(Integer, ForeignKey('operators.operator_id'), nullable=False)

    # Fields
    is_confidential = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)

    # Indexes and Constraints (as specified in schema)
    __table_args__ = (
        Index('idx_project_operator_project', 'project_id'),
        Index('idx_project_operator_operator', 'operator_id'),
        Index('idx_project_operator_conf', 'is_confidential'),
        UniqueConstraint('project_id', 'operator_id', name='uq_project_operator'),
    )

    # Relationships
    project = relationship('Project', back_populates='operator_relationships')
    operator = relationship('Operator', back_populates='project_relationships')

    def __repr__(self):
        return f'<ProjectOperatorRelationship project:{self.project_id} operator:{self.operator_id}>'


class ProjectOwnerRelationship(Base, TimestampMixin):
    """
    Track which owners/developers own projects

    Schema from 03_DATABASE_RELATIONSHIPS.md
    """
    __tablename__ = 'project_owner_relationships'

    # Primary Key
    relationship_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)
    owner_id = Column(Integer, ForeignKey('owners_developers.owner_id'), nullable=False)

    # Fields
    is_confidential = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)

    # Indexes and Constraints (as specified in schema)
    __table_args__ = (
        Index('idx_project_owner_project', 'project_id'),
        Index('idx_project_owner_owner', 'owner_id'),
        Index('idx_project_owner_conf', 'is_confidential'),
        UniqueConstraint('project_id', 'owner_id', name='uq_project_owner'),
    )

    # Relationships
    project = relationship('Project', back_populates='owner_relationships')
    owner = relationship('OwnerDeveloper', back_populates='project_relationships')

    def __repr__(self):
        return f'<ProjectOwnerRelationship project:{self.project_id} owner:{self.owner_id}>'


class ProjectOfftakerRelationship(Base, TimestampMixin):
    """Track energy off-takers linked to projects."""

    __tablename__ = 'project_offtaker_relationships'

    relationship_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)
    offtaker_id = Column(Integer, ForeignKey('offtakers.offtaker_id'), nullable=False)
    agreement_type = Column(Text)
    contracted_volume = Column(Text)
    is_confidential = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)

    __table_args__ = (
        Index('idx_project_offtaker_project', 'project_id'),
        Index('idx_project_offtaker_offtaker', 'offtaker_id'),
        Index('idx_project_offtaker_conf', 'is_confidential'),
        UniqueConstraint('project_id', 'offtaker_id', name='uq_project_offtaker'),
    )

    project = relationship('Project', back_populates='offtaker_relationships')
    offtaker = relationship('Offtaker', back_populates='project_relationships')

    def __repr__(self):
        return f'<ProjectOfftakerRelationship project:{self.project_id} offtaker:{self.offtaker_id}>'


class VendorPreferredConstructor(Base, TimestampMixin):
    """
    Track which constructors are preferred by vendors

    Schema from 03_DATABASE_RELATIONSHIPS.md
    """
    __tablename__ = 'vendor_preferred_constructor'

    # Primary Key
    relationship_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    vendor_id = Column(Integer, ForeignKey('technology_vendors.vendor_id'), nullable=False)
    constructor_id = Column(Integer, ForeignKey('constructors.constructor_id'), nullable=False)

    # Fields
    is_confidential = Column(Boolean, default=False, nullable=False)
    preference_reason = Column(Text)

    # Indexes and Constraints (as specified in schema)
    __table_args__ = (
        Index('idx_vendor_constructor_vendor', 'vendor_id'),
        Index('idx_vendor_constructor_constructor', 'constructor_id'),
        Index('idx_vendor_constructor_conf', 'is_confidential'),
        UniqueConstraint('vendor_id', 'constructor_id', name='uq_vendor_constructor'),
    )

    # Relationships
    vendor = relationship('TechnologyVendor', back_populates='preferred_constructor_relationships')
    constructor = relationship('Constructor', back_populates='vendor_preferences')

    def __repr__(self):
        return f'<VendorPreferredConstructor vendor:{self.vendor_id} constructor:{self.constructor_id}>'


class PersonnelEntityRelationship(Base, TimestampMixin):
    """
    Track which people are associated with which organizations/projects (polymorphic)

    Schema from 03_DATABASE_RELATIONSHIPS.md
    """
    __tablename__ = 'personnel_entity_relationships'

    # Primary Key
    relationship_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    personnel_id = Column(Integer, ForeignKey('personnel.personnel_id'), nullable=False)

    # Polymorphic relationship (no FK constraint on entity_id)
    entity_type = Column(Text, nullable=False)  # Vendor, Owner, Operator, Constructor, Project
    entity_id = Column(Integer, nullable=False)

    # Fields
    role_at_entity = Column(Text)
    is_confidential = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)

    # Indexes and Constraints (as specified in schema)
    __table_args__ = (
        Index('idx_personnel_entity_personnel', 'personnel_id'),
        Index('idx_personnel_entity_type', 'entity_type', 'entity_id'),
        Index('idx_personnel_entity_conf', 'is_confidential'),
        UniqueConstraint('personnel_id', 'entity_type', 'entity_id', name='uq_personnel_entity'),
    )

    # Relationships
    person = relationship('Personnel', back_populates='entity_relationships')

    def __repr__(self):
        return f'<PersonnelEntityRelationship person:{self.personnel_id} {self.entity_type}:{self.entity_id}>'


class EntityTeamMember(Base):
    """
    Track internal team assignments to clients/projects (for CRM)

    Schema from 03_DATABASE_RELATIONSHIPS.md
    Note: This table does NOT use TimestampMixin (no created_by/modified_by per spec)
    """
    __tablename__ = 'entity_team_members'

    # Primary Key
    assignment_id = Column(Integer, primary_key=True, autoincrement=True)

    # Polymorphic relationship (no FK constraint on entity_id)
    entity_type = Column(Text, nullable=False)  # Owner, Vendor, Project, etc.
    entity_id = Column(Integer, nullable=False)

    # Foreign Key to Personnel (must be Internal type)
    personnel_id = Column(Integer, ForeignKey('personnel.personnel_id'), nullable=False)

    # Fields
    assignment_type = Column(Text)  # Primary_POC, Secondary_POC, Team_Member
    assigned_date = Column(Date)
    is_active = Column(Boolean, default=True, nullable=False)

    # Indexes (as specified in schema)
    __table_args__ = (
        Index('idx_team_members_entity', 'entity_type', 'entity_id'),
        Index('idx_team_members_personnel', 'personnel_id'),
        Index('idx_team_members_active', 'is_active'),
    )

    # Relationships
    person = relationship('Personnel', back_populates='team_assignments')

    def __repr__(self):
        return f'<EntityTeamMember person:{self.personnel_id} assigned to {self.entity_type}:{self.entity_id}>'


# ============================================================================
# CLIENT RELATIONSHIP TABLES (CRM)
# ============================================================================

class ClientOwnerRelationship(Base, TimestampMixin):
    """
    Link Clients to Owners/Developers (when a client IS an owner/developer)

    Schema from migration 003_add_clients_crm.sql
    """
    __tablename__ = 'client_owner_relationships'

    # Primary Key
    relationship_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    client_id = Column(Integer, ForeignKey('clients.client_id'), nullable=False)
    owner_id = Column(Integer, ForeignKey('owners_developers.owner_id'), nullable=False)

    # Fields
    is_confidential = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)

    # Indexes and Constraints
    __table_args__ = (
        Index('idx_client_owner_client', 'client_id'),
        Index('idx_client_owner_owner', 'owner_id'),
        Index('idx_client_owner_conf', 'is_confidential'),
        UniqueConstraint('client_id', 'owner_id', name='uq_client_owner'),
    )

    # Relationships
    client = relationship('Client', back_populates='owner_relationships')
    owner = relationship('OwnerDeveloper', backref='client_relationships')

    def __repr__(self):
        return f'<ClientOwnerRelationship client:{self.client_id} owner:{self.owner_id}>'


class ClientProjectRelationship(Base, TimestampMixin):
    """
    Link Clients to Projects (direct relationship)

    Schema from migration 003_add_clients_crm.sql
    """
    __tablename__ = 'client_project_relationships'

    # Primary Key
    relationship_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    client_id = Column(Integer, ForeignKey('clients.client_id'), nullable=False)
    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)

    # Fields
    relationship_type = Column(Text)  # Lead, Partner, Consultant, Advisor
    is_confidential = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)

    # Indexes and Constraints
    __table_args__ = (
        Index('idx_client_project_client', 'client_id'),
        Index('idx_client_project_project', 'project_id'),
        Index('idx_client_project_conf', 'is_confidential'),
        UniqueConstraint('client_id', 'project_id', name='uq_client_project'),
    )

    # Relationships
    client = relationship('Client', back_populates='project_relationships')
    project = relationship('Project', backref='client_relationships')

    def __repr__(self):
        return f'<ClientProjectRelationship client:{self.client_id} project:{self.project_id}>'


class ClientVendorRelationship(Base, TimestampMixin):
    """
    Link Clients to Technology Vendors (client interest in specific technologies)

    Schema from migration 003_add_clients_crm.sql
    """
    __tablename__ = 'client_vendor_relationships'

    # Primary Key
    relationship_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    client_id = Column(Integer, ForeignKey('clients.client_id'), nullable=False)
    vendor_id = Column(Integer, ForeignKey('technology_vendors.vendor_id'), nullable=False)

    # Fields
    is_confidential = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)

    # Indexes and Constraints
    __table_args__ = (
        Index('idx_client_vendor_client', 'client_id'),
        Index('idx_client_vendor_vendor', 'vendor_id'),
        Index('idx_client_vendor_conf', 'is_confidential'),
        UniqueConstraint('client_id', 'vendor_id', name='uq_client_vendor'),
    )

    # Relationships
    client = relationship('Client', back_populates='vendor_relationships')
    vendor = relationship('TechnologyVendor', backref='client_relationships')

    def __repr__(self):
        return f'<ClientVendorRelationship client:{self.client_id} vendor:{self.vendor_id}>'


class ClientOperatorRelationship(Base, TimestampMixin):
    """
    Link Clients to Operators (when a client IS an operator)

    Schema from migration 003_add_clients_crm.sql
    """
    __tablename__ = 'client_operator_relationships'

    # Primary Key
    relationship_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    client_id = Column(Integer, ForeignKey('clients.client_id'), nullable=False)
    operator_id = Column(Integer, ForeignKey('operators.operator_id'), nullable=False)

    # Fields
    is_confidential = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)

    # Indexes and Constraints
    __table_args__ = (
        Index('idx_client_operator_client', 'client_id'),
        Index('idx_client_operator_operator', 'operator_id'),
        Index('idx_client_operator_conf', 'is_confidential'),
        UniqueConstraint('client_id', 'operator_id', name='uq_client_operator'),
    )

    # Relationships
    client = relationship('Client', back_populates='operator_relationships')
    operator = relationship('Operator', backref='client_relationships')

    def __repr__(self):
        return f'<ClientOperatorRelationship client:{self.client_id} operator:{self.operator_id}>'


class ClientPersonnelRelationship(Base, TimestampMixin):
    """
    Link Clients to Personnel (key personnel at the client organization)

    Schema from migration 003_add_clients_crm.sql
    """
    __tablename__ = 'client_personnel_relationships'

    # Primary Key
    relationship_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    client_id = Column(Integer, ForeignKey('clients.client_id'), nullable=False)
    personnel_id = Column(Integer, ForeignKey('personnel.personnel_id'), nullable=False)

    # Fields
    role_at_client = Column(Text)  # CEO, VP Nuclear, Engineering Director, etc.
    is_primary_contact = Column(Boolean, default=False, nullable=False)
    is_confidential = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)

    # Indexes and Constraints
    __table_args__ = (
        Index('idx_client_personnel_client', 'client_id'),
        Index('idx_client_personnel_personnel', 'personnel_id'),
        Index('idx_client_personnel_primary', 'is_primary_contact'),
        Index('idx_client_personnel_conf', 'is_confidential'),
        UniqueConstraint('client_id', 'personnel_id', name='uq_client_personnel'),
    )

    # Relationships
    client = relationship('Client', back_populates='personnel_relationships')
    person = relationship('Personnel', backref='client_relationships')

    def __repr__(self):
        return f'<ClientPersonnelRelationship client:{self.client_id} personnel:{self.personnel_id}>'

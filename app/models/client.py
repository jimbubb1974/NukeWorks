"""
Client model for CRM features
Matches migration 003_add_clients_crm.sql specification
"""
from sqlalchemy import Column, Integer, Text, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Client(Base, TimestampMixin):
    """
    Clients tracked in the CRM system

    Can be linked to Owners/Developers, Projects, Vendors, Operators, and Personnel.
    Includes CRM fields for contact tracking and internal assessment (NED Team only).

    Schema from migration 003_add_clients_crm.sql
    """
    __tablename__ = 'clients'

    # Primary Key
    client_id = Column(Integer, primary_key=True, autoincrement=True)

    # Basic Client Information
    client_name = Column(Text, nullable=False)
    client_type = Column(Text)  # Utility, IPP, Government, Consulting, Other
    notes = Column(Text)

    # MPR Relationship
    mpr_primary_poc = Column(Integer, ForeignKey('personnel.personnel_id'))
    mpr_secondary_poc = Column(Integer, ForeignKey('personnel.personnel_id'))

    # Contact Tracking (All Users)
    last_contact_date = Column(Date)
    last_contact_type = Column(Text)  # In-person, Phone, Email, Video
    last_contact_by = Column(Integer, ForeignKey('personnel.personnel_id'))
    last_contact_notes = Column(Text)
    next_planned_contact_date = Column(Date)
    next_planned_contact_type = Column(Text)
    next_planned_contact_assigned_to = Column(Integer, ForeignKey('personnel.personnel_id'))

    # Internal Assessment (NED Team Only)
    relationship_strength = Column(Text)  # Strong, Good, Needs Attention, At Risk, New
    relationship_notes = Column(Text)  # Internal strategy notes
    client_priority = Column(Text)  # High, Medium, Low, Strategic, Opportunistic
    client_status = Column(Text)  # Active, Warm, Cold, Prospective

    # Indexes
    __table_args__ = (
        Index('idx_clients_name', 'client_name'),
        Index('idx_clients_priority', 'client_priority'),
        Index('idx_clients_status', 'client_status'),
        Index('idx_clients_mpr_poc', 'mpr_primary_poc'),
    )

    # Relationships to Personnel (MPR team members)
    mpr_primary_contact = relationship(
        'Personnel',
        foreign_keys=[mpr_primary_poc],
        backref='clients_as_primary_poc'
    )

    mpr_secondary_contact = relationship(
        'Personnel',
        foreign_keys=[mpr_secondary_poc],
        backref='clients_as_secondary_poc'
    )

    last_contacted_by_person = relationship(
        'Personnel',
        foreign_keys=[last_contact_by],
        backref='last_contacted_clients'
    )

    next_contact_assigned_person = relationship(
        'Personnel',
        foreign_keys=[next_planned_contact_assigned_to],
        backref='assigned_next_client_contacts'
    )

    # Relationships to other entities via junction tables
    owner_relationships = relationship(
        'ClientOwnerRelationship',
        back_populates='client',
        cascade='all, delete-orphan'
    )

    project_relationships = relationship(
        'ClientProjectRelationship',
        back_populates='client',
        cascade='all, delete-orphan'
    )

    vendor_relationships = relationship(
        'ClientVendorRelationship',
        back_populates='client',
        cascade='all, delete-orphan'
    )

    operator_relationships = relationship(
        'ClientOperatorRelationship',
        back_populates='client',
        cascade='all, delete-orphan'
    )

    personnel_relationships = relationship(
        'ClientPersonnelRelationship',
        back_populates='client',
        cascade='all, delete-orphan'
    )

    # Contact logs and roundtable history
    contact_logs = relationship(
        'ContactLog',
        foreign_keys='ContactLog.entity_id',
        primaryjoin='and_(Client.client_id==foreign(ContactLog.entity_id), '
                   'ContactLog.entity_type=="Client")',
        viewonly=True
    )

    roundtable_history = relationship(
        'RoundtableHistory',
        foreign_keys='RoundtableHistory.entity_id',
        primaryjoin='and_(Client.client_id==foreign(RoundtableHistory.entity_id), '
                   'RoundtableHistory.entity_type=="Client")',
        viewonly=True
    )

    def __repr__(self):
        return f'<Client {self.client_name}>'

    def to_dict(self, user=None):
        """
        Convert to dictionary, respecting NED Team permissions

        Args:
            user: Current user (to check NED Team access)

        Returns:
            Dictionary with appropriate fields based on user permissions
        """
        data = {
            'client_id': self.client_id,
            'client_name': self.client_name,
            'client_type': self.client_type,
            'notes': self.notes,
            # MPR team
            'mpr_primary_poc': self.mpr_primary_poc,
            'mpr_secondary_poc': self.mpr_secondary_poc,
            # Contact tracking (visible to all)
            'last_contact_date': self.last_contact_date.isoformat() if self.last_contact_date else None,
            'last_contact_type': self.last_contact_type,
            'last_contact_by': self.last_contact_by,
            'last_contact_notes': self.last_contact_notes,
            'next_planned_contact_date': self.next_planned_contact_date.isoformat() if self.next_planned_contact_date else None,
            'next_planned_contact_type': self.next_planned_contact_type,
            'next_planned_contact_assigned_to': self.next_planned_contact_assigned_to,
            # Audit fields
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
            'created_by': self.created_by,
            'modified_by': self.modified_by,
        }

        # Internal assessment fields (NED Team only)
        if user and (user.is_ned_team or user.is_admin):
            data.update({
                'relationship_strength': self.relationship_strength,
                'relationship_notes': self.relationship_notes,
                'client_priority': self.client_priority,
                'client_status': self.client_status,
            })
        else:
            # Redact for non-NED users
            data.update({
                'relationship_strength': '[NED Team Only]',
                'relationship_notes': '[NED Team Only]',
                'client_priority': '[NED Team Only]',
                'client_status': '[NED Team Only]',
            })

        return data

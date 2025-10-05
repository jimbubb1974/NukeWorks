"""
Owner/Developer model (utilities, IPPs, etc.)
Matches 02_DATABASE_SCHEMA.md specification exactly with all CRM fields
"""
from sqlalchemy import Column, Integer, Text, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class OwnerDeveloper(Base, TimestampMixin):
    """
    Organizations that own or develop nuclear projects

    Includes CRM fields for contact tracking and internal assessment (NED Team only)
    Schema from 02_DATABASE_SCHEMA.md - Owners_Developers table
    """
    __tablename__ = 'owners_developers'

    # Primary Key
    owner_id = Column(Integer, primary_key=True, autoincrement=True)

    # Basic Company Information
    company_name = Column(Text, nullable=False)
    company_type = Column(Text)  # IOU, COOP, Public Power, IPP
    target_customers = Column(Text)
    engagement_level = Column(Text)  # Intrigued, Interested, Invested, Inservice
    notes = Column(Text)

    # CRM Fields: Contact Tracking (Visible to All Users)
    primary_poc = Column(Integer, ForeignKey('personnel.personnel_id'))
    secondary_poc = Column(Integer, ForeignKey('personnel.personnel_id'))
    last_contact_date = Column(Date)
    last_contact_type = Column(Text)  # In-person, Phone, Email, Video
    last_contact_by = Column(Integer, ForeignKey('personnel.personnel_id'))
    last_contact_notes = Column(Text)
    next_planned_contact_date = Column(Date)
    next_planned_contact_type = Column(Text)
    next_planned_contact_assigned_to = Column(Integer, ForeignKey('personnel.personnel_id'))

    # CRM Fields: Internal Assessment (NED Team Only)
    relationship_strength = Column(Text)  # Strong, Good, Needs Attention, At Risk, New
    relationship_notes = Column(Text)  # Internal strategy notes
    client_priority = Column(Text)  # High, Medium, Low, Strategic, Opportunistic
    client_status = Column(Text)  # Active, Warm, Cold, Prospective

    # Indexes (as specified in schema)
    __table_args__ = (
        Index('idx_owners_name', 'company_name'),
        Index('idx_owners_priority', 'client_priority'),
        Index('idx_owners_poc', 'primary_poc'),
    )

    # Relationships to Personnel
    primary_contact = relationship(
        'Personnel',
        foreign_keys=[primary_poc],
        backref='owned_as_primary_poc'
    )

    secondary_contact = relationship(
        'Personnel',
        foreign_keys=[secondary_poc],
        backref='owned_as_secondary_poc'
    )

    last_contacted_by_person = relationship(
        'Personnel',
        foreign_keys=[last_contact_by],
        backref='last_contacted_owners'
    )

    next_contact_assigned = relationship(
        'Personnel',
        foreign_keys=[next_planned_contact_assigned_to],
        backref='assigned_next_contacts'
    )

    # Relationships to other entities
    vendor_relationships = relationship(
        'OwnerVendorRelationship',
        back_populates='owner',
        cascade='all, delete-orphan'
    )

    project_relationships = relationship(
        'ProjectOwnerRelationship',
        back_populates='owner',
        cascade='all, delete-orphan'
    )

    # Contact logs and roundtable history
    contact_logs = relationship(
        'ContactLog',
        foreign_keys='ContactLog.entity_id',
        primaryjoin='and_(OwnerDeveloper.owner_id==foreign(ContactLog.entity_id), '
                   'ContactLog.entity_type=="Owner")',
        viewonly=True
    )

    roundtable_history = relationship(
        'RoundtableHistory',
        foreign_keys='RoundtableHistory.entity_id',
        primaryjoin='and_(OwnerDeveloper.owner_id==foreign(RoundtableHistory.entity_id), '
                   'RoundtableHistory.entity_type=="Owner")',
        viewonly=True
    )

    def __repr__(self):
        return f'<OwnerDeveloper {self.company_name}>'

    def to_dict(self, user=None):
        """
        Convert to dictionary, respecting NED Team permissions

        Args:
            user: Current user (to check NED Team access)

        Returns:
            Dictionary with appropriate fields based on user permissions
        """
        data = {
            'owner_id': self.owner_id,
            'company_name': self.company_name,
            'company_type': self.company_type,
            'target_customers': self.target_customers,
            'engagement_level': self.engagement_level,
            'notes': self.notes,
            # Contact tracking (visible to all)
            'primary_poc': self.primary_poc,
            'secondary_poc': self.secondary_poc,
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

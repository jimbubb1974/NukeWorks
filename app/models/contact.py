"""
Contact Log model for CRM tracking
Matches 02_DATABASE_SCHEMA.md specification exactly
"""
from sqlalchemy import Column, Integer, Text, Date, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class ContactLog(Base, TimestampMixin):
    """
    Track interactions with clients (Owner/Developers)

    Schema from 02_DATABASE_SCHEMA.md - Contact_Log table
    """
    __tablename__ = 'contact_log'

    # Primary Key
    contact_id = Column(Integer, primary_key=True, autoincrement=True)

    # Polymorphic Entity Reference (currently "Owner" only, but extensible)
    entity_type = Column(Text, nullable=False)  # Currently "Owner"
    entity_id = Column(Integer, nullable=False)

    # Contact Details
    contact_date = Column(Date, nullable=False)
    contact_type = Column(Text)  # In-person, Phone, Email, Video, Conference

    # Who made the contact
    contacted_by = Column(Integer, ForeignKey('personnel.personnel_id'), nullable=False)

    # Who was contacted
    contact_person_id = Column(Integer, ForeignKey('personnel.personnel_id'))
    contact_person_freetext = Column(Text)  # If contact not in Personnel table

    # Content
    summary = Column(Text)
    is_confidential = Column(Boolean, default=False, nullable=False)

    # Follow-up
    follow_up_needed = Column(Boolean, default=False, nullable=False)
    follow_up_date = Column(Date)
    follow_up_assigned_to = Column(Integer, ForeignKey('personnel.personnel_id'))

    # Indexes (as specified in schema)
    __table_args__ = (
        Index('idx_contact_log_entity', 'entity_type', 'entity_id'),
        Index('idx_contact_log_date', 'contact_date'),
        Index('idx_contact_log_contacted_by', 'contacted_by'),
        Index('idx_contact_log_followup', 'follow_up_needed'),
        Index('idx_contact_log_followup_date', 'follow_up_date'),
    )

    # Relationships
    follow_up_person = relationship(
        'Personnel',
        foreign_keys=[follow_up_assigned_to],
        backref='assigned_followups'
    )

    def __repr__(self):
        return f'<ContactLog {self.entity_type}:{self.entity_id} on {self.contact_date}>'

    def to_dict(self, user=None):
        """
        Convert to dictionary, respecting confidentiality

        Args:
            user: Current user (to check confidential access)

        Returns:
            Dictionary with appropriate fields based on user permissions
        """
        data = {
            'contact_id': self.contact_id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'contact_date': self.contact_date.isoformat() if self.contact_date else None,
            'contact_type': self.contact_type,
            'contacted_by': self.contacted_by,
            'contact_person_id': self.contact_person_id,
            'contact_person_freetext': self.contact_person_freetext,
            'is_confidential': self.is_confidential,
            'follow_up_needed': self.follow_up_needed,
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'follow_up_assigned_to': self.follow_up_assigned_to,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
            'created_by': self.created_by,
            'modified_by': self.modified_by,
        }

        # Summary field - check confidentiality
        if user and self.is_confidential and not (user.has_confidential_access or user.is_admin):
            data['summary'] = '[Confidential - Access Restricted]'
        else:
            data['summary'] = self.summary

        return data

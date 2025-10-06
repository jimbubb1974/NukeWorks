"""
Internal Personnel model
For people who work for our firm
"""
from sqlalchemy import Column, Integer, Text, Boolean, Index, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class InternalPersonnel(Base, TimestampMixin):
    """
    Internal team members who work for our firm
    """
    __tablename__ = 'internal_personnel'

    # Primary Key
    personnel_id = Column(Integer, primary_key=True, autoincrement=True)

    # Required Fields
    full_name = Column(Text, nullable=False)
    email = Column(Text)
    phone = Column(Text)
    role = Column(Text)  # Job title/role within our firm
    department = Column(Text)  # Department within our firm

    # Status and Notes
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text)

    # Indexes
    __table_args__ = (
        Index('idx_internal_personnel_name', 'full_name'),
        Index('idx_internal_personnel_email', 'email'),
        Index('idx_internal_personnel_active', 'is_active'),
        Index('idx_internal_personnel_department', 'department'),
    )

    # Relationships
    # Note: EntityTeamMember relationships will be updated separately
    # team_assignments = relationship(
    #     'EntityTeamMember',
    #     foreign_keys='EntityTeamMember.personnel_id',
    #     back_populates='personnel',
    #     cascade='all, delete-orphan'
    # )

    # Note: ContactLog relationships will be updated separately
    # contact_logs_as_contactor = relationship(
    #     'ContactLog',
    #     foreign_keys='ContactLog.contacted_by',
    #     backref='contacted_by_internal_person'
    # )
    
    # Personnel relationships
    external_relationships = relationship(
        'PersonnelRelationship',
        foreign_keys='PersonnelRelationship.internal_personnel_id',
        back_populates='internal_personnel',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<InternalPersonnel {self.full_name}>'

    def to_dict(self):
        return {
            'personnel_id': self.personnel_id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'department': self.department,
            'is_active': self.is_active,
            'notes': self.notes,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
            'created_by': self.created_by,
            'modified_by': self.modified_by,
        }

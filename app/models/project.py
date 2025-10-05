"""
Project model
Matches 02_DATABASE_SCHEMA.md specification exactly with all financial fields
"""
from sqlalchemy import Column, Integer, Text, Float, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Project(Base, TimestampMixin):
    """
    Specific nuclear project sites and deployments

    Schema from 02_DATABASE_SCHEMA.md - Projects table
    Financial fields (capex, opex, fuel_cost, lcoe) can be marked confidential per-record
    """
    __tablename__ = 'projects'

    # Primary Key
    project_id = Column(Integer, primary_key=True, autoincrement=True)

    # Basic Project Information
    project_name = Column(Text, nullable=False)
    location = Column(Text)
    project_status = Column(Text)  # Planning, Design, Licensing, Construction, etc.
    licensing_approach = Column(Text)  # Research Reactor, Part 50, Part 52
    configuration = Column(Text)
    project_schedule = Column(Text)
    target_cod = Column(Date)

    # Geospatial metadata for map visualizations
    latitude = Column(Float)  # Decimal degrees, WGS84
    longitude = Column(Float)  # Decimal degrees, WGS84

    # Financial Data (can be marked confidential via Confidential_Field_Flags table)
    capex = Column(Float)  # Capital expenditure
    opex = Column(Float)  # Operating expenditure
    fuel_cost = Column(Float)
    lcoe = Column(Float)  # Levelized cost of energy

    # Project Dates and IDs
    cod = Column(Date)  # Commercial operation date
    mpr_project_id = Column(Text)  # Link to external MPR project files
    notes = Column(Text)

    # Firm Involvement
    firm_involvement = Column(Text)
    primary_firm_contact = Column(Integer, ForeignKey('personnel.personnel_id'))
    last_project_interaction_date = Column(Date)
    last_project_interaction_by = Column(Integer, ForeignKey('personnel.personnel_id'))
    project_health = Column(Text)  # On track, Delayed, At risk, Stalled

    # Indexes (as specified in schema)
    __table_args__ = (
        Index('idx_projects_name', 'project_name'),
        Index('idx_projects_status', 'project_status'),
        Index('idx_projects_location', 'location'),
        Index('idx_projects_cod', 'cod'),
        Index('idx_projects_lat_lon', 'latitude', 'longitude'),
    )

    # Relationships to Personnel
    primary_contact = relationship(
        'Personnel',
        foreign_keys=[primary_firm_contact],
        backref='projects_as_primary'
    )

    last_interaction_by = relationship(
        'Personnel',
        foreign_keys=[last_project_interaction_by],
        backref='projects_interacted'
    )

    # Relationships to other entities
    vendor_relationships = relationship(
        'ProjectVendorRelationship',
        back_populates='project',
        cascade='all, delete-orphan'
    )

    constructor_relationships = relationship(
        'ProjectConstructorRelationship',
        back_populates='project',
        cascade='all, delete-orphan'
    )

    operator_relationships = relationship(
        'ProjectOperatorRelationship',
        back_populates='project',
        cascade='all, delete-orphan'
    )

    owner_relationships = relationship(
        'ProjectOwnerRelationship',
        back_populates='project',
        cascade='all, delete-orphan'
    )

    offtaker_relationships = relationship(
        'ProjectOfftakerRelationship',
        back_populates='project',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Project {self.project_name}>'

    def to_dict(self, user=None):
        """
        Convert to dictionary, respecting confidentiality

        Args:
            user: Current user (to check confidential access for financial fields)

        Returns:
            Dictionary with appropriate fields based on user permissions
        """
        from app.utils.permissions import can_view_field

        data = {
            'project_id': self.project_id,
            'project_name': self.project_name,
            'location': self.location,
            'project_status': self.project_status,
            'licensing_approach': self.licensing_approach,
            'configuration': self.configuration,
            'project_schedule': self.project_schedule,
            'target_cod': self.target_cod.isoformat() if self.target_cod else None,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'cod': self.cod.isoformat() if self.cod else None,
            'mpr_project_id': self.mpr_project_id,
            'notes': self.notes,
            'firm_involvement': self.firm_involvement,
            'primary_firm_contact': self.primary_firm_contact,
            'last_project_interaction_date': self.last_project_interaction_date.isoformat() if self.last_project_interaction_date else None,
            'last_project_interaction_by': self.last_project_interaction_by,
            'project_health': self.project_health,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
            'created_by': self.created_by,
            'modified_by': self.modified_by,
        }

        # Financial fields - check confidentiality if user provided
        financial_fields = ['capex', 'opex', 'fuel_cost', 'lcoe']
        for field in financial_fields:
            if user:
                if can_view_field(user, 'projects', self.project_id, field):
                    data[field] = getattr(self, field)
                else:
                    data[field] = '[Confidential - Access Restricted]'
            else:
                data[field] = getattr(self, field)

        return data

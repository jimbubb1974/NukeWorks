"""
Technology Vendor and Product models
Matches 02_DATABASE_SCHEMA.md specification exactly
"""
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class TechnologyVendor(Base, TimestampMixin):
    """
    Nuclear technology vendors and reactor developers

    Schema from 02_DATABASE_SCHEMA.md - Technology_Vendors table
    """
    __tablename__ = 'technology_vendors'

    # Primary Key
    vendor_id = Column(Integer, primary_key=True, autoincrement=True)

    # Fields
    vendor_name = Column(Text, nullable=False)
    notes = Column(Text)

    # Indexes (as specified in schema)
    __table_args__ = (
        Index('idx_vendors_name', 'vendor_name'),
        Index('idx_vendors_created', 'created_date'),
    )

    # Relationships (defined in 03_DATABASE_RELATIONSHIPS.md)
    # Note: Products now use the unified company system via CompanyRoleAssignment
    # The old direct vendor->products relationship is deprecated

    supplier_relationships = relationship(
        'VendorSupplierRelationship',
        foreign_keys='VendorSupplierRelationship.vendor_id',
        back_populates='vendor',
        cascade='all, delete-orphan'
    )

    as_supplier_relationships = relationship(
        'VendorSupplierRelationship',
        foreign_keys='VendorSupplierRelationship.supplier_id',
        back_populates='supplier',
        cascade='all, delete-orphan'
    )

    owner_relationships = relationship(
        'OwnerVendorRelationship',
        back_populates='vendor',
        cascade='all, delete-orphan'
    )

    project_relationships = relationship(
        'ProjectVendorRelationship',
        back_populates='vendor',
        cascade='all, delete-orphan'
    )

    preferred_constructor_relationships = relationship(
        'VendorPreferredConstructor',
        back_populates='vendor',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<TechnologyVendor {self.vendor_name}>'

    def to_dict(self):
        return {
            'vendor_id': self.vendor_id,
            'vendor_name': self.vendor_name,
            'notes': self.notes,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
            'created_by': self.created_by,
            'modified_by': self.modified_by,
        }


class Product(Base, TimestampMixin):
    """
    Specific reactor designs/models offered by vendors

    Schema from 02_DATABASE_SCHEMA.md - Products table
    """
    __tablename__ = 'products'

    # Primary Key
    product_id = Column(Integer, primary_key=True, autoincrement=True)

    # Required Fields
    product_name = Column(Text, nullable=False)
    company_id = Column(Integer, ForeignKey('companies.company_id'), nullable=False)

    # Technical specifications (all optional per spec)
    reactor_type = Column(Text)  # PWR, BWR, SMR, Micro, etc.
    generation = Column(Text)  # III+, IV, etc.
    thermal_capacity = Column(Float)  # MW thermal
    gross_capacity_mwt = Column(Float)  # Reported gross capacity in MWt
    thermal_efficiency = Column(Float)  # Percentage
    fuel_type = Column(Text)
    fuel_enrichment = Column(Text)  # e.g., 5% U-235
    burnup = Column(Float)  # GWd/MTU
    design_status = Column(Text)  # Conceptual, Licensed, Operating, etc.
    mpr_project_ids = Column(Text)  # Comma-separated IDs

    # Notes
    notes = Column(Text)

    # Indexes (as specified in schema)
    __table_args__ = (
        Index('idx_products_company', 'company_id'),
        Index('idx_products_type', 'reactor_type'),
    )

    # Relationships
    company = relationship('Company', back_populates='products')

    def __repr__(self):
        return f'<Product {self.product_name}>'

    def to_dict(self):
        return {
            'product_id': self.product_id,
            'product_name': self.product_name,
            'company_id': self.company_id,
            'company_name': self.company.company_name if self.company else None,
            'reactor_type': self.reactor_type,
            'generation': self.generation,
            'thermal_capacity': self.thermal_capacity,
            'gross_capacity_mwt': self.gross_capacity_mwt,
            'thermal_efficiency': self.thermal_efficiency,
            'fuel_type': self.fuel_type,
            'fuel_enrichment': self.fuel_enrichment,
            'burnup': self.burnup,
            'design_status': self.design_status,
            'mpr_project_ids': self.mpr_project_ids,
            'notes': self.notes,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
            'created_by': self.created_by,
            'modified_by': self.modified_by,
        }

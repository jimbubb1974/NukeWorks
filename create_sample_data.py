#!/usr/bin/env python3
"""
Create Sample Data for NukeWorks Database
Populates the database with realistic test data for demonstration
"""
import sys
sys.path.insert(0, '.')

from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import (
    Base, User, TechnologyVendor, Product, OwnerDeveloper, Constructor,
    Operator, Offtaker, Project, Personnel, ContactLog, RoundtableHistory,
    VendorSupplierRelationship, OwnerVendorRelationship, ProjectVendorRelationship,
    ProjectConstructorRelationship, ProjectOperatorRelationship, ProjectOwnerRelationship,
    ProjectOfftakerRelationship, VendorPreferredConstructor, PersonnelEntityRelationship, EntityTeamMember
)
from config import DevelopmentConfig

def create_sample_data():
    """Create comprehensive sample data"""

    # Setup database connection
    config = DevelopmentConfig()
    engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("Creating sample data...")

    # Get admin user for created_by fields
    admin = session.query(User).filter_by(username='admin').first()
    if not admin:
        print("ERROR: Admin user not found. Run 'flask init-db-cmd' first.")
        return

    admin_id = admin.user_id

    # 1. CREATE USERS
    print("\n1. Creating users...")
    users_data = [
        {
            'username': 'jsmith',
            'email': 'jsmith@mpr.com',
            'full_name': 'John Smith',
            'password': 'password123',
            'has_confidential_access': True,
            'is_ned_team': True,
            'is_admin': False
        },
        {
            'username': 'mjones',
            'email': 'mjones@mpr.com',
            'full_name': 'Mary Jones',
            'password': 'password123',
            'has_confidential_access': True,
            'is_ned_team': True,
            'is_admin': False
        },
        {
            'username': 'bwilson',
            'email': 'bwilson@mpr.com',
            'full_name': 'Bob Wilson',
            'password': 'password123',
            'has_confidential_access': False,
            'is_ned_team': False,
            'is_admin': False
        }
    ]

    users = {}
    users_created = 0
    users_updated = 0
    for user_entry in users_data:
        data = user_entry.copy()
        password = data.pop('password')
        username = data['username']
        user = session.query(User).filter_by(username=username).one_or_none()

        if user:
            for key, value in data.items():
                setattr(user, key, value)
            user.set_password(password)
            users_updated += 1
            action = "Updated"
        else:
            user = User(**data)
            user.set_password(password)
            session.add(user)
            session.flush()
            users_created += 1
            action = "Created"

        users[user.username] = user
        print(f"  {action} user: {user.username}")

    session.commit()

    # 2. CREATE TECHNOLOGY VENDORS
    print("\n2. Creating technology vendors...")
    vendors_data = [
        {
            'vendor_name': 'NuScale Power',
            'notes': 'Portland, Oregon. Leading SMR developer with NRC-certified VOYGR design.',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'vendor_name': 'X-energy',
            'notes': 'Rockville, Maryland. Xe-100 high-temperature gas-cooled reactor.',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'vendor_name': 'TerraPower',
            'notes': 'Bellevue, Washington. Natrium sodium fast reactor with energy storage.',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'vendor_name': 'GE Hitachi Nuclear Energy',
            'notes': 'Wilmington, North Carolina. BWRX-300 small modular reactor program.',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'vendor_name': 'Holtec International',
            'notes': 'Camden, New Jersey. SMR-160 pressurized water reactor.',
            'created_by': admin_id,
            'modified_by': admin_id
        }
    ]

    vendors = {}
    vendors_created = 0
    vendors_updated = 0
    for vendor_entry in vendors_data:
        data = vendor_entry.copy()
        name = data['vendor_name']
        vendor = session.query(TechnologyVendor).filter_by(vendor_name=name).one_or_none()

        if vendor:
            for key, value in data.items():
                setattr(vendor, key, value)
            vendors_updated += 1
            action = "Updated"
        else:
            vendor = TechnologyVendor(**data)
            session.add(vendor)
            session.flush()
            vendors_created += 1
            action = "Created"

        vendors[vendor.vendor_name] = vendor
        print(f"  {action} vendor: {vendor.vendor_name}")

    session.commit()

    # 3. CREATE PRODUCTS
    print("\n3. Creating products...")
    products_data = [
        {
            'vendor_id': vendors['NuScale Power'].vendor_id,
            'product_name': 'NuScale VOYGR-12',
            'reactor_type': 'PWR',
            'generation': 'III+',
            'thermal_capacity': 250,
            'gross_capacity_mwt': 250,
            'thermal_efficiency': 30.8,
            'fuel_type': 'LEU',
            'fuel_enrichment': '4.95% U-235',
            'mpr_project_ids': 'MPR-001',
            'burnup': 45000,
            'design_status': 'NRC_Certified',
            'notes': '12-module configuration delivering 924 MWe total (77 MWe/module).',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'vendor_id': vendors['X-energy'].vendor_id,
            'product_name': 'Xe-100',
            'reactor_type': 'HTGR',
            'generation': 'IV',
            'thermal_capacity': 200,
            'gross_capacity_mwt': 200,
            'thermal_efficiency': 40.0,
            'fuel_type': 'TRISO',
            'fuel_enrichment': '15.5% U-235',
            'mpr_project_ids': 'MPR-002',
            'burnup': 150000,
            'design_status': 'Design_Review',
            'notes': 'High-temperature gas-cooled pebble bed reactor (80 MWe/module).',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'vendor_id': vendors['TerraPower'].vendor_id,
            'product_name': 'Natrium',
            'reactor_type': 'SFR',
            'generation': 'IV',
            'thermal_capacity': 840,
            'gross_capacity_mwt': 840,
            'thermal_efficiency': 41.1,
            'fuel_type': 'HALEU Metal',
            'fuel_enrichment': '19.75% U-235',
            'mpr_project_ids': 'MPR-003',
            'burnup': 75000,
            'design_status': 'Concept',
            'notes': 'Sodium-cooled fast reactor with molten salt energy storage (345 MWe output).',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'vendor_id': vendors['GE Hitachi Nuclear Energy'].vendor_id,
            'product_name': 'BWRX-300',
            'reactor_type': 'BWR',
            'generation': 'III+',
            'thermal_capacity': 900,
            'gross_capacity_mwt': 900,
            'thermal_efficiency': 33.3,
            'fuel_type': 'LEU',
            'fuel_enrichment': '4.95% U-235',
            'mpr_project_ids': 'MPR-004',
            'burnup': 50000,
            'design_status': 'Design_Review',
            'notes': 'Simplified boiling water reactor with passive safety (300 MWe).',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'vendor_id': vendors['Holtec International'].vendor_id,
            'product_name': 'SMR-160',
            'reactor_type': 'PWR',
            'generation': 'III',
            'thermal_capacity': 525,
            'gross_capacity_mwt': 525,
            'thermal_efficiency': 30.5,
            'fuel_type': 'LEU',
            'fuel_enrichment': '4.95% U-235',
            'mpr_project_ids': 'MPR-005',
            'burnup': 55000,
            'design_status': 'Concept',
            'notes': 'Pressurized light water SMR with underground siting (160 MWe).',
            'created_by': admin_id,
            'modified_by': admin_id
        }
    ]

    products = {}
    products_created = 0
    products_updated = 0
    for product_entry in products_data:
        data = product_entry.copy()
        name = data['product_name']
        product = session.query(Product).filter_by(product_name=name).one_or_none()

        if product:
            for key, value in data.items():
                setattr(product, key, value)
            products_updated += 1
            action = "Updated"
        else:
            product = Product(**data)
            session.add(product)
            session.flush()
            products_created += 1
            action = "Created"

        products[product.product_name] = product
        print(f"  {action} product: {product.product_name}")

    session.commit()

    # 4. CREATE CONSTRUCTORS
    print("\n4. Creating constructors...")
    constructors_data = [
        {
            'company_name': 'Bechtel Corporation',
            'notes': 'Reston, Virginia. Global EPC firm with large nuclear portfolio.',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'company_name': 'Fluor Corporation',
            'notes': 'Irving, Texas. Strategic partner for NuScale SMR deployments.',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'company_name': 'Kiewit Corporation',
            'notes': 'Omaha, Nebraska. Power and infrastructure construction experience.',
            'created_by': admin_id,
            'modified_by': admin_id
        }
    ]

    constructors = {}
    constructors_created = 0
    constructors_updated = 0
    for constructor_entry in constructors_data:
        data = constructor_entry.copy()
        name = data['company_name']
        constructor = session.query(Constructor).filter_by(company_name=name).one_or_none()

        if constructor:
            for key, value in data.items():
                setattr(constructor, key, value)
            constructors_updated += 1
            action = "Updated"
        else:
            constructor = Constructor(**data)
            session.add(constructor)
            session.flush()
            constructors_created += 1
            action = "Created"

        constructors[constructor.company_name] = constructor
        print(f"  {action} constructor: {constructor.company_name}")

    session.commit()

    # 5. CREATE OPERATORS
    print("\n5. Creating operators...")
    operators_data = [
        {
            'company_name': 'Exelon Generation',
            'notes': 'Chicago, Illinois. Largest nuclear fleet operator in the United States.',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'company_name': 'Duke Energy',
            'notes': 'Charlotte, North Carolina. Major utility with active nuclear operations.',
            'created_by': admin_id,
            'modified_by': admin_id
        }
    ]

    operators = {}
    operators_created = 0
    operators_updated = 0
    for operator_entry in operators_data:
        data = operator_entry.copy()
        name = data['company_name']
        operator = session.query(Operator).filter_by(company_name=name).one_or_none()

        if operator:
            for key, value in data.items():
                setattr(operator, key, value)
            operators_updated += 1
            action = "Updated"
        else:
            operator = Operator(**data)
            session.add(operator)
            session.flush()
            operators_created += 1
            action = "Created"

        operators[operator.company_name] = operator
        print(f"  {action} operator: {operator.company_name}")

    session.commit()

    # 6. CREATE OFF-TAKERS
    print("\n6. Creating energy off-takers...")
    offtaker_data = [
        {
            'organization_name': 'Amazon Web Services',
            'sector': 'Data Centers',
            'notes': 'Driving long-term renewable procurement for hyperscale data centers.',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'organization_name': 'Google Energy LLC',
            'sector': 'Technology',
            'notes': 'Carbon-free energy initiative for global operations.',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'organization_name': 'Microsoft Corporation',
            'sector': 'Technology',
            'notes': 'Exploring nuclear energy as part of 24/7 carbon-free goal.',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'organization_name': 'Meta Platforms Energy Procurement',
            'sector': 'Data Centers',
            'notes': 'Building long-term zero-carbon supply for hyperscale campuses.',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'organization_name': 'Apple Energy LLC',
            'sector': 'Technology',
            'notes': 'Evaluating firm clean capacity for global operations and suppliers.',
            'created_by': admin_id,
            'modified_by': admin_id
        }
    ]

    offtakers = {}
    offtaker_created = 0
    offtaker_updated = 0
    for entry in offtaker_data:
        data = entry.copy()
        name = data['organization_name']
        offtaker = session.query(Offtaker).filter_by(organization_name=name).one_or_none()

        if offtaker:
            for key, value in data.items():
                setattr(offtaker, key, value)
            offtaker_updated += 1
            action = "Updated"
        else:
            offtaker = Offtaker(**data)
            session.add(offtaker)
            session.flush()
            offtaker_created += 1
            action = "Created"

        offtakers[offtaker.organization_name] = offtaker
        print(f"  {action} off-taker: {offtaker.organization_name}")

    session.commit()

    # 7. CREATE OWNERS/DEVELOPERS
    print("\n7. Creating owners/developers...")
    owners_data = [
        {
            'company_name': 'Utah Associated Municipal Power Systems (UAMPS)',
            'company_type': 'Public Power',
            'target_customers': 'Member utilities in the Intermountain West',
            'engagement_level': 'Invested',
            'notes': 'Leading the Carbon Free Power Project with NuScale.',
            'last_contact_date': date.today() - timedelta(days=15),
            'last_contact_type': 'Video',
            'relationship_strength': 'Strong',
            'relationship_notes': 'Active VOYGR project development, regular contact.',
            'client_priority': 'High',
            'client_status': 'Active',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'company_name': 'Energy Northwest',
            'company_type': 'Public Power',
            'target_customers': 'Northwest municipal utilities',
            'engagement_level': 'Interested',
            'notes': 'Exploring multiple SMR options for regional capacity needs.',
            'last_contact_date': date.today() - timedelta(days=30),
            'last_contact_type': 'Conference',
            'relationship_strength': 'Good',
            'relationship_notes': 'Monitoring technology progress across vendors.',
            'client_priority': 'Medium',
            'client_status': 'Prospective',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'company_name': 'Ontario Power Generation',
            'company_type': 'Utility',
            'target_customers': 'Ontario ratepayers',
            'engagement_level': 'Invested',
            'notes': 'Darlington SMR deployment with GEH BWRX-300.',
            'last_contact_date': date.today() - timedelta(days=45),
            'last_contact_type': 'Phone',
            'relationship_strength': 'Strong',
            'relationship_notes': 'Long-term SMR strategy with provincial backing.',
            'client_priority': 'High',
            'client_status': 'Active',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'company_name': 'PacifiCorp',
            'company_type': 'Investor-Owned Utility',
            'target_customers': 'Western U.S. service territories',
            'engagement_level': 'Intrigued',
            'notes': 'Evaluating SMRs as part of coal replacement strategy.',
            'last_contact_date': date.today() - timedelta(days=60),
            'last_contact_type': 'Email',
            'relationship_strength': 'Needs Attention',
            'relationship_notes': 'Initial discussions, requires economic validation.',
            'client_priority': 'Low',
            'client_status': 'Inactive',
            'created_by': admin_id,
            'modified_by': admin_id
        }
    ]

    owners = {}
    owners_created = 0
    owners_updated = 0
    for owner_entry in owners_data:
        data = owner_entry.copy()
        name = data['company_name']
        owner = session.query(OwnerDeveloper).filter_by(company_name=name).one_or_none()

        if owner:
            for key, value in data.items():
                setattr(owner, key, value)
            owners_updated += 1
            action = "Updated"
        else:
            owner = OwnerDeveloper(**data)
            session.add(owner)
            session.flush()
            owners_created += 1
            action = "Created"

        owners[owner.company_name] = owner
        print(f"  {action} owner: {owner.company_name}")

    session.commit()

    # 7. CREATE PERSONNEL
    print("\n7. Creating personnel...")
    personnel_data = [
        {
            'full_name': 'John Smith',
            'email': 'jsmith@mpr.com',
            'phone': '+1-555-0100',
            'role': 'NED Team Lead',
            'personnel_type': 'Internal',
            'notes': 'Internal NED team member (matches user jsmith).',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'full_name': 'Mary Jones',
            'email': 'mjones@mpr.com',
            'phone': '+1-555-0101',
            'role': 'NED Analyst',
            'personnel_type': 'Internal',
            'notes': 'Internal NED team member (matches user mjones).',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'full_name': 'Bob Wilson',
            'email': 'bwilson@mpr.com',
            'phone': '+1-555-0102',
            'role': 'Business Development',
            'personnel_type': 'Internal',
            'notes': 'Internal user for general access.',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'full_name': 'John Clayton',
            'email': 'jclayton@nuscalepower.com',
            'phone': '+1-503-612-3500',
            'role': 'CEO',
            'personnel_type': 'Vendor_Contact',
            'organization_type': 'Vendor',
            'organization_id': vendors['NuScale Power'].vendor_id,
            'notes': 'NuScale CEO, former Navy officer.',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'full_name': 'Clay Sell',
            'email': 'csell@x-energy.com',
            'phone': '+1-301-984-9400',
            'role': 'CEO',
            'personnel_type': 'Vendor_Contact',
            'organization_type': 'Vendor',
            'organization_id': vendors['X-energy'].vendor_id,
            'notes': 'Former U.S. Deputy Secretary of Energy.',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'full_name': 'Chris Levesque',
            'email': 'clevesque@terrapower.com',
            'phone': '+1-425-468-8600',
            'role': 'President & CEO',
            'personnel_type': 'Vendor_Contact',
            'organization_type': 'Vendor',
            'organization_id': vendors['TerraPower'].vendor_id,
            'notes': 'Leading Natrium development.',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'full_name': 'Doug Hunter',
            'email': 'dhunter@uamps.com',
            'phone': '+1-801-424-4800',
            'role': 'CEO',
            'personnel_type': 'Owner_Contact',
            'organization_type': 'Owner',
            'organization_id': owners['Utah Associated Municipal Power Systems (UAMPS)'].owner_id,
            'notes': 'Primary contact for CFPP development.',
            'created_by': admin_id,
            'modified_by': admin_id
        }
    ]

    personnel = {}
    personnel_created = 0
    personnel_updated = 0
    for person_entry in personnel_data:
        data = person_entry.copy()
        email = data['email']
        person = session.query(Personnel).filter_by(email=email).one_or_none()

        if person:
            for key, value in data.items():
                setattr(person, key, value)
            personnel_updated += 1
            action = "Updated"
        else:
            person = Personnel(**data)
            session.add(person)
            session.flush()
            personnel_created += 1
            action = "Created"

        personnel[person.full_name] = person
        print(f"  {action} person: {person.full_name}")

    session.commit()

    # 8. CREATE PROJECTS
    print("\n8. Creating projects...")
    projects_data = [
        {
            'project_name': 'Carbon Free Power Project (CFPP)',
            'location': 'Idaho National Laboratory, Idaho, USA',
            'project_status': 'Licensing',
            'licensing_approach': 'Part 52',
            'configuration': '6x NuScale VOYGR-77 modules',
            'project_schedule': 'Phased module deployment starting 2029',
            'target_cod': date(2029, 12, 1),
            'cod': date(2029, 12, 31),
            'capex': 5300000000,  # $5.3B
            'opex': 180000000,  # $180M/year
            'fuel_cost': 25000000,  # $25M/year
            'lcoe': 89.50,  # $/MWh
            'notes': 'First NuScale SMR project in USA, utility consortium led by UAMPS.',
            'firm_involvement': 'Owner’s engineer support and licensing advisory.',
            'project_health': 'At risk',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'project_name': 'Darlington New Nuclear',
            'location': 'Darlington, Ontario, Canada',
            'project_status': 'Planning',
            'licensing_approach': 'Canadian Vendor Design Review',
            'configuration': '4x BWRX-300 modules',
            'project_schedule': 'First unit online by 2028',
            'target_cod': date(2028, 6, 1),
            'cod': date(2028, 6, 30),
            'capex': 4200000000,  # $4.2B CAD
            'opex': 150000000,
            'lcoe': 92.00,
            'notes': 'GE Hitachi BWRX-300 deployment at existing nuclear site.',
            'firm_involvement': 'Supporting technology evaluation for provincial stakeholders.',
            'project_health': 'On track',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'project_name': 'Natrium Demonstration',
            'location': 'Kemmerer, Wyoming, USA',
            'project_status': 'Development',
            'licensing_approach': 'Advanced Reactor Demonstration Program',
            'configuration': '345 MWe sodium fast reactor with thermal storage',
            'project_schedule': 'Demonstration targeted for 2030',
            'cod': date(2030, 12, 31),
            'capex': 4000000000,
            'notes': 'First Natrium reactor replacing retiring coal plant.',
            'firm_involvement': 'Owner advisor for site redevelopment planning.',
            'project_health': 'Delayed',
            'created_by': admin_id,
            'modified_by': admin_id
        }
    ]

    projects = {}
    projects_created = 0
    projects_updated = 0
    for project_entry in projects_data:
        data = project_entry.copy()
        name = data['project_name']
        project = session.query(Project).filter_by(project_name=name).one_or_none()

        if project:
            for key, value in data.items():
                setattr(project, key, value)
            projects_updated += 1
            action = "Updated"
        else:
            project = Project(**data)
            session.add(project)
            session.flush()
            projects_created += 1
            action = "Created"

        projects[project.project_name] = project
        print(f"  {action} project: {project.project_name}")

    session.commit()

    # 9. CREATE RELATIONSHIPS
    print("\n9. Creating relationships...")

    # Vendor-Supplier relationships
    supplier_lookup = {
        'vendor_id': vendors['NuScale Power'].vendor_id,
        'supplier_id': vendors['Holtec International'].vendor_id,
    }
    supplier_rel = session.query(VendorSupplierRelationship).filter_by(**supplier_lookup).one_or_none()
    if supplier_rel:
        supplier_rel.component_type = 'Major Components'
        supplier_rel.notes = 'Holtec fabricates large components for NuScale deployments.'
        supplier_rel.is_confidential = False
        supplier_rel.created_by = admin_id
        supplier_rel.modified_by = admin_id
        supplier_status = "Updated"
    else:
        supplier_rel = VendorSupplierRelationship(
            component_type='Major Components',
            notes='Holtec fabricates large components for NuScale deployments.',
            is_confidential=False,
            created_by=admin_id,
            modified_by=admin_id,
            **supplier_lookup,
        )
        session.add(supplier_rel)
        supplier_status = "Created"
    print(f"  {supplier_status} vendor-supplier relationship")

    # Owner-Vendor relationships
    owner_vendor_rels = [
        {
            'owner_id': owners['Utah Associated Municipal Power Systems (UAMPS)'].owner_id,
            'vendor_id': vendors['NuScale Power'].vendor_id,
            'relationship_type': 'Delivery_Contract',
            'is_confidential': True,
            'notes': 'Carbon Free Power Project development agreement.',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'owner_id': owners['Ontario Power Generation'].owner_id,
            'vendor_id': vendors['GE Hitachi Nuclear Energy'].vendor_id,
            'relationship_type': 'Development_Agreement',
            'is_confidential': False,
            'notes': 'Darlington BWRX-300 deployment partnership.',
            'created_by': admin_id,
            'modified_by': admin_id
        }
    ]

    owner_vendor_created = 0
    owner_vendor_updated = 0
    for rel_entry in owner_vendor_rels:
        data = rel_entry.copy()
        lookup = {
            'owner_id': data['owner_id'],
            'vendor_id': data['vendor_id'],
        }
        rel = session.query(OwnerVendorRelationship).filter_by(**lookup).one_or_none()
        if rel:
            for key, value in data.items():
                setattr(rel, key, value)
            owner_vendor_updated += 1
        else:
            rel = OwnerVendorRelationship(**data)
            session.add(rel)
            owner_vendor_created += 1
    print(f"  Created owner-vendor relationships: {owner_vendor_created}, updated: {owner_vendor_updated}")

    # Project-Vendor relationships
    project_vendor_rels = [
        {
            'project_id': projects['Carbon Free Power Project (CFPP)'].project_id,
            'vendor_id': vendors['NuScale Power'].vendor_id,
            'is_confidential': False,
            'notes': 'Technology provider for 6-module VOYGR',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'project_id': projects['Darlington New Nuclear'].project_id,
            'vendor_id': vendors['GE Hitachi Nuclear Energy'].vendor_id,
            'is_confidential': False,
            'notes': 'BWRX-300 technology provider',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'project_id': projects['Natrium Demonstration'].project_id,
            'vendor_id': vendors['TerraPower'].vendor_id,
            'is_confidential': False,
            'notes': 'Natrium reactor technology',
            'created_by': admin_id,
            'modified_by': admin_id
        }
    ]

    project_vendor_created = 0
    project_vendor_updated = 0
    for rel_entry in project_vendor_rels:
        data = rel_entry.copy()
        lookup = {
            'project_id': data['project_id'],
            'vendor_id': data['vendor_id'],
        }
        rel = session.query(ProjectVendorRelationship).filter_by(**lookup).one_or_none()
        if rel:
            for key, value in data.items():
                setattr(rel, key, value)
            project_vendor_updated += 1
        else:
            rel = ProjectVendorRelationship(**data)
            session.add(rel)
            project_vendor_created += 1
    print(f"  Created project-vendor relationships: {project_vendor_created}, updated: {project_vendor_updated}")

    # Project-Owner relationships
    project_owner_rels = [
        {
            'project_id': projects['Carbon Free Power Project (CFPP)'].project_id,
            'owner_id': owners['Utah Associated Municipal Power Systems (UAMPS)'].owner_id,
            'is_confidential': False,
            'notes': 'Project owner and developer',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'project_id': projects['Darlington New Nuclear'].project_id,
            'owner_id': owners['Ontario Power Generation'].owner_id,
            'is_confidential': False,
            'notes': 'Owner and operator',
            'created_by': admin_id,
            'modified_by': admin_id
        }
    ]

    project_owner_created = 0
    project_owner_updated = 0
    for rel_entry in project_owner_rels:
        data = rel_entry.copy()
        lookup = {
            'project_id': data['project_id'],
            'owner_id': data['owner_id'],
        }
        rel = session.query(ProjectOwnerRelationship).filter_by(**lookup).one_or_none()
        if rel:
            for key, value in data.items():
                setattr(rel, key, value)
            project_owner_updated += 1
        else:
            rel = ProjectOwnerRelationship(**data)
            session.add(rel)
            project_owner_created += 1
    print(f"  Created project-owner relationships: {project_owner_created}, updated: {project_owner_updated}")

    # Project-Offtaker relationships
    project_offtaker_rels = [
        {
            'project_id': projects['Carbon Free Power Project (CFPP)'].project_id,
            'offtaker_id': offtakers['Amazon Web Services'].offtaker_id,
            'agreement_type': 'PPA (preliminary)',
            'contracted_volume': '250 MW',
            'is_confidential': False,
            'notes': 'Exploratory discussions for data center supply',
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'project_id': projects['Darlington New Nuclear'].project_id,
            'offtaker_id': offtakers['Google Energy LLC'].offtaker_id,
            'agreement_type': 'MOU',
            'contracted_volume': '100 MW',
            'is_confidential': False,
            'notes': 'Early stage MOU for Ontario operations',
            'created_by': admin_id,
            'modified_by': admin_id
        }
    ]

    project_offtaker_created = 0
    project_offtaker_updated = 0
    for rel_entry in project_offtaker_rels:
        data = rel_entry.copy()
        lookup = {
            'project_id': data['project_id'],
            'offtaker_id': data['offtaker_id'],
        }
        rel = session.query(ProjectOfftakerRelationship).filter_by(**lookup).one_or_none()
        if rel:
            for key, value in data.items():
                setattr(rel, key, value)
            project_offtaker_updated += 1
        else:
            rel = ProjectOfftakerRelationship(**data)
            session.add(rel)
            project_offtaker_created += 1
    print(f"  Created project-offtaker relationships: {project_offtaker_created}, updated: {project_offtaker_updated}")

    # Project-Constructor relationships
    project_constructor_lookup = {
        'project_id': projects['Carbon Free Power Project (CFPP)'].project_id,
        'constructor_id': constructors['Fluor Corporation'].constructor_id,
    }
    project_constructor_rel = session.query(ProjectConstructorRelationship).filter_by(**project_constructor_lookup).one_or_none()
    if project_constructor_rel:
        project_constructor_rel.is_confidential = False
        project_constructor_rel.notes = 'EPC contractor'
        project_constructor_rel.created_by = admin_id
        project_constructor_rel.modified_by = admin_id
        project_constructor_status = "Updated"
    else:
        project_constructor_rel = ProjectConstructorRelationship(
            is_confidential=False,
            notes='EPC contractor',
            created_by=admin_id,
            modified_by=admin_id,
            **project_constructor_lookup,
        )
        session.add(project_constructor_rel)
        project_constructor_status = "Created"
    print(f"  {project_constructor_status} project-constructor relationship")

    # Vendor Preferred Constructor
    vendor_pref_lookup = {
        'vendor_id': vendors['NuScale Power'].vendor_id,
        'constructor_id': constructors['Fluor Corporation'].constructor_id,
    }
    vendor_pref_constructor = session.query(VendorPreferredConstructor).filter_by(**vendor_pref_lookup).one_or_none()
    if vendor_pref_constructor:
        vendor_pref_constructor.is_confidential = False
        vendor_pref_constructor.preference_reason = 'Strategic alliance for SMR construction'
        vendor_pref_constructor.created_by = admin_id
        vendor_pref_constructor.modified_by = admin_id
        vendor_pref_status = "Updated"
    else:
        vendor_pref_constructor = VendorPreferredConstructor(
            is_confidential=False,
            preference_reason='Strategic alliance for SMR construction',
            created_by=admin_id,
            modified_by=admin_id,
            **vendor_pref_lookup,
        )
        session.add(vendor_pref_constructor)
        vendor_pref_status = "Created"
    print(f"  {vendor_pref_status} vendor preferred constructor")

    session.commit()

    # 10. CREATE CONTACT LOGS
    print("\n10. Creating contact logs...")
    contact_logs = [
        {
            'entity_type': 'Owner',
            'entity_id': owners['Utah Associated Municipal Power Systems (UAMPS)'].owner_id,
            'contact_date': date.today() - timedelta(days=15),
            'contact_type': 'Meeting',
            'contacted_by': personnel['John Smith'].personnel_id,
            'contact_person_id': personnel['Doug Hunter'].personnel_id,
            'summary': 'Discussed project schedule and licensing progress.',
            'is_confidential': False,
            'follow_up_needed': True,
            'follow_up_date': date.today() + timedelta(days=30),
            'follow_up_assigned_to': personnel['Mary Jones'].personnel_id,
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'entity_type': 'Vendor',
            'entity_id': vendors['NuScale Power'].vendor_id,
            'contact_date': date.today() - timedelta(days=20),
            'contact_type': 'Conference',
            'contacted_by': personnel['Mary Jones'].personnel_id,
            'contact_person_id': personnel['John Clayton'].personnel_id,
            'summary': 'ANS conference presentation on VOYGR deployment.',
            'is_confidential': False,
            'follow_up_needed': False,
            'created_by': admin_id,
            'modified_by': admin_id
        },
        {
            'entity_type': 'Owner',
            'entity_id': owners['Ontario Power Generation'].owner_id,
            'contact_date': date.today() - timedelta(days=45),
            'contact_type': 'Phone',
            'contacted_by': personnel['Bob Wilson'].personnel_id,
            'contact_person_freetext': 'Darlington project office',
            'summary': 'Status update on Darlington licensing milestones.',
            'is_confidential': False,
            'follow_up_needed': True,
            'follow_up_date': date.today() + timedelta(days=15),
            'follow_up_assigned_to': personnel['John Smith'].personnel_id,
            'created_by': admin_id,
            'modified_by': admin_id
        }
    ]

    contact_created = 0
    contact_updated = 0
    for log_entry in contact_logs:
        data = log_entry.copy()
        lookup = {
            'entity_type': data['entity_type'],
            'entity_id': data['entity_id'],
            'contact_date': data['contact_date'],
            'summary': data['summary'],
        }
        log = session.query(ContactLog).filter_by(**lookup).one_or_none()
        if log:
            for key, value in data.items():
                setattr(log, key, value)
            contact_updated += 1
        else:
            log = ContactLog(**data)
            session.add(log)
            contact_created += 1
    print(f"  Created contact logs: {contact_created}, updated: {contact_updated}")

    session.commit()

    # 11. CREATE ROUNDTABLE HISTORY (NED Team Only)
    print("\n11. Creating roundtable history...")
    roundtable_entries = [
        {
            'entity_type': 'Owner',
            'entity_id': owners['Utah Associated Municipal Power Systems (UAMPS)'].owner_id,
            'meeting_date': date.today() - timedelta(days=7),
            'discussion': 'Team assessment: UAMPS remains committed despite schedule delays. Financial viability depends on DOE support. Recommend increasing engagement frequency.',
            'action_items': 'John to schedule call with UAMPS CEO next week.',
            'created_by': admin_id,
            'created_date': date.today() - timedelta(days=7)
        },
        {
            'entity_type': 'Owner',
            'entity_id': owners['PacifiCorp'].owner_id,
            'meeting_date': date.today() - timedelta(days=14),
            'discussion': 'Team assessment: PacifiCorp showing renewed interest in SMRs for coal replacement. Need economics briefing for IRP alignment.',
            'action_items': 'Mary to develop SMR economics brief for PacifiCorp.',
            'created_by': admin_id,
            'created_date': date.today() - timedelta(days=14)
        },
        {
            'entity_type': 'Vendor',
            'entity_id': vendors['X-energy'].vendor_id,
            'meeting_date': date.today() - timedelta(days=21),
            'discussion': 'Team discussion on X-energy ARDP funding and Xe-100 progress. DOE support strong. Watch for utility partnerships.',
            'action_items': 'Track X-energy announcements for new utility partners.',
            'created_by': admin_id,
            'created_date': date.today() - timedelta(days=21)
        }
    ]

    roundtable_created = 0
    roundtable_updated = 0
    for entry_entry in roundtable_entries:
        data = entry_entry.copy()
        lookup = {
            'entity_type': data['entity_type'],
            'entity_id': data['entity_id'],
            'meeting_date': data['meeting_date'],
        }
        entry = session.query(RoundtableHistory).filter_by(**lookup).one_or_none()
        if entry:
            for key, value in data.items():
                setattr(entry, key, value)
            roundtable_updated += 1
        else:
            entry = RoundtableHistory(**data)
            session.add(entry)
            roundtable_created += 1
    print(f"  Created roundtable entries: {roundtable_created}, updated: {roundtable_updated}")

    session.commit()

    # 12. ASSIGN TEAM MEMBERS
    print("\n12. Assigning team members...")
    team_assignments = [
        {
            'entity_type': 'Owner',
            'entity_id': owners['Utah Associated Municipal Power Systems (UAMPS)'].owner_id,
            'personnel_id': personnel['John Smith'].personnel_id,
            'assignment_type': 'Primary_POC',
            'assigned_date': date.today() - timedelta(days=60)
        },
        {
            'entity_type': 'Owner',
            'entity_id': owners['Ontario Power Generation'].owner_id,
            'personnel_id': personnel['Mary Jones'].personnel_id,
            'assignment_type': 'Primary_POC',
            'assigned_date': date.today() - timedelta(days=45)
        },
        {
            'entity_type': 'Vendor',
            'entity_id': vendors['NuScale Power'].vendor_id,
            'personnel_id': personnel['John Smith'].personnel_id,
            'assignment_type': 'Technical_Lead',
            'assigned_date': date.today() - timedelta(days=90)
        }
    ]

    team_created = 0
    team_updated = 0
    for assignment_entry in team_assignments:
        data = assignment_entry.copy()
        lookup = {
            'entity_type': data['entity_type'],
            'entity_id': data['entity_id'],
            'personnel_id': data['personnel_id'],
        }
        assignment = session.query(EntityTeamMember).filter_by(**lookup).one_or_none()
        if assignment:
            for key, value in data.items():
                setattr(assignment, key, value)
            team_updated += 1
        else:
            assignment = EntityTeamMember(**data)
            session.add(assignment)
            team_created += 1
    print(f"  Created team assignments: {team_created}, updated: {team_updated}")

    session.commit()

    print("\n" + "="*70)
    print("✓ SAMPLE DATA CREATION COMPLETE")
    print("="*70)
    print(f"\nProcessed:")
    print(f"  - Users: {users_created} created, {users_updated} updated")
    print(f"  - Technology vendors: {vendors_created} created, {vendors_updated} updated")
    print(f"  - Products: {products_created} created, {products_updated} updated")
    print(f"  - Constructors: {constructors_created} created, {constructors_updated} updated")
    print(f"  - Operators: {operators_created} created, {operators_updated} updated")
    print(f"  - Owners/developers: {owners_created} created, {owners_updated} updated")
    print(f"  - Personnel: {personnel_created} created, {personnel_updated} updated")
    print(f"  - Projects: {projects_created} created, {projects_updated} updated")
    print(f"  - Vendor-supplier relationship: {supplier_status.lower()}" )
    print(f"  - Owner-vendor relationships: {owner_vendor_created} created, {owner_vendor_updated} updated")
    print(f"  - Project-vendor relationships: {project_vendor_created} created, {project_vendor_updated} updated")
    print(f"  - Project-owner relationships: {project_owner_created} created, {project_owner_updated} updated")
    print(f"  - Project-constructor relationship: {project_constructor_status.lower()}")
    print(f"  - Vendor preferred constructor: {vendor_pref_status.lower()}")
    print(f"  - Contact logs: {contact_created} created, {contact_updated} updated")
    print(f"  - Roundtable history: {roundtable_created} created, {roundtable_updated} updated")
    print(f"  - Team assignments: {team_created} created, {team_updated} updated")
    print("\nYou can now log in with:")
    print("  Username: admin / Password: admin123 (full access)")
    print("  Username: jsmith / Password: password123 (NED Team)")
    print("  Username: mjones / Password: password123 (NED Team)")
    print("  Username: bwilson / Password: password123 (Basic user)")
    print("="*70)


if __name__ == '__main__':
    try:
        create_sample_data()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

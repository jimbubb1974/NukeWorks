#!/usr/bin/env python
"""
JSON to SQLite Import Script for NukeWorks
Merges AI_RESEARCH_EXTRACTION_2025-10-18.json into dev_nukeworks.sqlite

Phases:
1. Upsert Companies
2. Upsert External Personnel
3. Create Client Profiles (CRM data with encryption)
4. Create Roundtable History entries (encrypted NED Team notes)
5. Link Internal-External Personnel relationships
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import_log.txt'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app, db_session as default_db_session
from app.models import (
    Company, ExternalPersonnel, ClientProfile, RoundtableHistory,
    InternalPersonnel, PersonnelRelationship
)
from sqlalchemy.orm import scoped_session


class JSONImporter:
    """Import JSON research data into NukeWorks database"""

    def __init__(self, db_path: str, json_path: str):
        self.db_path = db_path
        self.json_path = json_path
        self.app = None
        self.session = None
        self.stats = {
            'companies_created': 0,
            'companies_updated': 0,
            'personnel_created': 0,
            'personnel_updated': 0,
            'client_profiles_created': 0,
            'roundtable_entries_created': 0,
            'relationships_created': 0,
            'errors': []
        }
        self.internal_staff_map = {}  # Map of last_name -> InternalPersonnel.id

    def load_json(self) -> Dict:
        """Load JSON file"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded JSON from {self.json_path}")
            return data
        except Exception as e:
            logger.error(f"Failed to load JSON: {e}")
            raise

    def init_app(self):
        """Initialize Flask app and database session"""
        # Create app and get session
        self.app = create_app('development')

        # Override database path
        self.app.config['DATABASE_PATH'] = self.db_path

        with self.app.app_context():
            from app import get_or_create_engine_session
            engine, scoped_sess = get_or_create_engine_session(self.db_path, self.app)
            self.session = scoped_sess
            logger.info(f"Connected to database: {self.db_path}")

            # Load internal staff map for relationship linking
            self._load_internal_staff_map()

    def _load_internal_staff_map(self):
        """Build map of internal personnel by last name for fuzzy matching"""
        try:
            internal_staff = self.session.query(InternalPersonnel).all()
            for person in internal_staff:
                # Map by last name (simple fuzzy match)
                last_name = person.full_name.split()[-1] if person.full_name else ""
                self.internal_staff_map[last_name.lower()] = person.personnel_id
            logger.info(f"Loaded {len(self.internal_staff_map)} internal staff members")
        except Exception as e:
            logger.error(f"Failed to load internal staff map: {e}")

    def run(self):
        """Execute full import"""
        try:
            with self.app.app_context():
                data = self.load_json()

                logger.info("=" * 70)
                logger.info("PHASE 1: Importing Companies")
                logger.info("=" * 70)
                self.phase_1_companies(data)

                logger.info("\n" + "=" * 70)
                logger.info("PHASE 2: Importing External Personnel")
                logger.info("=" * 70)
                self.phase_2_external_personnel(data)

                logger.info("\n" + "=" * 70)
                logger.info("PHASE 3: Creating Client Profiles & Roundtable Entries")
                logger.info("=" * 70)
                self.phase_3_client_profiles_and_roundtable(data)

                logger.info("\n" + "=" * 70)
                logger.info("PHASE 4: Linking Internal-External Relationships")
                logger.info("=" * 70)
                self.phase_4_relationships(data)

                logger.info("\n" + "=" * 70)
                logger.info("IMPORT COMPLETE")
                logger.info("=" * 70)
                self.print_summary()

        except Exception as e:
            logger.error(f"Import failed: {e}", exc_info=True)
            self.session.rollback()
            raise

    def phase_1_companies(self, data: Dict):
        """Phase 1: Upsert companies"""
        clients = data.get('clients', [])
        logger.info(f"Processing {len(clients)} clients...")

        for client_data in clients:
            try:
                ext_client = client_data.get('external_client', {})
                company_name = ext_client.get('company_name')
                company_id = ext_client.get('company_id')
                confidence = ext_client.get('db_match_confidence', 0)

                if not company_name:
                    logger.warning("Skipping client with no company_name")
                    continue

                # Check if company exists
                existing = self.session.query(Company).filter_by(company_name=company_name).first()

                if existing:
                    # Update if confidence is high
                    if confidence >= 0.95:
                        if ext_client.get('notes'):
                            existing.notes = (existing.notes or "") + "\n[UPDATED 2025-10-18]\n" + ext_client.get('notes', '')
                        existing.headquarters_country = ext_client.get('headquarters_country')
                        self.session.commit()
                        logger.info(f"✓ Updated company: {company_name} (confidence: {confidence})")
                        self.stats['companies_updated'] += 1
                else:
                    # Create new company
                    new_company = Company(
                        company_name=company_name,
                        company_type=ext_client.get('company_type', 'Unknown'),
                        website=ext_client.get('website'),
                        headquarters_country=ext_client.get('headquarters_country'),
                        is_mpr_client=True,
                        is_internal=False,
                        notes=f"[AI_RESEARCH_EXTRACTION 2025-10-18] {ext_client.get('notes', '')}"
                    )
                    self.session.add(new_company)
                    self.session.flush()  # Get the ID
                    logger.info(f"✓ Created company: {company_name} (ID: {new_company.company_id})")
                    self.stats['companies_created'] += 1

            except Exception as e:
                logger.error(f"Error processing company {company_name}: {e}")
                self.stats['errors'].append(f"Company '{company_name}': {str(e)}")
                self.session.rollback()

        self.session.commit()
        logger.info(f"Phase 1 Complete: Created {self.stats['companies_created']}, Updated {self.stats['companies_updated']}")

    def phase_2_external_personnel(self, data: Dict):
        """Phase 2: Upsert external personnel"""
        clients = data.get('clients', [])
        logger.info(f"Processing external personnel for {len(clients)} clients...")

        for client_data in clients:
            try:
                company_name = client_data['external_client']['company_name']
                company = self.session.query(Company).filter_by(company_name=company_name).first()

                if not company:
                    logger.warning(f"Company not found: {company_name}")
                    continue

                external_personnel_list = client_data.get('external_personnel', [])

                for person_data in external_personnel_list:
                    try:
                        full_name = person_data.get('contact_name')
                        role = person_data.get('contact_title')
                        personnel_id = person_data.get('personnel_id')
                        confidence = person_data.get('db_match_confidence', 0)

                        if not full_name:
                            logger.warning(f"Skipping personnel with no name in {company_name}")
                            continue

                        # Check if person exists
                        existing = None
                        if personnel_id:
                            # Try to find by ID first (high confidence)
                            existing = self.session.query(ExternalPersonnel).filter_by(
                                personnel_id=personnel_id
                            ).first()

                        if not existing:
                            # Try to find by name and company
                            existing = self.session.query(ExternalPersonnel).filter_by(
                                full_name=full_name,
                                company_id=company.company_id
                            ).first()

                        if existing:
                            # Update if confidence >= 0.85
                            if confidence >= 0.85:
                                existing.role = role
                                self.session.commit()
                                logger.info(f"✓ Updated personnel: {full_name} at {company_name} (conf: {confidence})")
                                self.stats['personnel_updated'] += 1
                        else:
                            # Create new
                            new_person = ExternalPersonnel(
                                full_name=full_name,
                                email=person_data.get('contact_email'),
                                phone=person_data.get('contact_phone'),
                                role=role,
                                company_id=company.company_id,
                                contact_type=person_data.get('relationship_to_mpr', 'General'),
                                is_active=True,
                                notes=f"[AI_RESEARCH_EXTRACTION 2025-10-18] Confidence: {confidence}"
                            )
                            self.session.add(new_person)
                            self.session.flush()
                            logger.info(f"✓ Created personnel: {full_name} at {company_name} (conf: {confidence})")
                            self.stats['personnel_created'] += 1

                    except Exception as e:
                        logger.error(f"Error processing personnel {full_name}: {e}")
                        self.stats['errors'].append(f"Personnel '{full_name}': {str(e)}")
                        self.session.rollback()

            except Exception as e:
                logger.error(f"Error processing client {company_name}: {e}")
                self.stats['errors'].append(f"Client '{company_name}': {str(e)}")
                self.session.rollback()

        self.session.commit()
        logger.info(f"Phase 2 Complete: Created {self.stats['personnel_created']}, Updated {self.stats['personnel_updated']}")

    def phase_3_client_profiles_and_roundtable(self, data: Dict):
        """Phase 3: Create client profiles with encrypted fields and roundtable entries"""
        clients = data.get('clients', [])
        logger.info(f"Processing client profiles for {len(clients)} clients...")

        for client_data in clients:
            try:
                company_name = client_data['external_client']['company_name']
                company = self.session.query(Company).filter_by(company_name=company_name).first()

                if not company:
                    logger.warning(f"Company not found: {company_name}")
                    continue

                # Check if client profile exists
                existing_profile = self.session.query(ClientProfile).filter_by(
                    company_id=company.company_id
                ).first()

                client_profile_data = client_data.get('client_profile', {})

                if existing_profile:
                    logger.info(f"Client profile already exists for {company_name}, skipping")
                else:
                    # Create client profile with encrypted fields
                    new_profile = ClientProfile(
                        company_id=company.company_id,
                        relationship_strength=client_profile_data.get('relationship_strength', 'Unknown'),
                        relationship_notes=client_profile_data.get('relationship_notes', ''),
                        client_priority=client_profile_data.get('client_priority', 'Unknown'),
                        client_status=client_profile_data.get('client_status', 'Active'),
                        last_contact_date=datetime.strptime('2025-10-18', '%Y-%m-%d').date(),
                        last_contact_type=client_profile_data.get('last_contact_type', 'Meeting/Review')
                    )
                    self.session.add(new_profile)
                    self.session.flush()
                    logger.info(f"✓ Created client profile for {company_name}")
                    self.stats['client_profiles_created'] += 1

                # Create roundtable entry
                roundtable_data = client_data.get('roundtable_entry', {})
                fields = roundtable_data.get('fields', {})

                new_roundtable = RoundtableHistory(
                    entity_type='Company',
                    entity_id=company.company_id,
                    discussion=fields.get('general_discussion', ''),
                    action_items='\n'.join(fields.get('next_steps', [])) if fields.get('next_steps') else '',
                    next_steps='\n'.join(fields.get('next_steps', [])) if fields.get('next_steps') else '',
                    client_near_term_focus='\n'.join(fields.get('client_near_term_focus_areas', [])) if fields.get('client_near_term_focus_areas') else '',
                    mpr_work_targets='\n'.join(fields.get('mpr_work_targets_goals', [])) if fields.get('mpr_work_targets_goals') else '',
                    client_strategic_objectives='\n'.join(fields.get('client_strategic_objectives_priorities', [])) if fields.get('client_strategic_objectives_priorities') else '',
                    created_by=1,  # System user or admin
                    created_timestamp=datetime(2025, 10, 18, 12, 0, 0)
                )
                self.session.add(new_roundtable)
                self.session.flush()
                logger.info(f"✓ Created roundtable entry for {company_name}")
                self.stats['roundtable_entries_created'] += 1

            except Exception as e:
                logger.error(f"Error processing client profile for {company_name}: {e}", exc_info=True)
                self.stats['errors'].append(f"Client Profile '{company_name}': {str(e)}")
                self.session.rollback()

        self.session.commit()
        logger.info(f"Phase 3 Complete: Created {self.stats['client_profiles_created']} profiles, {self.stats['roundtable_entries_created']} roundtable entries")

    def phase_4_relationships(self, data: Dict):
        """Phase 4: Link internal-external personnel relationships"""
        clients = data.get('clients', [])
        logger.info(f"Processing relationships for {len(clients)} clients...")

        for client_data in clients:
            try:
                company_name = client_data['external_client']['company_name']
                company = self.session.query(Company).filter_by(company_name=company_name).first()

                if not company:
                    logger.warning(f"Company not found: {company_name}")
                    continue

                # Get all external personnel for this company
                external_personnel = self.session.query(ExternalPersonnel).filter_by(
                    company_id=company.company_id
                ).all()

                # Get internal contacts
                internal_contacts = client_data.get('internal_contacts', [])

                for internal_contact in internal_contacts:
                    try:
                        employee_name = internal_contact.get('employee_name')

                        if not employee_name:
                            continue

                        # Try to find internal person (fuzzy match by last name)
                        last_name = employee_name.split()[-1] if employee_name else ""
                        internal_id = self.internal_staff_map.get(last_name.lower())

                        if not internal_id:
                            logger.warning(f"Could not find internal staff member: {employee_name}")
                            continue

                        relationship_type = internal_contact.get('relationship_type', 'supporting_contact')

                        # Link this internal person to all external personnel for this company
                        for ext_person in external_personnel:
                            # Check if relationship already exists
                            existing_rel = self.session.query(PersonnelRelationship).filter_by(
                                internal_personnel_id=internal_id,
                                external_personnel_id=ext_person.personnel_id
                            ).first()

                            if not existing_rel:
                                new_rel = PersonnelRelationship(
                                    internal_personnel_id=internal_id,
                                    external_personnel_id=ext_person.personnel_id,
                                    relationship_type=relationship_type,
                                    notes=internal_contact.get('relationship_notes', ''),
                                    is_active=True
                                )
                                self.session.add(new_rel)
                                self.stats['relationships_created'] += 1

                        logger.info(f"✓ Linked {employee_name} to {len(external_personnel)} personnel at {company_name}")

                    except Exception as e:
                        logger.error(f"Error processing internal contact {employee_name}: {e}")
                        self.stats['errors'].append(f"Relationship for '{employee_name}': {str(e)}")
                        self.session.rollback()

            except Exception as e:
                logger.error(f"Error processing relationships for {company_name}: {e}")
                self.stats['errors'].append(f"Relationships for '{company_name}': {str(e)}")
                self.session.rollback()

        self.session.commit()
        logger.info(f"Phase 4 Complete: Created {self.stats['relationships_created']} relationships")

    def print_summary(self):
        """Print import summary"""
        logger.info("\n" + "=" * 70)
        logger.info("IMPORT SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Companies Created:        {self.stats['companies_created']}")
        logger.info(f"Companies Updated:        {self.stats['companies_updated']}")
        logger.info(f"Personnel Created:        {self.stats['personnel_created']}")
        logger.info(f"Personnel Updated:        {self.stats['personnel_updated']}")
        logger.info(f"Client Profiles Created:  {self.stats['client_profiles_created']}")
        logger.info(f"Roundtable Entries:       {self.stats['roundtable_entries_created']}")
        logger.info(f"Relationships Created:    {self.stats['relationships_created']}")
        logger.info(f"Total Errors:             {len(self.stats['errors'])}")

        if self.stats['errors']:
            logger.info("\nErrors encountered:")
            for error in self.stats['errors']:
                logger.info(f"  - {error}")

        logger.info("=" * 70)


def main():
    # Default paths
    project_root = Path(__file__).parent
    db_path = project_root / "dev_nukeworks.sqlite"
    json_path = project_root / "AI_RESEARCH_EXTRACTION_2025-10-18.json"

    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        sys.exit(1)

    if not json_path.exists():
        logger.error(f"JSON file not found: {json_path}")
        sys.exit(1)

    logger.info(f"Starting import...")
    logger.info(f"Database: {db_path}")
    logger.info(f"JSON File: {json_path}")
    logger.info("")

    importer = JSONImporter(str(db_path), str(json_path))
    importer.init_app()
    importer.run()

    logger.info("\nImport script completed successfully!")


if __name__ == '__main__':
    main()

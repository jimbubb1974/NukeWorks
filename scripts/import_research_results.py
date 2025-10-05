#!/usr/bin/env python3
"""Import research_results.json into the NukeWorks database.

This script replaces existing vendor/project CRM seed data with the curated
research JSON snapshot. It clears the relevant tables, inserts fresh entities,
and then wires up the relationships. Any referenced slug missing from the JSON
will be created as a placeholder entry so referential integrity remains intact.

Usage:
    python scripts/import_research_results.py [--input research_results.json]
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OFFTAKER_ALIAS_MAP = {
    "meta": "meta-platforms",
}

VENDOR_PLACEHOLDERS = {
    "bwxt": {
        "vendor_name": "BWX Technologies (BWXT)",
        "notes": "Manufacturer of nuclear reactor components; placeholder generated from research relationships.",
        "sources": [],
    },
}

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from config import get_config
from app.__init__ import _ensure_product_columns
from app.models import (
    Base,
    Constructor,
    Offtaker,
    Operator,
    OwnerDeveloper,
    Personnel,
    Product,
    Project,
    TechnologyVendor,
)
from app.models.relationships import (
    OwnerVendorRelationship,
    PersonnelEntityRelationship,
    ProjectConstructorRelationship,
    ProjectOfftakerRelationship,
    ProjectOperatorRelationship,
    ProjectOwnerRelationship,
    ProjectVendorRelationship,
    VendorPreferredConstructor,
    VendorSupplierRelationship,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("research_results.json"),
        help="Path to research_results.json",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Configuration name to load (defaults to FLASK_ENV or development)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load data and report without committing changes",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def load_json(path: Path) -> Dict[str, Any]:
    logging.info("Loading data from %s", path)
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise SystemExit(f"Input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON: {exc}") from exc

    expected_top_level = {"metadata", "entities", "relationships"}
    missing = expected_top_level - data.keys()
    if missing:
        raise SystemExit(f"JSON missing top-level keys: {", ".join(sorted(missing))}")
    return data


def normalize_text(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    cleaned = value.replace("\u00a0", " ").strip()
    return cleaned or None


def join_sources(notes: Optional[str], sources: Optional[Iterable[str]]) -> Optional[str]:
    base = normalize_text(notes)
    cleaned_sources = [normalize_text(src) for src in (sources or []) if normalize_text(src)]
    if cleaned_sources:
        source_block = "Sources:\n" + "\n".join(cleaned_sources)
        if base:
            return f"{base}\n\n{source_block}"
        return source_block
    return base


def slug_to_title(slug: str) -> str:
    return " ".join(segment.capitalize() for segment in slug.replace("_", "-").split("-"))


class ImportContext:
    """Track entity IDs and placeholder creations during import."""

    def __init__(self) -> None:
        self.vendor_ids: Dict[str, int] = {}
        self.product_ids: Dict[str, int] = {}
        self.owner_ids: Dict[str, int] = {}
        self.constructor_ids: Dict[str, int] = {}
        self.operator_ids: Dict[str, int] = {}
        self.offtaker_ids: Dict[str, int] = {}
        self.project_ids: Dict[str, int] = {}
        self.personnel_ids: Dict[str, int] = {}
        self.placeholders: Dict[str, List[str]] = {
            "owners": [],
            "operators": [],
            "offtakers": [],
            "vendors": [],
        }
        self.skipped_relationships: List[str] = []


# ---------------------------------------------------------------------------
# Database setup and teardown helpers
# ---------------------------------------------------------------------------


def _ensure_additional_columns(engine) -> None:
    """Add schema columns expected by current models but missing in older DBs."""
    with engine.begin() as connection:
        project_columns = {row[1] for row in connection.execute(text('PRAGMA table_info(projects)'))}
        for column, ddl in {
            'latitude': 'REAL',
            'longitude': 'REAL',
        }.items():
            if column not in project_columns:
                logging.debug("Adding missing projects column %s", column)
                connection.execute(text(f"ALTER TABLE projects ADD COLUMN {column} {ddl}"))


def create_session(config_name: Optional[str] = None) -> Tuple[Session, Any]:
    config_obj = get_config(config_name)

    engine = create_engine(
        config_obj.SQLALCHEMY_DATABASE_URI,
        **config_obj.SQLALCHEMY_ENGINE_OPTIONS,
        future=True,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragmas(dbapi_conn, _):  # pragma: no cover - tested via integration
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    _ensure_product_columns(engine)
    _ensure_additional_columns(engine)
    SessionFactory = sessionmaker(bind=engine, future=True)
    session = SessionFactory()
    logging.debug("Connected to %s", config_obj.SQLALCHEMY_DATABASE_URI)
    return session, engine


def clear_existing_data(session: Session) -> None:
    """Remove existing records from dependent tables in safe order."""
    inspector = inspect(session.bind)
    existing_tables = set(inspector.get_table_names())
    tables_in_order = [
        "personnel_entity_relationships",
        "entity_team_members",
        "project_offtaker_relationships",
        "project_operator_relationships",
        "project_constructor_relationships",
        "project_vendor_relationships",
        "project_owner_relationships",
        "owner_vendor_relationships",
        "vendor_supplier_relationships",
        "vendor_preferred_constructor",
        "client_owner_relationships",
        "client_vendor_relationships",
        "client_project_relationships",
        "contact_log",
        "products",
        "technology_vendors",
        "projects",
        "constructors",
        "operators",
        "offtakers",
        "owners_developers",
    ]

    for table in tables_in_order:
        if table not in existing_tables:
            logging.debug("Skipping table %s (table not found)", table)
            continue
        logging.debug("Clearing table %s", table)
        session.execute(text(f"DELETE FROM {table}"))


# ---------------------------------------------------------------------------
# Entity insertion helpers
# ---------------------------------------------------------------------------


def insert_vendors(session: Session, data: Dict[str, Dict[str, Any]], ctx: ImportContext) -> None:
    for slug, entry in data.items():
        vendor = TechnologyVendor(
            vendor_name=normalize_text(entry.get("vendor_name")) or slug_to_title(slug),
            notes=join_sources(entry.get("notes"), entry.get("sources")),
        )
        session.add(vendor)
        session.flush()
        ctx.vendor_ids[slug] = vendor.vendor_id
        logging.debug("Inserted vendor %s -> id %s", slug, vendor.vendor_id)


def insert_products(session: Session, data: Dict[str, Dict[str, Any]], ctx: ImportContext) -> None:
    for slug, entry in data.items():
        vendor_slug = entry.get("vendor_slug")
        vendor_id = ctx.vendor_ids.get(vendor_slug)
        if not vendor_id:
            ctx.skipped_relationships.append(
                f"Product {slug} skipped: unknown vendor slug {vendor_slug}"
            )
            continue

        product = Product(
            product_name=normalize_text(entry.get("product_name")) or slug_to_title(slug),
            vendor_id=vendor_id,
            reactor_type=normalize_text(entry.get("reactor_type")),
            generation=normalize_text(entry.get("generation")),
            thermal_capacity=_to_float(entry.get("thermal_capacity")),
            gross_capacity_mwt=_to_float(entry.get("gross_capacity_mwt")),
            thermal_efficiency=_to_float(entry.get("thermal_efficiency")),
            fuel_type=normalize_text(entry.get("fuel_type")),
            fuel_enrichment=normalize_text(entry.get("fuel_enrichment")),
            burnup=_to_float(entry.get("burnup")),
            design_status=normalize_text(entry.get("design_status")),
            mpr_project_ids=normalize_text(entry.get("mpr_project_ids")),
            notes=join_sources(entry.get("notes"), entry.get("sources")),
        )
        session.add(product)
        session.flush()
        ctx.product_ids[slug] = product.product_id
        logging.debug("Inserted product %s -> id %s", slug, product.product_id)


def insert_owners(session: Session, data: Dict[str, Dict[str, Any]], ctx: ImportContext) -> None:
    for slug, entry in data.items():
        owner = OwnerDeveloper(
            company_name=normalize_text(entry.get("company_name")) or slug_to_title(slug),
            company_type=normalize_text(entry.get("company_type")),
            engagement_level=normalize_text(entry.get("engagement_level")),
            notes=join_sources(entry.get("notes"), entry.get("sources")),
        )
        session.add(owner)
        session.flush()
        ctx.owner_ids[slug] = owner.owner_id
        logging.debug("Inserted owner %s -> id %s", slug, owner.owner_id)


def insert_constructors(session: Session, data: Dict[str, Dict[str, Any]], ctx: ImportContext) -> None:
    for slug, entry in data.items():
        constructor = Constructor(
            company_name=normalize_text(entry.get("company_name")) or slug_to_title(slug),
            notes=join_sources(entry.get("notes"), entry.get("sources")),
        )
        session.add(constructor)
        session.flush()
        ctx.constructor_ids[slug] = constructor.constructor_id
        logging.debug("Inserted constructor %s -> id %s", slug, constructor.constructor_id)


def insert_operators(session: Session, data: Dict[str, Dict[str, Any]], ctx: ImportContext) -> None:
    for slug, entry in data.items():
        operator = Operator(
            company_name=normalize_text(entry.get("company_name")) or slug_to_title(slug),
            notes=join_sources(entry.get("notes"), entry.get("sources")),
        )
        session.add(operator)
        session.flush()
        ctx.operator_ids[slug] = operator.operator_id
        logging.debug("Inserted operator %s -> id %s", slug, operator.operator_id)


def insert_offtakers(session: Session, data: Dict[str, Dict[str, Any]], ctx: ImportContext) -> None:
    for slug, entry in data.items():
        offtaker = Offtaker(
            organization_name=normalize_text(entry.get("organization_name")) or slug_to_title(slug),
            sector=normalize_text(entry.get("sector")),
            notes=join_sources(entry.get("notes"), entry.get("sources")),
        )
        session.add(offtaker)
        session.flush()
        ctx.offtaker_ids[slug] = offtaker.offtaker_id
        logging.debug("Inserted offtaker %s -> id %s", slug, offtaker.offtaker_id)

    for alias, target in OFFTAKER_ALIAS_MAP.items():
        target_id = ctx.offtaker_ids.get(target)
        if target_id:
            ctx.offtaker_ids[alias] = target_id
            logging.debug("Aliased offtaker slug %s -> %s (id %s)", alias, target, target_id)


def insert_projects(session: Session, data: Dict[str, Dict[str, Any]], ctx: ImportContext) -> None:
    for slug, entry in data.items():
        project = Project(
            project_name=normalize_text(entry.get("project_name")) or slug_to_title(slug),
            location=normalize_text(entry.get("location")),
            project_status=normalize_text(entry.get("project_status")),
            licensing_approach=normalize_text(entry.get("licensing_approach")),
            configuration=normalize_text(entry.get("configuration")),
            project_schedule=normalize_text(entry.get("project_schedule")),
            target_cod=_parse_date(entry.get("target_cod")),
            notes=join_sources(entry.get("notes"), entry.get("sources")),
            firm_involvement=normalize_text(entry.get("firm_involvement")),
        )
        session.add(project)
        session.flush()
        ctx.project_ids[slug] = project.project_id
        logging.debug("Inserted project %s -> id %s", slug, project.project_id)


def insert_personnel(session: Session, data: Dict[str, Dict[str, Any]], ctx: ImportContext) -> None:
    for slug, entry in data.items():
        person = Personnel(
            full_name=normalize_text(entry.get("full_name")) or slug_to_title(slug),
            email=normalize_text(entry.get("email")),
            phone=normalize_text(entry.get("phone")),
            role=normalize_text(entry.get("role")),
            personnel_type=normalize_text(entry.get("personnel_type")),
            organization_id=None,
            organization_type=normalize_text(entry.get("organization_type")),
            notes=join_sources(entry.get("notes"), entry.get("sources")),
        )
        session.add(person)
        session.flush()
        ctx.personnel_ids[slug] = person.personnel_id
        logging.debug("Inserted personnel %s -> id %s", slug, person.personnel_id)


# ---------------------------------------------------------------------------
# Relationship insertion helpers
# ---------------------------------------------------------------------------


def insert_relationships(session: Session, data: Dict[str, List[Dict[str, Any]]], ctx: ImportContext) -> Dict[str, int]:
    counts = {
        "vendor_supplier": 0,
        "owner_vendor": 0,
        "project_vendor": 0,
        "project_constructor": 0,
        "project_operator": 0,
        "project_owner": 0,
        "project_offtaker": 0,
        "vendor_preferred_constructor": 0,
        "personnel_entity": 0,
    }

    for entry in data.get("vendor_supplier_relationships", []):
        vendor_id = ctx.vendor_ids.get(entry.get("vendor_slug"))
        supplier_id = ctx.vendor_ids.get(entry.get("supplier_slug"))
        if not vendor_id or not supplier_id:
            ctx.skipped_relationships.append(
                f"VendorSupplier {entry.get('relationship_key')} skipped (vendor:{entry.get('vendor_slug')} supplier:{entry.get('supplier_slug')})"
            )
            continue
        rel = VendorSupplierRelationship(
            vendor_id=vendor_id,
            supplier_id=supplier_id,
            component_type=normalize_text(entry.get("component_type")),
            is_confidential=bool(entry.get("is_confidential")),
            notes=join_sources(entry.get("notes"), entry.get("sources")),
        )
        session.add(rel)
        counts["vendor_supplier"] += 1

    for entry in data.get("owner_vendor_relationships", []):
        owner_id = ctx.owner_ids.get(entry.get("owner_slug"))
        vendor_id = ctx.vendor_ids.get(entry.get("vendor_slug"))
        if not owner_id or not vendor_id:
            ctx.skipped_relationships.append(
                f"OwnerVendor {entry.get('relationship_key', entry.get('owner_slug'))} skipped (owner:{entry.get('owner_slug')} vendor:{entry.get('vendor_slug')})"
            )
            continue
        rel = OwnerVendorRelationship(
            owner_id=owner_id,
            vendor_id=vendor_id,
            relationship_type=normalize_text(entry.get("relationship_type")),
            is_confidential=bool(entry.get("is_confidential")),
            notes=join_sources(entry.get("notes"), entry.get("sources")),
        )
        session.add(rel)
        counts["owner_vendor"] += 1

    for entry in data.get("project_vendor_relationships", []):
        project_id = ctx.project_ids.get(entry.get("project_slug"))
        vendor_id = ctx.vendor_ids.get(entry.get("vendor_slug"))
        if not project_id or not vendor_id:
            ctx.skipped_relationships.append(
                f"ProjectVendor {entry.get('relationship_key')} skipped (project:{entry.get('project_slug')} vendor:{entry.get('vendor_slug')})"
            )
            continue
        rel = ProjectVendorRelationship(
            project_id=project_id,
            vendor_id=vendor_id,
            is_confidential=bool(entry.get("is_confidential")),
            notes=join_sources(entry.get("notes"), entry.get("sources")),
        )
        session.add(rel)
        counts["project_vendor"] += 1

    for entry in data.get("project_constructor_relationships", []):
        project_id = ctx.project_ids.get(entry.get("project_slug"))
        constructor_id = ctx.constructor_ids.get(entry.get("constructor_slug"))
        if not project_id or not constructor_id:
            ctx.skipped_relationships.append(
                f"ProjectConstructor {entry.get('relationship_key')} skipped (project:{entry.get('project_slug')} constructor:{entry.get('constructor_slug')})"
            )
            continue
        rel = ProjectConstructorRelationship(
            project_id=project_id,
            constructor_id=constructor_id,
            is_confidential=bool(entry.get("is_confidential")),
            notes=join_sources(entry.get("notes"), entry.get("sources")),
        )
        session.add(rel)
        counts["project_constructor"] += 1

    for entry in data.get("project_operator_relationships", []):
        project_id = ctx.project_ids.get(entry.get("project_slug"))
        operator_id = ctx.operator_ids.get(entry.get("operator_slug"))
        if not project_id or not operator_id:
            ctx.skipped_relationships.append(
                f"ProjectOperator {entry.get('relationship_key')} skipped (project:{entry.get('project_slug')} operator:{entry.get('operator_slug')})"
            )
            continue
        rel = ProjectOperatorRelationship(
            project_id=project_id,
            operator_id=operator_id,
            is_confidential=bool(entry.get("is_confidential")),
            notes=join_sources(entry.get("notes"), entry.get("sources")),
        )
        session.add(rel)
        counts["project_operator"] += 1

    for entry in data.get("project_owner_relationships", []):
        project_id = ctx.project_ids.get(entry.get("project_slug"))
        owner_id = ctx.owner_ids.get(entry.get("owner_slug"))
        if not project_id or not owner_id:
            ctx.skipped_relationships.append(
                f"ProjectOwner {entry.get('relationship_key')} skipped (project:{entry.get('project_slug')} owner:{entry.get('owner_slug')})"
            )
            continue
        rel = ProjectOwnerRelationship(
            project_id=project_id,
            owner_id=owner_id,
            is_confidential=bool(entry.get("is_confidential")),
            notes=join_sources(entry.get("notes"), entry.get("sources")),
        )
        session.add(rel)
        counts["project_owner"] += 1

    for entry in data.get("project_offtaker_relationships", []):
        project_id = ctx.project_ids.get(entry.get("project_slug"))
        offtaker_id = ctx.offtaker_ids.get(entry.get("offtaker_slug"))
        if not project_id or not offtaker_id:
            ctx.skipped_relationships.append(
                f"ProjectOfftaker {entry.get('relationship_key')} skipped (project:{entry.get('project_slug')} offtaker:{entry.get('offtaker_slug')})"
            )
            continue
        rel = ProjectOfftakerRelationship(
            project_id=project_id,
            offtaker_id=offtaker_id,
            agreement_type=normalize_text(entry.get("agreement_type")),
            contracted_volume=normalize_text(entry.get("contracted_volume")),
            is_confidential=bool(entry.get("is_confidential")),
            notes=join_sources(entry.get("notes"), entry.get("sources")),
        )
        session.add(rel)
        counts["project_offtaker"] += 1

    for entry in data.get("vendor_preferred_constructor", []):
        project_id = ctx.constructor_ids.get(entry.get("constructor_slug"))
        vendor_id = ctx.vendor_ids.get(entry.get("vendor_slug"))
        if not vendor_id or not project_id:
            ctx.skipped_relationships.append(
                f"VendorPreferredConstructor skipped (vendor:{entry.get('vendor_slug')} constructor:{entry.get('constructor_slug')})"
            )
            continue
        rel = VendorPreferredConstructor(
            vendor_id=vendor_id,
            constructor_id=project_id,
            is_confidential=bool(entry.get("is_confidential")),
            preference_reason=normalize_text(entry.get("preference_reason")),
        )
        session.add(rel)
        counts["vendor_preferred_constructor"] += 1

    for entry in data.get("personnel_entity_relationships", []):
        personnel_id = ctx.personnel_ids.get(entry.get("personnel_slug"))
        if not personnel_id:
            ctx.skipped_relationships.append(
                f"PersonnelEntity skipped (personnel:{entry.get('personnel_slug')})"
            )
            continue
        rel = PersonnelEntityRelationship(
            personnel_id=personnel_id,
            entity_type=normalize_text(entry.get("entity_type")),
            entity_id=entry.get("entity_id"),
            role_at_entity=normalize_text(entry.get("role_at_entity")),
            is_confidential=bool(entry.get("is_confidential")),
            notes=join_sources(entry.get("notes"), entry.get("sources")),
        )
        session.add(rel)
        counts["personnel_entity"] += 1

    return counts


# ---------------------------------------------------------------------------
# Utility conversions
# ---------------------------------------------------------------------------


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.date()
        except ValueError:
            continue
    logging.warning("Could not parse date value '%s'", value)
    return None


# ---------------------------------------------------------------------------
# Pre-flight augmentation
# ---------------------------------------------------------------------------


def augment_entities(raw: Dict[str, Any]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Return mutable dictionaries keyed by slug, inserting placeholders if needed."""
    entities = raw["entities"]

    vendors = {entry["slug"]: dict(entry) for entry in entities.get("technology_vendors", [])}
    owners = {entry["slug"]: dict(entry) for entry in entities.get("owners_developers", [])}
    constructors = {entry["slug"]: dict(entry) for entry in entities.get("constructors", [])}
    operators = {entry["slug"]: dict(entry) for entry in entities.get("operators", [])}
    offtakers = {entry["slug"]: dict(entry) for entry in entities.get("offtakers", [])}
    projects = {entry["slug"]: dict(entry) for entry in entities.get("projects", [])}
    personnel = {entry.get("slug", f"person-{idx}"): dict(entry) for idx, entry in enumerate(entities.get("personnel", []))}
    products = {entry["slug"]: dict(entry) for entry in entities.get("products", [])}

    relationships = raw.get("relationships", {})

    # Ensure vendors for supplier relationships exist
    for rel in relationships.get("vendor_supplier_relationships", []):
        for key in ("vendor_slug", "supplier_slug"):
            slug = rel.get(key)
            if slug and slug not in vendors:
                placeholder = VENDOR_PLACEHOLDERS.get(slug, {})
                vendors[slug] = {
                    "slug": slug,
                    "vendor_name": placeholder.get("vendor_name") or slug_to_title(slug),
                    "notes": placeholder.get("notes"),
                    "sources": placeholder.get("sources", []),
                    "__placeholder__": True,
                }

    # Ensure owners exist for relationships
    owner_sources = {**owners}
    owner_sources.update({slug: data for slug, data in offtakers.items()})
    owner_sources.update({slug: data for slug, data in vendors.items()})

    required_owner_slugs = set()
    for rel in relationships.get("owner_vendor_relationships", []):
        if rel.get("owner_slug"):
            required_owner_slugs.add(rel["owner_slug"])
    for rel in relationships.get("project_owner_relationships", []):
        if rel.get("owner_slug"):
            required_owner_slugs.add(rel["owner_slug"])

    for slug in required_owner_slugs:
        if slug in owners:
            continue
        source = owner_sources.get(slug)
        owners[slug] = {
            "slug": slug,
            "company_name": source.get("company_name")
            or source.get("organization_name")
            or source.get("vendor_name")
            or slug_to_title(slug),
            "company_type": source.get("company_type"),
            "engagement_level": source.get("engagement_level"),
            "notes": source.get("notes"),
            "sources": source.get("sources", []),
            "__placeholder__": True,
        } if source else {
            "slug": slug,
            "company_name": slug_to_title(slug),
            "company_type": None,
            "engagement_level": None,
            "notes": f"Auto-generated placeholder for owner {slug}",
            "sources": [],
            "__placeholder__": True,
        }

    # Ensure operators exist
    operator_sources = {**operators, **owners}
    for rel in relationships.get("project_operator_relationships", []):
        slug = rel.get("operator_slug")
        if not slug or slug in operators:
            continue
        source = operator_sources.get(slug)
        operators[slug] = {
            "slug": slug,
            "company_name": source.get("company_name") if source else slug_to_title(slug),
            "notes": source.get("notes") if source else f"Auto-generated placeholder for operator {slug}",
            "sources": source.get("sources", []) if source else [],
            "__placeholder__": True,
        }

    # Ensure offtakers exist
    for rel in relationships.get("project_offtaker_relationships", []):
        slug = rel.get("offtaker_slug")
        if not slug:
            continue
        target_slug = OFFTAKER_ALIAS_MAP.get(slug)
        if target_slug and target_slug in offtakers:
            continue
        if slug not in offtakers:
            offtakers[slug] = {
                "slug": slug,
                "organization_name": slug_to_title(slug),
                "sector": None,
                "notes": f"Auto-generated placeholder for offtaker {slug}",
                "sources": [],
                "__placeholder__": True,
            }

    return {
        "vendors": vendors,
        "products": products,
        "owners": owners,
        "constructors": constructors,
        "operators": operators,
        "offtakers": offtakers,
        "projects": projects,
        "personnel": personnel,
    }


# ---------------------------------------------------------------------------
# Main routine
# ---------------------------------------------------------------------------


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)
    payload = load_json(args.input)

    entity_maps = augment_entities(payload)
    ctx = ImportContext()

    session, engine = create_session(args.config)
    relationship_counts: Dict[str, int] = {
        "vendor_supplier": 0,
        "owner_vendor": 0,
        "project_vendor": 0,
        "project_constructor": 0,
        "project_operator": 0,
        "project_owner": 0,
        "project_offtaker": 0,
        "vendor_preferred_constructor": 0,
        "personnel_entity": 0,
    }
    committed = False

    try:
        try:
            clear_existing_data(session)

            insert_vendors(session, entity_maps["vendors"], ctx)
            insert_products(session, entity_maps["products"], ctx)
            insert_owners(session, entity_maps["owners"], ctx)
            insert_constructors(session, entity_maps["constructors"], ctx)
            insert_operators(session, entity_maps["operators"], ctx)
            insert_offtakers(session, entity_maps["offtakers"], ctx)
            insert_projects(session, entity_maps["projects"], ctx)

            relationship_counts = insert_relationships(
                session=session,
                data=payload.get("relationships", {}),
                ctx=ctx,
            )

            if args.dry_run:
                logging.info("Dry-run enabled -> rolling back transaction")
                session.rollback()
            else:
                session.commit()
                committed = True
        except Exception:
            session.rollback()
            raise
    finally:
        session.close()
        engine.dispose()

    # Reporting
    unique_offtaker_count = len(set(ctx.offtaker_ids.values()))

    print("\n=== Import Summary ===")
    print(f"Vendors inserted: {len(ctx.vendor_ids)}")
    print(f"Products inserted: {len(ctx.product_ids)}")
    print(f"Owners inserted: {len(ctx.owner_ids)}")
    print(f"Constructors inserted: {len(ctx.constructor_ids)}")
    print(f"Operators inserted: {len(ctx.operator_ids)}")
    print(f"Offtakers inserted: {unique_offtaker_count}")
    print(f"Projects inserted: {len(ctx.project_ids)}")
    print(f"Personnel inserted: {len(ctx.personnel_ids)}")

    for rel_name, count in relationship_counts.items():
        print(f"{rel_name.replace('_', ' ').title()} relationships: {count}")

    placeholder_summary = {
        key: [slug for slug, data in entity_maps[label].items() if data.get("__placeholder__")]
        for key, label in (
            ("vendors", "vendors"),
            ("owners", "owners"),
            ("operators", "operators"),
            ("offtakers", "offtakers"),
        )
    }

    for key, slugs in placeholder_summary.items():
        if slugs:
            print(f"Placeholder {key}: {', '.join(sorted(slugs))}")

    if ctx.skipped_relationships:
        print("\nSkipped relationships:")
        for item in ctx.skipped_relationships:
            print(f" - {item}")

    if args.dry_run:
        print("\nDry-run complete. No changes were committed.")
    elif committed:
        print("\nImport completed and committed successfully.")


if __name__ == "__main__":
    main()

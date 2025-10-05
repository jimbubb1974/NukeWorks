"""Network diagram data serialization utilities."""
from collections import defaultdict, deque
from typing import Any, Dict, Iterable, List, Optional, Tuple

from flask import url_for
from sqlalchemy.orm import joinedload

from app import db_session
from app.models import (
    Company,
    CompanyRoleAssignment,
    OwnerVendorRelationship,
    Project,
    ProjectOwnerRelationship,
    ProjectVendorRelationship,
    ProjectConstructorRelationship,
    ProjectOperatorRelationship,
    ProjectOfftakerRelationship,
    VendorPreferredConstructor,
    VendorSupplierRelationship,
)
from app.utils.permissions import can_view_relationship

DEFAULT_ENTITY_TYPES: Tuple[str, ...] = ("company", "project")
DEFAULT_RELATIONSHIP_TYPES: Tuple[str, ...] = (
    "project_vendor",
    "project_owner",
    "project_constructor",
    "project_operator",
    "project_offtaker",
    "owner_vendor",
    "vendor_supplier",
    "vendor_constructor",
)


def _build_project_node(project: Project) -> Dict[str, Any]:
    details = []
    if project.project_status:
        details.append(f"Status: {project.project_status}")
    if project.location:
        details.append(f"Location: {project.location}")

    title = f"Project: {project.project_name}"
    if details:
        title = f"{title}\n" + "\n".join(details)

    return {
        "id": f"project_{project.project_id}",
        "label": project.project_name,
        "group": "project",
        "title": title,
        "url": url_for("projects.view_project", project_id=project.project_id),
    }


def _build_company_node(company: Company) -> Dict[str, Any]:
    details = []
    if company.company_type:
        details.append(f"Type: {company.company_type}")
    if company.is_mpr_client:
        details.append("MPR Client")
    if company.notes:
        preview = company.notes.splitlines()[0]
        details.append(f"Notes: {preview[:120]}{'…' if len(preview) > 120 else ''}")

    title = f"Company: {company.company_name}"
    if details:
        title = f"{title}\n" + "\n".join(details)

    return {
        "id": f"company_{company.company_id}",
        "label": company.company_name,
        "group": "company",
        "title": title,
        "url": url_for('companies.list_companies') + f"#company-{company.company_id}",
    }


def _fetch_nodes_by_type(entity_types: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    nodes: Dict[str, Dict[str, Any]] = {}

    if "company" in entity_types:
        for company in db_session.query(Company).order_by(Company.company_name).all():
            node = _build_company_node(company)
            nodes[node["id"]] = node

    if "project" in entity_types:
        for project in db_session.query(Project).order_by(Project.project_name).all():
            node = _build_project_node(project)
            nodes[node["id"]] = node

    return nodes


def _build_assignment_index() -> Dict[Tuple[str, int], CompanyRoleAssignment]:
    assignments = (
        db_session.query(CompanyRoleAssignment)
        .options(
            joinedload(CompanyRoleAssignment.company),
            joinedload(CompanyRoleAssignment.role),
        )
        .all()
    )
    index: Dict[Tuple[str, int], CompanyRoleAssignment] = {}
    for assignment in assignments:
        if assignment.context_id is None:
            continue
        key = (assignment.context_type, assignment.context_id)
        if key not in index:
            index[key] = assignment
    return index


def _company_node_for(
    assignment_index: Dict[Tuple[str, int], CompanyRoleAssignment],
    context_type: str,
    context_id: Optional[int],
) -> Tuple[Optional[str], Optional[CompanyRoleAssignment]]:
    if context_id is None:
        return None, None
    assignment = assignment_index.get((context_type, context_id))
    if not assignment:
        return None, None
    return f"company_{assignment.company_id}", assignment


def _owner_vendor_edges(
    user,
    entity_types: Iterable[str],
    nodes: Dict[str, Dict[str, Any]],
    assignment_index: Dict[Tuple[str, int], CompanyRoleAssignment],
) -> Tuple[List[Dict[str, Any]], int]:
    edges: List[Dict[str, Any]] = []
    hidden = 0
    if "company" not in entity_types:
        return edges, hidden
    query = db_session.query(OwnerVendorRelationship).options(
        joinedload(OwnerVendorRelationship.owner),
        joinedload(OwnerVendorRelationship.vendor),
    )
    for rel in query.all():
        if not can_view_relationship(user, rel):
            hidden += 1
            continue
        owner_node, owner_assignment = _company_node_for(assignment_index, "OwnerRecord", rel.owner_id)
        vendor_node, vendor_assignment = _company_node_for(assignment_index, "VendorRecord", rel.vendor_id)
        if not owner_node or not vendor_node:
            continue
        if owner_node not in nodes or vendor_node not in nodes:
            continue
        label = rel.relationship_type or "Owner ↔ Vendor"
        title = label
        if owner_assignment and vendor_assignment:
            title = (
                f"{owner_assignment.company.company_name} ↔ {vendor_assignment.company.company_name}"
            )
            if rel.relationship_type:
                title += f"\nType: {rel.relationship_type}"
        edges.append(
            {
                "id": f"owner_vendor_{rel.relationship_id}",
                "from": owner_node,
                "to": vendor_node,
                "label": label,
                "title": title,
            }
        )
    return edges, hidden


def _vendor_supplier_edges(
    user,
    entity_types: Iterable[str],
    nodes: Dict[str, Dict[str, Any]],
    assignment_index: Dict[Tuple[str, int], CompanyRoleAssignment],
) -> Tuple[List[Dict[str, Any]], int]:
    edges: List[Dict[str, Any]] = []
    hidden = 0
    if "company" not in entity_types:
        return edges, hidden
    query = db_session.query(VendorSupplierRelationship).options(
        joinedload(VendorSupplierRelationship.vendor),
        joinedload(VendorSupplierRelationship.supplier),
    )
    for rel in query.all():
        if not can_view_relationship(user, rel):
            hidden += 1
            continue
        supplier_node, supplier_assignment = _company_node_for(assignment_index, "VendorRecord", rel.supplier_id)
        vendor_node, vendor_assignment = _company_node_for(assignment_index, "VendorRecord", rel.vendor_id)
        if not supplier_node or not vendor_node:
            continue
        if supplier_node not in nodes or vendor_node not in nodes:
            continue
        label = rel.component_type or "Supplier"
        title = label
        if supplier_assignment and vendor_assignment:
            title = (
                f"{supplier_assignment.company.company_name} supplies {vendor_assignment.company.company_name}"
            )
        edges.append(
            {
                "id": f"vendor_supplier_{rel.relationship_id}",
                "from": supplier_node,
                "to": vendor_node,
                "label": label,
                "title": title,
                "arrows": "to",
            }
        )
    return edges, hidden


def _vendor_constructor_edges(
    user,
    entity_types: Iterable[str],
    nodes: Dict[str, Dict[str, Any]],
    assignment_index: Dict[Tuple[str, int], CompanyRoleAssignment],
) -> Tuple[List[Dict[str, Any]], int]:
    edges: List[Dict[str, Any]] = []
    hidden = 0
    if "company" not in entity_types:
        return edges, hidden
    query = db_session.query(VendorPreferredConstructor).options(
        joinedload(VendorPreferredConstructor.vendor),
        joinedload(VendorPreferredConstructor.constructor),
    )
    for rel in query.all():
        if not can_view_relationship(user, rel):
            hidden += 1
            continue
        vendor_node, vendor_assignment = _company_node_for(assignment_index, "VendorRecord", rel.vendor_id)
        constructor_node, constructor_assignment = _company_node_for(assignment_index, "ConstructorRecord", rel.constructor_id)
        if not vendor_node or not constructor_node:
            continue
        if vendor_node not in nodes or constructor_node not in nodes:
            continue
        title = "Preferred constructor"
        if vendor_assignment and constructor_assignment:
            title = (
                f"{vendor_assignment.company.company_name} prefers {constructor_assignment.company.company_name}"
            )
        edges.append(
            {
                "id": f"vendor_constructor_{rel.relationship_id}",
                "from": vendor_node,
                "to": constructor_node,
                "label": "Preferred",
                "title": title,
            }
        )
    return edges, hidden


def _project_vendor_edges(
    user,
    entity_types: Iterable[str],
    nodes: Dict[str, Dict[str, Any]],
    assignment_index: Dict[Tuple[str, int], CompanyRoleAssignment],
) -> Tuple[List[Dict[str, Any]], int]:
    edges: List[Dict[str, Any]] = []
    hidden = 0
    if "company" not in entity_types or "project" not in entity_types:
        return edges, hidden
    query = db_session.query(ProjectVendorRelationship).options(
        joinedload(ProjectVendorRelationship.project),
        joinedload(ProjectVendorRelationship.vendor),
    )
    for rel in query.all():
        if not can_view_relationship(user, rel):
            hidden += 1
            continue
        vendor_node, vendor_assignment = _company_node_for(assignment_index, "VendorRecord", rel.vendor_id)
        project_node = f"project_{rel.project_id}"
        if not vendor_node or project_node not in nodes:
            continue
        if vendor_node not in nodes:
            continue
        title = "Vendor involved with project"
        if vendor_assignment and rel.project:
            title = f"{vendor_assignment.company.company_name} ↔ {rel.project.project_name}"
        edges.append(
            {
                "id": f"project_vendor_{rel.relationship_id}",
                "from": vendor_node,
                "to": project_node,
                "label": "Vendor",
                "title": title,
            }
        )
    return edges, hidden


def _project_owner_edges(
    user,
    entity_types: Iterable[str],
    nodes: Dict[str, Dict[str, Any]],
    assignment_index: Dict[Tuple[str, int], CompanyRoleAssignment],
) -> Tuple[List[Dict[str, Any]], int]:
    edges: List[Dict[str, Any]] = []
    hidden = 0
    if "company" not in entity_types or "project" not in entity_types:
        return edges, hidden
    query = db_session.query(ProjectOwnerRelationship).options(
        joinedload(ProjectOwnerRelationship.project),
        joinedload(ProjectOwnerRelationship.owner),
    )
    for rel in query.all():
        if not can_view_relationship(user, rel):
            hidden += 1
            continue
        owner_node, owner_assignment = _company_node_for(assignment_index, "OwnerRecord", rel.owner_id)
        project_node = f"project_{rel.project_id}"
        if not owner_node or project_node not in nodes:
            continue
        if owner_node not in nodes:
            continue
        title = "Owner relationship"
        if owner_assignment and rel.project:
            title = f"{owner_assignment.company.company_name} ↔ {rel.project.project_name}"
        edges.append(
            {
                "id": f"project_owner_{rel.relationship_id}",
                "from": owner_node,
                "to": project_node,
                "label": "Owner",
                "title": title,
            }
        )
    return edges, hidden


def _project_constructor_edges(
    user,
    entity_types: Iterable[str],
    nodes: Dict[str, Dict[str, Any]],
    assignment_index: Dict[Tuple[str, int], CompanyRoleAssignment],
) -> Tuple[List[Dict[str, Any]], int]:
    edges: List[Dict[str, Any]] = []
    hidden = 0
    if "company" not in entity_types or "project" not in entity_types:
        return edges, hidden
    query = db_session.query(ProjectConstructorRelationship).options(
        joinedload(ProjectConstructorRelationship.project),
        joinedload(ProjectConstructorRelationship.constructor),
    )
    for rel in query.all():
        if not can_view_relationship(user, rel):
            hidden += 1
            continue
        constructor_node, constructor_assignment = _company_node_for(assignment_index, "ConstructorRecord", rel.constructor_id)
        project_node = f"project_{rel.project_id}"
        if not constructor_node or project_node not in nodes:
            continue
        if constructor_node not in nodes:
            continue
        title = "Constructor relationship"
        if constructor_assignment and rel.project:
            title = f"{constructor_assignment.company.company_name} ↔ {rel.project.project_name}"
        edges.append(
            {
                "id": f"project_constructor_{rel.relationship_id}",
                "from": constructor_node,
                "to": project_node,
                "label": "Constructor",
                "title": title,
            }
        )
    return edges, hidden


def _project_operator_edges(
    user,
    entity_types: Iterable[str],
    nodes: Dict[str, Dict[str, Any]],
    assignment_index: Dict[Tuple[str, int], CompanyRoleAssignment],
) -> Tuple[List[Dict[str, Any]], int]:
    edges: List[Dict[str, Any]] = []
    hidden = 0
    if "company" not in entity_types or "project" not in entity_types:
        return edges, hidden
    query = db_session.query(ProjectOperatorRelationship).options(
        joinedload(ProjectOperatorRelationship.project),
        joinedload(ProjectOperatorRelationship.operator),
    )
    for rel in query.all():
        if not can_view_relationship(user, rel):
            hidden += 1
            continue
        operator_node, operator_assignment = _company_node_for(assignment_index, "OperatorRecord", rel.operator_id)
        project_node = f"project_{rel.project_id}"
        if not operator_node or project_node not in nodes:
            continue
        if operator_node not in nodes:
            continue
        title = "Operator relationship"
        if operator_assignment and rel.project:
            title = f"{operator_assignment.company.company_name} ↔ {rel.project.project_name}"
        edges.append(
            {
                "id": f"project_operator_{rel.relationship_id}",
                "from": operator_node,
                "to": project_node,
                "label": "Operator",
                "title": title,
            }
        )
    return edges, hidden


def _project_offtaker_edges(
    user,
    entity_types: Iterable[str],
    nodes: Dict[str, Dict[str, Any]],
    assignment_index: Dict[Tuple[str, int], CompanyRoleAssignment],
) -> Tuple[List[Dict[str, Any]], int]:
    edges: List[Dict[str, Any]] = []
    hidden = 0
    if "company" not in entity_types or "project" not in entity_types:
        return edges, hidden
    query = db_session.query(ProjectOfftakerRelationship).options(
        joinedload(ProjectOfftakerRelationship.project),
        joinedload(ProjectOfftakerRelationship.offtaker),
    )
    for rel in query.all():
        if not can_view_relationship(user, rel):
            hidden += 1
            continue
        offtaker_node, offtaker_assignment = _company_node_for(assignment_index, "OfftakerRecord", rel.offtaker_id)
        project_node = f"project_{rel.project_id}"
        if not offtaker_node or project_node not in nodes:
            continue
        if offtaker_node not in nodes:
            continue
        label = rel.agreement_type or "Off-taker"
        title = label
        if offtaker_assignment and rel.project:
            title = f"{offtaker_assignment.company.company_name} ↔ {rel.project.project_name}"
            if rel.agreement_type:
                title += f"\nType: {rel.agreement_type}"
        edges.append(
            {
                "id": f"project_offtaker_{rel.relationship_id}",
                "from": offtaker_node,
                "to": project_node,
                "label": label,
                "title": title,
            }
        )
    return edges, hidden

EDGE_BUILDERS = {
    "owner_vendor": _owner_vendor_edges,
    "vendor_supplier": _vendor_supplier_edges,
    "vendor_constructor": _vendor_constructor_edges,
    "project_vendor": _project_vendor_edges,
    "project_owner": _project_owner_edges,
    "project_constructor": _project_constructor_edges,
    "project_operator": _project_operator_edges,
    "project_offtaker": _project_offtaker_edges,
}



def _apply_focus_filter(
    nodes: Dict[str, Dict[str, Any]],
    edges: List[Dict[str, Any]],
    focus_entity: Optional[Dict[str, Any]],
    depth_value: Any,
) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
    if not focus_entity:
        return nodes, edges

    try:
        depth = None if depth_value in (None, "all") else int(depth_value)
    except (ValueError, TypeError):
        depth = None

    if depth is None:
        return nodes, edges

    focus_id = f"{focus_entity.get('type')}_{focus_entity.get('id')}"
    if focus_id not in nodes:
        return nodes, edges

    adjacency: Dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        adjacency[edge["from"]].add(edge["to"])
        adjacency[edge["to"]].add(edge["from"])

    visible_nodes = {focus_id}
    visited: set[str] = set()
    queue: deque[Tuple[str, int]] = deque([(focus_id, 0)])

    while queue:
        node_id, current_depth = queue.popleft()
        if node_id in visited:
            continue
        visited.add(node_id)

        if current_depth >= depth:
            continue

        for neighbor in adjacency.get(node_id, set()):
            if neighbor not in visible_nodes:
                visible_nodes.add(neighbor)
            queue.append((neighbor, current_depth + 1))

    filtered_nodes = {node_id: nodes[node_id] for node_id in visible_nodes if node_id in nodes}
    filtered_edges = [edge for edge in edges if edge["from"] in visible_nodes and edge["to"] in visible_nodes]

    return filtered_nodes, filtered_edges


def get_network_data(user, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    filters = filters or {}
    entity_types = tuple(filters.get("entity_types") or DEFAULT_ENTITY_TYPES)
    relationship_types = tuple(filters.get("relationship_types") or DEFAULT_RELATIONSHIP_TYPES)

    nodes = _fetch_nodes_by_type(entity_types)
    assignment_index = _build_assignment_index()

    edges: List[Dict[str, Any]] = []
    confidential_hidden = 0

    for rel_type in relationship_types:
        builder = EDGE_BUILDERS.get(rel_type)
        if not builder:
            continue
        new_edges, hidden = builder(user, entity_types, nodes, assignment_index)
        edges.extend(new_edges)
        confidential_hidden += hidden

    focused_nodes, focused_edges = _apply_focus_filter(
        nodes,
        edges,
        filters.get("focus_entity"),
        filters.get("depth"),
    )

    stats_by_type: Dict[str, int] = defaultdict(int)
    for node in focused_nodes.values():
        stats_by_type[node.get("group", "unknown")] += 1

    stats = {
        "total_nodes": len(focused_nodes),
        "total_edges": len(focused_edges),
        "by_type": dict(stats_by_type),
        "confidential_hidden": confidential_hidden,
    }

    return {
        "nodes": list(focused_nodes.values()),
        "edges": focused_edges,
        "stats": stats,
    }


__all__ = ["get_network_data"]

"""Network diagram data serialization utilities."""
from collections import defaultdict, deque
from typing import Any, Dict, Iterable, List, Optional, Tuple

from flask import url_for

from app import db_session
from app.models import (
    Constructor,
    Offtaker,
    Operator,
    OwnerDeveloper,
    OwnerVendorRelationship,
    Project,
    ProjectConstructorRelationship,
    ProjectOfftakerRelationship,
    ProjectOperatorRelationship,
    ProjectOwnerRelationship,
    ProjectVendorRelationship,
    TechnologyVendor,
    VendorPreferredConstructor,
    VendorSupplierRelationship,
)
from app.utils.permissions import can_view_relationship

# Supported entity and relationship types (mirrors docs/11_NETWORK_DIAGRAM.md)
DEFAULT_ENTITY_TYPES: Tuple[str, ...] = (
    "vendor",
    "owner",
    "project",
    "constructor",
    "operator",
    "offtaker",
)

DEFAULT_RELATIONSHIP_TYPES: Tuple[str, ...] = (
    "owner_vendor",
    "project_vendor",
    "project_owner",
    "project_constructor",
    "project_operator",
    "vendor_supplier",
    "vendor_constructor",
    "project_offtaker",
)


def _build_vendor_node(vendor: TechnologyVendor) -> Dict[str, Any]:
    return {
        "id": f"vendor_{vendor.vendor_id}",
        "label": vendor.vendor_name,
        "group": "vendor",
        "title": f"Vendor: {vendor.vendor_name}",
        "url": url_for("vendors.view_vendor", vendor_id=vendor.vendor_id),
    }


def _build_owner_node(owner: OwnerDeveloper) -> Dict[str, Any]:
    details = []
    if owner.company_type:
        details.append(f"Type: {owner.company_type}")
    if owner.engagement_level:
        details.append(f"Engagement: {owner.engagement_level}")

    title = "Owner: {name}".format(name=owner.company_name)
    if details:
        title = f"{title}\n" + "\n".join(details)

    return {
        "id": f"owner_{owner.owner_id}",
        "label": owner.company_name,
        "group": "owner",
        "title": title,
        "url": url_for("owners.view_owner", owner_id=owner.owner_id),
    }


def _build_project_node(project: Project) -> Dict[str, Any]:
    details = []
    if project.project_status:
        details.append(f"Status: {project.project_status}")
    if project.location:
        details.append(f"Location: {project.location}")

    title = "Project: {name}".format(name=project.project_name)
    if details:
        title = f"{title}\n" + "\n".join(details)

    return {
        "id": f"project_{project.project_id}",
        "label": project.project_name,
        "group": "project",
        "title": title,
        "url": url_for("projects.view_project", project_id=project.project_id),
    }


def _build_constructor_node(constructor: Constructor) -> Dict[str, Any]:
    return {
        "id": f"constructor_{constructor.constructor_id}",
        "label": constructor.company_name,
        "group": "constructor",
        "title": f"Constructor: {constructor.company_name}",
        "url": None,  # Constructor detail pages are not implemented yet
    }


def _build_operator_node(operator: Operator) -> Dict[str, Any]:
    return {
        "id": f"operator_{operator.operator_id}",
        "label": operator.company_name,
        "group": "operator",
        "title": f"Operator: {operator.company_name}",
        "url": None,  # Operator detail pages are not implemented yet
    }


def _build_offtaker_node(offtaker: Offtaker) -> Dict[str, Any]:
    details = []
    if offtaker.sector:
        details.append(f"Sector: {offtaker.sector}")

    notes_preview = (offtaker.notes or "").strip()
    if notes_preview:
        preview = notes_preview.splitlines()[0]
        details.append(f"Notes: {preview[:120]}{'…' if len(preview) > 120 else ''}")

    title = f"Off-taker: {offtaker.organization_name}"
    if details:
        title = f"{title}\n" + "\n".join(details)

    return {
        "id": f"offtaker_{offtaker.offtaker_id}",
        "label": offtaker.organization_name,
        "group": "offtaker",
        "title": title,
        "url": url_for("offtakers.view_offtaker", offtaker_id=offtaker.offtaker_id),
    }


NODE_BUILDERS = {
    "vendor": _build_vendor_node,
    "owner": _build_owner_node,
    "project": _build_project_node,
    "constructor": _build_constructor_node,
    "operator": _build_operator_node,
    "offtaker": _build_offtaker_node,
}


def _relationship_configs():
    """Return relationship configuration mapping.

    Lazy function to avoid circular imports when module is imported at app start.
    """

    return {
        "owner_vendor": {
            "model": OwnerVendorRelationship,
            "endpoints": ("owner", "vendor"),
            "id_fields": ("owner_id", "vendor_id"),
            "label": lambda rel: rel.relationship_type or "Owner ↔ Vendor",
            "title": lambda rel: rel.relationship_type or "Owner ↔ Vendor",
            "style": lambda rel: {"dashes": (rel.relationship_type or "").lower() == "mou"},
        },
        "project_vendor": {
            "model": ProjectVendorRelationship,
            "endpoints": ("project", "vendor"),
            "id_fields": ("project_id", "vendor_id"),
            "label": lambda rel: "Vendor",
            "title": lambda rel: "Vendor involved with project",
            "style": lambda rel: {},
        },
        "project_owner": {
            "model": ProjectOwnerRelationship,
            "endpoints": ("project", "owner"),
            "id_fields": ("project_id", "owner_id"),
            "label": lambda rel: "Owner",
            "title": lambda rel: "Owner relationship",
            "style": lambda rel: {},
        },
        "project_constructor": {
            "model": ProjectConstructorRelationship,
            "endpoints": ("project", "constructor"),
            "id_fields": ("project_id", "constructor_id"),
            "label": lambda rel: "Constructor",
            "title": lambda rel: "Constructor relationship",
            "style": lambda rel: {},
        },
        "project_operator": {
            "model": ProjectOperatorRelationship,
            "endpoints": ("project", "operator"),
            "id_fields": ("project_id", "operator_id"),
            "label": lambda rel: "Operator",
            "title": lambda rel: "Operator relationship",
            "style": lambda rel: {},
        },
        "project_offtaker": {
            "model": ProjectOfftakerRelationship,
            "endpoints": ("project", "offtaker"),
            "id_fields": ("project_id", "offtaker_id"),
            "label": lambda rel: rel.agreement_type or "Off-taker",
            "title": lambda rel: rel.agreement_type or "Off-taker relationship",
            "style": lambda rel: {},
        },
        "vendor_supplier": {
            "model": VendorSupplierRelationship,
            "endpoints": ("vendor", "vendor"),
            "id_fields": ("supplier_id", "vendor_id"),
            "label": lambda rel: rel.component_type or "Supplier",
            "title": lambda rel: rel.component_type or "Supplier",
            "style": lambda rel: {"arrows": "to"},
        },
        "vendor_constructor": {
            "model": VendorPreferredConstructor,
            "endpoints": ("vendor", "constructor"),
            "id_fields": ("vendor_id", "constructor_id"),
            "label": lambda rel: "Preferred",
            "title": lambda rel: "Preferred constructor",
            "style": lambda rel: {},
        },
    }


def _fetch_nodes_by_type(entity_types: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    """Fetch all nodes for the requested entity types."""
    nodes: Dict[str, Dict[str, Any]] = {}

    if "vendor" in entity_types:
        for vendor in db_session.query(TechnologyVendor).order_by(TechnologyVendor.vendor_name).all():
            node = NODE_BUILDERS["vendor"](vendor)
            nodes[node["id"]] = node

    if "owner" in entity_types:
        for owner in db_session.query(OwnerDeveloper).order_by(OwnerDeveloper.company_name).all():
            node = NODE_BUILDERS["owner"](owner)
            nodes[node["id"]] = node

    if "project" in entity_types:
        for project in db_session.query(Project).order_by(Project.project_name).all():
            node = NODE_BUILDERS["project"](project)
            nodes[node["id"]] = node

    if "constructor" in entity_types:
        for constructor in db_session.query(Constructor).order_by(Constructor.company_name).all():
            node = NODE_BUILDERS["constructor"](constructor)
            nodes[node["id"]] = node

    if "operator" in entity_types:
        for operator in db_session.query(Operator).order_by(Operator.company_name).all():
            node = NODE_BUILDERS["operator"](operator)
            nodes[node["id"]] = node

    if "offtaker" in entity_types:
        for offtaker in db_session.query(Offtaker).order_by(Offtaker.organization_name).all():
            node = NODE_BUILDERS["offtaker"](offtaker)
            nodes[node["id"]] = node

    return nodes


def _build_edge(rel_type: str, rel: Any) -> Dict[str, Any]:
    """Serialize a relationship into an edge dict."""
    config = _relationship_configs()[rel_type]
    from_type, to_type = config["endpoints"]
    from_field, to_field = config["id_fields"]

    edge = {
        "id": f"{rel_type}_{getattr(rel, 'relationship_id', getattr(rel, 'id', ''))}",
        "from": f"{from_type}_{getattr(rel, from_field)}",
        "to": f"{to_type}_{getattr(rel, to_field)}",
        "label": config["label"](rel),
        "title": config["title"](rel),
        "type": rel_type,
    }

    style = config["style"](rel)
    if style:
        edge.update(style)
    return edge


def _filter_edges_for_entities(edge: Dict[str, Any], entity_types: Iterable[str]) -> bool:
    """Return True if edge endpoints align with entity filter."""
    from_type = edge["from"].split("_", 1)[0]
    to_type = edge["to"].split("_", 1)[0]
    return from_type in entity_types and to_type in entity_types


def _apply_focus_filter(
    nodes: Dict[str, Dict[str, Any]],
    edges: List[Dict[str, Any]],
    focus_entity: Optional[Dict[str, Any]],
    depth_value: Any,
) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
    """Limit nodes/edges to focus neighborhood when requested."""
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
    """Serialize entities and relationships for the network diagram.

    Args:
        user: Current user (permission checks)
        filters: Optional filters dict with keys:
            - entity_types: list[str]
            - relationship_types: list[str]
            - focus_entity: {"type": str, "id": int}
            - depth: int | "all"

    Returns:
        Dict[str, Any]: nodes, edges, stats payload
    """
    filters = filters or {}
    entity_types = tuple(filters.get("entity_types") or DEFAULT_ENTITY_TYPES)
    relationship_types = tuple(filters.get("relationship_types") or DEFAULT_RELATIONSHIP_TYPES)

    nodes = _fetch_nodes_by_type(entity_types)

    edges: List[Dict[str, Any]] = []
    confidential_hidden = 0
    relationship_configs = _relationship_configs()

    for rel_type in relationship_types:
        config = relationship_configs.get(rel_type)
        if not config:
            continue

        from_type, to_type = config["endpoints"]
        # Skip relationships if endpoints filtered out
        if from_type not in entity_types or to_type not in entity_types:
            continue

        query = db_session.query(config["model"])
        for rel in query.all():
            if not can_view_relationship(user, rel):
                confidential_hidden += 1
                continue

            edge = _build_edge(rel_type, rel)
            if not _filter_edges_for_entities(edge, entity_types):
                continue

            # Only include edge if both endpoints exist in node map
            if edge["from"] not in nodes or edge["to"] not in nodes:
                continue

            edges.append(edge)

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

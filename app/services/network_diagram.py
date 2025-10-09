"""Network diagram data serialization utilities."""
from collections import defaultdict, deque
from typing import Any, Dict, Iterable, List, Optional, Tuple

from flask import url_for
from sqlalchemy.orm import joinedload

from app import db_session
from app.models import (
    Company,
    CompanyRole,
    CompanyRoleAssignment,
    Project,
)
from app.utils.permissions import can_view_relationship

DEFAULT_ENTITY_TYPES: Tuple[str, ...] = ("company", "project")
DEFAULT_RELATIONSHIP_TYPES: Tuple[str, ...] = (
    "project_company",  # Unified project-company relationships
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


def _calculate_edge_roundness(role_index: int, total_roles: int) -> float:
    """Calculate roundness value for multiple edges between same nodes.
    
    Args:
        role_index: Index of current role (0-based)
        total_roles: Total number of roles between these nodes
    
    Returns:
        Roundness value for vis.js smooth curve
    """
    if total_roles == 1:
        return 0.2  # Default single edge
    
    # Base roundness
    base = 0.2
    
    # Spread factor - increases with more roles
    spread = 0.15
    
    # Center offset - distribute roles evenly around center
    center_offset = (role_index - (total_roles - 1) / 2.0) * spread
    
    return base + center_offset


def _get_role_color(role_label: str) -> str:
    """Get color for a specific role type.
    
    Args:
        role_label: Role label (e.g., 'Vendor', 'Owner', 'Operator')
    
    Returns:
        Hex color code
    """
    # Normalize the role label to check for keywords
    role_lower = role_label.lower()
    
    # Map role keywords to colors
    if 'vendor' in role_lower or 'technology' in role_lower:
        return '#e74c3c'  # Red
    elif 'owner' in role_lower or 'developer' in role_lower:
        return '#3498db'  # Blue
    elif 'operator' in role_lower or 'operate' in role_lower:
        return '#9b59b6'  # Purple
    elif 'constructor' in role_lower or 'construct' in role_lower:
        return '#f39c12'  # Orange
    elif 'offtaker' in role_lower or 'off-taker' in role_lower:
        return '#16a085'  # Teal
    elif 'investor' in role_lower or 'investment' in role_lower:
        return '#34495e'  # Dark gray
    elif 'regulator' in role_lower or 'regulatory' in role_lower:
        return '#e67e22'  # Dark orange
    elif 'supplier' in role_lower or 'supply' in role_lower:
        return '#c0392b'  # Dark red
    else:
        return '#7f8c8d'  # Default gray for unknown roles



def _project_company_edges(
    user,
    entity_types: Iterable[str],
    nodes: Dict[str, Dict[str, Any]],
    assignment_index: Dict[Tuple[str, int], CompanyRoleAssignment],
) -> Tuple[List[Dict[str, Any]], int]:
    """Generate edges for all project-company relationships using unified schema."""
    edges: List[Dict[str, Any]] = []
    hidden = 0
    
    if "company" not in entity_types or "project" not in entity_types:
        return edges, hidden
    
    # Query all CompanyRoleAssignments with context_type='Project'
    query = db_session.query(CompanyRoleAssignment).filter_by(
        context_type='Project'
    ).options(
        joinedload(CompanyRoleAssignment.company),
        joinedload(CompanyRoleAssignment.role),
    )
    
    # Group multiple roles between the same company and project into a single edge
    grouped: Dict[Tuple[int, int], Dict[str, Any]] = {}

    for assignment in query.all():
        if not can_view_relationship(user, assignment):
            hidden += 1
            continue

        project_id = assignment.context_id
        company_id = assignment.company_id
        if project_id is None:
            continue

        project_node = f"project_{project_id}"
        company_node = f"company_{company_id}"

        if project_node not in nodes or company_node not in nodes:
            continue

        role_label = assignment.role.role_label if assignment.role else "Company"
        key = (project_id, company_id)
        if key not in grouped:
            company_name = assignment.company.company_name if assignment.company else "Company"
            project = db_session.get(Project, project_id)
            project_name = project.project_name if project else f"Project {project_id}"
            grouped[key] = {
                "from": company_node,
                "to": project_node,
                "role_labels": [role_label],
                "company_name": company_name,
                "project_name": project_name,
            }
        else:
            if role_label not in grouped[key]["role_labels"]:
                grouped[key]["role_labels"].append(role_label)

    # Generate separate edges for each role (with color coding and smart spacing)
    for (project_id, company_id), data in grouped.items():
        roles = data["role_labels"]
        
        # Create separate edge for each role
        for idx, role_label in enumerate(roles):
            roundness = _calculate_edge_roundness(idx, len(roles))
            
            # Determine curve direction (alternate for better spacing)
            curve_type = "curvedCW" if idx % 2 == 0 else "curvedCCW"
            
            title = f"{data['company_name']} ({role_label}) ↔ {data['project_name']}"
            
            edges.append({
                "id": f"project_company_{project_id}_{company_id}_{role_label}",
                "from": data["from"],
                "to": data["to"],
                "label": role_label,
                "title": title,
                "color": {
                    "color": _get_role_color(role_label),
                    "highlight": _get_role_color(role_label),
                    "hover": _get_role_color(role_label),
                    "inherit": False,
                },
                "smooth": {
                    "enabled": True,
                    "type": curve_type,
                    "roundness": roundness,
                },
                "width": 2,
            })
    
    return edges, hidden


EDGE_BUILDERS = {
    "project_company": _project_company_edges,
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

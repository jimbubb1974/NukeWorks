# 11_NETWORK_DIAGRAM.md

**Document:** Network Diagram Visualization  
**Version:** 1.1  
**Last Updated:** January 9, 2026  
**Related Documents:** `02_DATABASE_SCHEMA.md`, `03_DATABASE_RELATIONSHIPS.md`, `05_PERMISSION_SYSTEM.md`

---

## Table of Contents

1. [Overview](#overview)
2. [Technology Choice](#technology-choice)
3. [Data Serialization](#data-serialization)
4. [Visual Design](#visual-design)
5. [Interactivity](#interactivity)
6. [Filtering & Controls](#filtering--controls)
7. [Performance Optimization](#performance-optimization)
8. [Export Functionality](#export-functionality)

---

## 1. Overview

The Network Diagram provides an interactive visualization of relationships between entities (vendors, projects, owners, constructors, operators, off-takers). It helps users understand the ecosystem at a glance and explore connections.

### Key Features

- **Interactive nodes** - Click to view details, drag to reposition
- **Relationship visualization** - Lines connecting related entities
- **Filtering** - Show/hide entity types and relationship types
- **Focus mode** - Center on specific entity and show connections
- **Zoom & pan** - Navigate large networks
- **Confidentiality-aware** - Respects user permissions
- **Export** - Save as image or generate report

### Use Cases

- Understand vendor-owner relationships
- Identify project stakeholders
- Explore supply chain connections
- Generate relationship reports
- Present ecosystem overview to stakeholders

---

## 2. Technology Choice

### Recommended: Vis.js

**Pros:**
- Excellent performance with large datasets
- Good documentation and examples
- Active community
- Built-in physics engine for auto-layout
- Extensive customization options

**Installation:**
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
<link href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css" rel="stylesheet" />
```

### Alternative: Cytoscape.js

**Pros:**
- More advanced layout algorithms
- Better for complex networks
- Extensive plugin ecosystem

**Use if:**
- Network has >500 nodes
- Need specific layout algorithms (hierarchical, circular)
- Need advanced graph analysis features

---

## 3. Data Serialization

### 3.1 Backend Serialization

```python
def get_network_data(user, filters=None):
    """
    Serialize database entities and relationships for network diagram
    
    Args:
        user: Current user (for permission checking)
        filters: Dict with entity_types, relationship_types, focus_entity, depth
    
    Returns:
        {
            'nodes': [...],
            'edges': [...],
            'stats': {...}
        }
    """
    nodes = []
    edges = []
    
    # Apply filters
    entity_types = filters.get('entity_types', ['vendor', 'owner', 'project', 'constructor', 'operator', 'offtaker'])
    relationship_types = filters.get('relationship_types', [])
    focus_entity = filters.get('focus_entity')  # {type: 'vendor', id: 5}
    depth = filters.get('depth', 'all')  # 'all', 1, 2
    
    # Get entities (nodes)
    if 'vendor' in entity_types:
        vendors = get_vendors_for_user(user)
        for vendor in vendors:
            nodes.append({
                'id': f'vendor_{vendor.vendor_id}',
                'label': vendor.vendor_name,
                'group': 'vendor',
                'title': f'Vendor: {vendor.vendor_name}',  # Tooltip
                'url': f'/vendors/{vendor.vendor_id}'  # For click navigation
            })
    
    if 'owner' in entity_types:
        owners = get_owners_for_user(user)
        for owner in owners:
            nodes.append({
                'id': f'owner_{owner.owner_id}',
                'label': owner.company_name,
                'group': 'owner',
                'title': f'Owner: {owner.company_name}\nType: {owner.company_type}',
                'url': f'/owners/{owner.owner_id}'
            })
    
    if 'project' in entity_types:
        projects = get_projects_for_user(user)
        for project in projects:
            nodes.append({
                'id': f'project_{project.project_id}',
                'label': project.project_name,
                'group': 'project',
                'title': f'Project: {project.project_name}\nStatus: {project.project_status}',
                'url': f'/projects/{project.project_id}'
            })
    
    # Add constructors and operators similarly...
    
    # Get relationships (edges)
    relationships = get_relationships_for_user(user, relationship_types)
    
    for rel in relationships:
        # Skip confidential relationships if user lacks access
        if rel.is_confidential and not user.has_confidential_access:
            continue
        
        # Create edge
        edge = {
            'from': f'{rel.entity1_type}_{rel.entity1_id}',
            'to': f'{rel.entity2_type}_{rel.entity2_id}',
            'title': rel.relationship_type or 'Related',
            'label': rel.relationship_type if len(rel.relationship_type) < 20 else '',
        }
        
        # Add relationship-specific styling
        if rel.relationship_type == 'Delivery_Contract':
            edge['color'] = {'color': '#2ecc71', 'highlight': '#27ae60'}
            edge['width'] = 3
        elif rel.relationship_type == 'MOU':
            edge['dashes'] = True
        
        edges.append(edge)
    
    # Apply focus filter if specified
    if focus_entity:
        nodes, edges = filter_by_focus(nodes, edges, focus_entity, depth)
    
    # Calculate statistics
    stats = {
        'total_nodes': len(nodes),
        'total_edges': len(edges),
        'by_type': count_by_type(nodes),
        'confidential_hidden': count_confidential_hidden(user, relationships)
    }
    
    return {
        'nodes': nodes,
        'edges': edges,
        'stats': stats
    }
```

### 3.2 Focus Filtering

```python
def filter_by_focus(nodes, edges, focus_entity, depth):
    """
    Filter network to show only entities within N hops of focus entity
    
    Args:
        focus_entity: {'type': 'vendor', 'id': 5}
        depth: 1, 2, or 'all'
    """
    if depth == 'all':
        return nodes, edges
    
    focus_id = f"{focus_entity['type']}_{focus_entity['id']}"
    
    # Build adjacency list
    adjacency = build_adjacency_list(edges)
    
    # BFS to find nodes within depth
    visible_nodes = set([focus_id])
    queue = [(focus_id, 0)]
    visited = set()
    
    while queue:
        node_id, current_depth = queue.pop(0)
        
        if node_id in visited:
            continue
        
        visited.add(node_id)
        
        if current_depth < depth:
            # Add neighbors
            for neighbor in adjacency.get(node_id, []):
                visible_nodes.add(neighbor)
                queue.append((neighbor, current_depth + 1))
    
    # Filter nodes and edges
    filtered_nodes = [n for n in nodes if n['id'] in visible_nodes]
    filtered_edges = [e for e in edges if e['from'] in visible_nodes and e['to'] in visible_nodes]
    
    return filtered_nodes, filtered_edges
```

### 3.3 JSON Response Format

```json
{
  "nodes": [
    {
      "id": "vendor_5",
      "label": "TechCorp A",
      "group": "vendor",
      "title": "Vendor: TechCorp A",
      "url": "/vendors/5"
    },
    {
      "id": "owner_12",
      "label": "Utility Company X",
      "group": "owner",
      "title": "Owner: Utility Company X\nType: IOU",
      "url": "/owners/12"
    },
    {
      "id": "project_45",
      "label": "Project Alpha",
      "group": "project",
      "title": "Project: Project Alpha\nStatus: Active",
      "url": "/projects/45"
    }
  ],
  "edges": [
    {
      "from": "owner_12",
      "to": "vendor_5",
      "title": "MOU",
      "label": "MOU",
      "dashes": true
    },
    {
      "from": "project_45",
      "to": "vendor_5",
      "title": "Technology",
      "label": "",
      "color": {"color": "#3498db"}
    }
  ],
  "stats": {
    "total_nodes": 3,
    "total_edges": 2,
    "by_type": {
      "vendor": 1,
      "owner": 1,
      "project": 1
    },
    "confidential_hidden": 2
  }
}
```

---

## 4. Visual Design

### 4.1 Node Styling

```javascript
const nodeStyles = {
    vendor: {
        shape: 'dot',
        color: {
            background: '#e74c3c',
            border: '#c0392b',
            highlight: {
                background: '#c0392b',
                border: '#a93226'
            }
        },
        size: 25,
        font: {
            color: '#2c3e50',
            size: 14,
            face: 'Arial'
        }
    },
    owner: {
        shape: 'box',
        color: {
            background: '#3498db',
            border: '#2980b9',
            highlight: {
                background: '#2980b9',
                border: '#21618c'
            }
        },
        font: {
            color: '#2c3e50',
            size: 14
        }
    },
    project: {
        shape: 'diamond',
        color: {
            background: '#2ecc71',
            border: '#27ae60',
            highlight: {
                background: '#27ae60',
                border: '#1e8449'
            }
        },
        size: 30,
        font: {
            color: '#2c3e50',
            size: 14
        }
    },
    constructor: {
        shape: 'triangle',
        color: {
            background: '#f39c12',
            border: '#d68910',
            highlight: {
                background: '#d68910',
                border: '#b9770e'
            }
        },
        size: 25,
        font: {
            color: '#2c3e50',
            size: 14
        }
    },
    operator: {
        shape: 'triangleDown',
        color: {
            background: '#9b59b6',
            border: '#8e44ad',
            highlight: {
                background: '#8e44ad',
                border: '#76448a'
            }
        },
        size: 25,
        font: {
            color: '#2c3e50',
            size: 14
        }
    },
    offtaker: {
        shape: 'hexagon',
        color: {
            background: '#16a085',
            border: '#13856d',
            highlight: {
                background: '#13856d',
                border: '#0e5f4a'
            }
        },
        size: 26,
        font: {
            color: '#2c3e50',
            size: 14
        }
    }
};
```

### 4.2 Edge Styling

```javascript
const edgeStyles = {
    default: {
        color: {
            color: '#95a5a6',
            highlight: '#7f8c8d'
        },
        width: 2,
        smooth: {
            type: 'continuous'
        }
    },
    mou: {
        dashes: true,
        color: {
            color: '#3498db'
        },
        width: 2
    },
    contract: {
        color: {
            color: '#2ecc71'
        },
        width: 3
    },
    supplier: {
        arrows: 'to',
        color: {
            color: '#e74c3c'
        },
        width: 2
    }
};
```

### 4.3 Legend

```html
<div class="network-legend">
    <h4>Legend</h4>
    <div class="legend-item">
        <span class="legend-node vendor-node"></span>
        <span>Technology Vendor</span>
    </div>
    <div class="legend-item">
        <span class="legend-node owner-node"></span>
        <span>Owner/Developer</span>
    </div>
    <div class="legend-item">
        <span class="legend-node project-node"></span>
        <span>Project</span>
    </div>
    <div class="legend-item">
        <span class="legend-node constructor-node"></span>
        <span>Constructor</span>
    </div>
    <div class="legend-item">
        <span class="legend-node operator-node"></span>
        <span>Operator</span>
    </div>
    <div class="legend-item">
        <span class="legend-node offtaker-node"></span>
        <span>Off-taker</span>
    </div>
    <hr>
    <div class="legend-item">
        <span class="legend-edge solid-edge"></span>
        <span>Relationship</span>
    </div>
    <div class="legend-item">
        <span class="legend-edge dashed-edge"></span>
        <span>MOU</span>
    </div>
    <div class="legend-item">
        <span class="legend-edge thick-edge"></span>
        <span>Contract</span>
    </div>
</div>
```

---

## 5. Interactivity

### 5.1 Network Initialization

```javascript
// Initialize network
function initializeNetwork(container, data) {
    const options = {
        nodes: {
            borderWidth: 2,
            borderWidthSelected: 3,
            font: {
                size: 14,
                face: 'Arial'
            }
        },
        edges: {
            smooth: {
                type: 'continuous'
            },
            font: {
                size: 12,
                align: 'middle'
            }
        },
        physics: {
            enabled: true,
            barnesHut: {
                gravitationalConstant: -2000,
                centralGravity: 0.3,
                springLength: 95,
                springConstant: 0.04,
                damping: 0.09
            },
            stabilization: {
                iterations: 200
            }
        },
        interaction: {
            hover: true,
            tooltipDelay: 200,
            navigationButtons: true,
            keyboard: true
        }
    };
    
    // Apply group-specific styling
    data.nodes.forEach(node => {
        Object.assign(node, nodeStyles[node.group]);
    });
    
    const network = new vis.Network(container, data, options);
    
    // Setup event handlers
    setupEventHandlers(network);
    
    return network;
}
```

### 5.2 Event Handlers

```javascript
function setupEventHandlers(network) {
    // Click on node - navigate to entity
    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const node = network.body.data.nodes.get(nodeId);
            
            if (node.url) {
                window.location.href = node.url;
            }
        }
    });
    
    // Right-click on node - show context menu
    network.on('oncontext', function(params) {
        params.event.preventDefault();
        
        if (params.nodes.length > 0) {
            showContextMenu(params.nodes[0], params.pointer.DOM);
        }
    });
    
    // Hover - show tooltip
    network.on('hoverNode', function(params) {
        const node = network.body.data.nodes.get(params.node);
        showTooltip(node, params.pointer.DOM);
    });
    
    network.on('blurNode', function() {
        hideTooltip();
    });
    
    // Double-click - focus on node
    network.on('doubleClick', function(params) {
        if (params.nodes.length > 0) {
            focusOnNode(network, params.nodes[0]);
        }
    });
    
    // Stabilization complete
    network.on('stabilizationIterationsDone', function() {
        network.setOptions({physics: false});
        console.log('Network layout stabilized');
    });
}
```

### 5.3 Context Menu

```javascript
function showContextMenu(nodeId, position) {
    const node = network.body.data.nodes.get(nodeId);
    
    const menu = document.createElement('div');
    menu.className = 'context-menu';
    menu.style.left = position.x + 'px';
    menu.style.top = position.y + 'px';
    
    menu.innerHTML = `
        <div class="context-menu-item" onclick="viewNodeDetails('${nodeId}')">
            View Details
        </div>
        <div class="context-menu-item" onclick="focusOnNode(network, '${nodeId}')">
            Focus on This Entity
        </div>
        <div class="context-menu-item" onclick="showConnections('${nodeId}')">
            Show Connections
        </div>
        <div class="context-menu-item" onclick="hideNode('${nodeId}')">
            Hide from Diagram
        </div>
    `;
    
    document.body.appendChild(menu);
    
    // Remove on click outside
    setTimeout(() => {
        document.addEventListener('click', () => menu.remove(), {once: true});
    }, 100);
}
```

### 5.4 Focus Mode

```javascript
function focusOnNode(network, nodeId) {
    // Get connected nodes
    const connectedNodes = network.getConnectedNodes(nodeId);
    
    // Highlight focus node and connections
    const nodesToHighlight = [nodeId, ...connectedNodes];
    
    // Get all nodes
    const allNodes = network.body.data.nodes.get();
    
    // Update node opacity
    allNodes.forEach(node => {
        if (nodesToHighlight.includes(node.id)) {
            node.opacity = 1.0;
            node.size = node.size * 1.2;  // Enlarge
        } else {
            node.opacity = 0.2;  // Fade
        }
    });
    
    network.body.data.nodes.update(allNodes);
    
    // Fit to focused nodes
    network.fit({
        nodes: nodesToHighlight,
        animation: {
            duration: 1000,
            easingFunction: 'easeInOutQuad'
        }
    });
}
```

---

## 6. Filtering & Controls

### 6.1 Filter Panel UI

```html
<div class="network-controls">
    <div class="control-section">
        <h4>Entity Types</h4>
        <label><input type="checkbox" value="vendor" checked> Vendors</label>
        <label><input type="checkbox" value="owner" checked> Owners</label>
        <label><input type="checkbox" value="project" checked> Projects</label>
        <label><input type="checkbox" value="constructor" checked> Constructors</label>
        <label><input type="checkbox" value="operator" checked> Operators</label>
        <label><input type="checkbox" value="offtaker" checked> Off-takers</label>
    </div>
    
    <div class="control-section">
        <h4>Relationship Types</h4>
        <label><input type="checkbox" value="all" checked> All</label>
        <label><input type="checkbox" value="mou"> MOUs</label>
        <label><input type="checkbox" value="contract"> Contracts</label>
        <label><input type="checkbox" value="technology"> Technology</label>
        <label><input type="checkbox" value="supplier"> Supplier</label>
        <label><input type="checkbox" value="offtake"> Off-take Agreements</label>
    </div>
    
    <div class="control-section">
        <h4>Focus</h4>
        <select id="focus-entity">
            <option value="">All Entities</option>
            <option value="vendor_5">TechCorp A</option>
            <option value="owner_12">Utility X</option>
            <!-- Populated dynamically -->
        </select>
        
        <label>Depth:</label>
        <select id="focus-depth">
            <option value="all">All</option>
            <option value="1">1 hop</option>
            <option value="2">2 hops</option>
        </select>
    </div>
    
    <div class="control-section">
        <h4>Layout</h4>
        <select id="layout-type">
            <option value="physics">Force-Directed</option>
            <option value="hierarchical">Hierarchical</option>
            <option value="circular">Circular</option>
        </select>
    </div>
    
    <div class="control-section">
        <button onclick="applyFilters()">Apply Filters</button>
        <button onclick="resetView()">Reset View</button>
        <button onclick="exportDiagram()">Export as Image</button>
    </div>
</div>
```

### 6.2 Apply Filters

```javascript
function applyFilters() {
    // Collect filter values
    const filters = {
        entity_types: getCheckedValues('.control-section input[type="checkbox"]:checked'),
        relationship_types: [], // Collected similarly
        focus_entity: document.getElementById('focus-entity').value,
        depth: document.getElementById('focus-depth').value
    };
    
    // Show loading indicator
    showLoading();
    
    // Fetch filtered data
    fetch('/api/network-diagram', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(filters)
    })
    .then(response => response.json())
    .then(data => {
        // Update network
        network.setData(data);
        
        // Update statistics
        updateStats(data.stats);
        
        hideLoading();
    })
    .catch(error => {
        console.error('Error applying filters:', error);
        showError('Failed to apply filters');
        hideLoading();
    });
}
```

---

## 7. Performance Optimization

### 7.1 Large Network Handling

```javascript
function optimizeForLargeNetwork(nodeCount) {
    if (nodeCount > 200) {
        // Disable physics after initial layout
        network.setOptions({
            physics: {
                stabilization: {
                    iterations: 100  // Reduce iterations
                }
            }
        });
        
        // Simplify rendering
        network.setOptions({
            nodes: {
                shapeProperties: {
                    interpolation: false  // Faster rendering
                }
            },
            edges: {
                smooth: false  // Straight edges
            }
        });
        
        // Warn user
        showWarning('Large network detected. Some features disabled for performance.');
    }
    
    if (nodeCount > 500) {
        // Suggest filtering
        showWarning('Network has ' + nodeCount + ' nodes. Consider applying filters for better performance.');
    }
}
```

### 7.2 Lazy Loading

```javascript
// Load network data in chunks for very large datasets
function loadNetworkInChunks(filters) {
    let offset = 0;
    const chunkSize = 100;
    
    function loadChunk() {
        fetch(`/api/network-diagram?offset=${offset}&limit=${chunkSize}`, {
            method: 'POST',
            body: JSON.stringify(filters)
        })
        .then(response => response.json())
        .then(data => {
            // Add nodes and edges to existing network
            network.body.data.nodes.add(data.nodes);
            network.body.data.edges.add(data.edges);
            
            offset += chunkSize;
            
            if (data.has_more) {
                // Load next chunk
                setTimeout(loadChunk, 100);
            } else {
                // All data loaded
                network.fit();
            }
        });
    }
    
    loadChunk();
}
```

---

## 8. Export Functionality

### 8.1 Export as Image

```javascript
function exportDiagram() {
    // Get canvas element
    const canvas = document.querySelector('.vis-network canvas');
    
    // Convert to data URL
    const dataURL = canvas.toDataURL('image/png');
    
    // Create download link
    const link = document.createElement('a');
    link.download = `network-diagram-${new Date().toISOString().split('T')[0]}.png`;
    link.href = dataURL;
    link.click();
}
```

### 8.2 Generate Report

```javascript
function generateNetworkReport() {
    // Show report options modal
    const modal = showModal('Generate Network Report');
    
    modal.innerHTML = `
        <form id="report-form">
            <label>
                <input type="checkbox" name="include_image" checked>
                Include network diagram image
            </label>
            
            <label>
                <input type="checkbox" name="include_statistics" checked>
                Include statistics
            </label>
            
            <label>
                <input type="checkbox" name="include_entity_list" checked>
                Include entity list
            </label>
            
            <label>
                <input type="checkbox" name="include_relationship_list" checked>
                Include relationship list
            </label>
            
            <button type="submit">Generate PDF</button>
        </form>
    `;
    
    document.getElementById('report-form').onsubmit = function(e) {
        e.preventDefault();
        
        // Get form data
        const formData = new FormData(e.target);
        
        // Get current filters
        const filters = getCurrentFilters();
        
        // Request report generation
        fetch('/api/reports/network-map', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                filters: filters,
                options: Object.fromEntries(formData)
            })
        })
        .then(response => response.blob())
        .then(blob => {
            // Download PDF
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'network-relationship-map.pdf';
            a.click();
        });
    };
}
```

---

## Document History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.1 | Jan 9, 2026 | Added energy off-taker nodes and project links | [Author] |
| 1.0 | Dec 4, 2025 | Initial network diagram specification | [Author] |

---

**END OF DOCUMENT**

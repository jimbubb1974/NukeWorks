(function (global) {
  const GROUP_LABELS = Object.assign(Object.create(null), {
    company: "Company",
    project: "Project",
  });

  const CONFIDENTIAL_EDGE_COLOR = "#f39c12";
  const CONFIDENTIAL_EDGE_HIGHLIGHT = "#d68910";
  const NODE_LABEL_FONT = { color: "#1f5f99", size: 14, face: "Arial", weight: "700" };
  const INTERACTION_OPTIONS = {
    hover: true,
    tooltipDelay: 200,
    navigationButtons: true,
    keyboard: true,
    dragView: true,
    zoomView: true,
    dragNodes: true,
  };
  const ROLE_GROUP_ALIASES = Object.assign(Object.create(null), {
    developer: "owner",
    owner_developer: "owner",
    "owner-developer": "owner",
    technology_vendor: "vendor",
    "technology-vendor": "vendor",
    architect_engineer: "engineer",
    "architect-engineer": "engineer",
    owners_engineer: "engineer",
    owner_engineer: "engineer",
    "owner's_engineer": "engineer",
  });
  const HIERARCHICAL_GROUP_ORDER = [
    "offtaker",
    "owner",
    "project",
    "vendor",
    "engineer",
    "constructor",
    "operator",
    "company",
  ];
  const HIERARCHICAL_GROUP_RANK = HIERARCHICAL_GROUP_ORDER.reduce(
    (rank, group, index) => {
      rank[group] = index;
      return rank;
    },
    Object.create(null)
  );

  const GROUP_STYLES = {
    company: {
      shape: "dot",
      size: 25,
      color: {
        background: "#3498db",
        border: "#2980b9",
        highlight: { background: "#2980b9", border: "#21618c" },
      },
      font: NODE_LABEL_FONT,
    },
    project: {
      shape: "diamond",
      size: 30,
      color: {
        background: "#2ecc71",
        border: "#27ae60",
        highlight: { background: "#27ae60", border: "#1e8449" },
      },
      font: NODE_LABEL_FONT,
    },
  };

  function withCanvasLabelOffset(node) {
    return Object.assign({}, node, {
      raw_label: node.raw_label || node.label,
      label: "",
    });
  }

  function formatNodeLabel(node) {
    const groupLabel = GROUP_LABELS[node.group] || node.group;
    return groupLabel + " • " + node.label;
  }

  function normalizeRoleGroup(value) {
    if (!value) return null;
    const normalized = String(value).trim().toLowerCase().replace(/\s+/g, "_");
    return ROLE_GROUP_ALIASES[normalized] || normalized;
  }

  function chooseRoleGroup(candidates) {
    let selected = null;
    let selectedCount = -1;
    candidates.forEach((count, group) => {
      const rank = HIERARCHICAL_GROUP_RANK[group] ?? HIERARCHICAL_GROUP_ORDER.length;
      const selectedRank =
        selected == null
          ? HIERARCHICAL_GROUP_ORDER.length + 1
          : HIERARCHICAL_GROUP_RANK[selected] ?? HIERARCHICAL_GROUP_ORDER.length;
      if (count > selectedCount || (count === selectedCount && rank < selectedRank)) {
        selected = group;
        selectedCount = count;
      }
    });
    return selected;
  }

  function normalizeEdge(edge) {
    if (!edge || !edge.is_confidential) {
      return edge;
    }

    return Object.assign({}, edge, {
      color: Object.assign({}, edge.color || {}, {
        color: CONFIDENTIAL_EDGE_COLOR,
        highlight: CONFIDENTIAL_EDGE_HIGHLIGHT,
        hover: CONFIDENTIAL_EDGE_HIGHLIGHT,
      }),
      font: Object.assign({}, edge.font || {}, {
        color: CONFIDENTIAL_EDGE_COLOR,
        strokeWidth: 0,
      }),
    });
  }

  // Fan out parallel edges (same from/to pair) with alternating CW/CCW curves.
  // Single edges between a pair remain straight (smooth: { enabled: false }).
  function assignParallelEdgeCurves(edges) {
    const pairGroups = new Map();
    edges.forEach((edge) => {
      const key = [String(edge.from), String(edge.to)].sort().join("\x00");
      if (!pairGroups.has(key)) pairGroups.set(key, []);
      pairGroups.get(key).push(edge.id);
    });

    const edgeInfo = new Map();
    pairGroups.forEach((ids) => {
      ids.forEach((id, i) => edgeInfo.set(id, { idx: i, total: ids.length }));
    });

    return edges.map((edge) => {
      const info = edgeInfo.get(edge.id);
      if (!info || info.total <= 1) return edge;

      const { idx, total } = info;
      const spread = idx - (total - 1) / 2;
      const roundness = Math.abs(spread) * 0.28;

      const smooth =
        roundness < 0.01
          ? { enabled: false }
          : {
              enabled: true,
              type: spread > 0 ? "curvedCW" : "curvedCCW",
              roundness,
            };

      return Object.assign({}, edge, { smooth });
    });
  }

  // X-axis position bands for columns layout (arbitrary units; physics settles y)
  const COLUMN_X = {
    offtaker:    -900,
    owner:       -450,
    project:        0,
    vendor:       450,
    engineer:     900,
    constructor:  900,
    operator:     900,
    company:      450,
  };

  const NetworkDiagram = {
    config: {},
    network: null,
    nodesDataSet: null,
    edgesDataSet: null,
    nodeIndex: new Map(),
    currentFilters: {
      entity_types: ["company", "project"],
      relationship_types: ["project_company"],
      show_orphan_nodes: false,
      focus_entity: null,
      depth: "all",
    },
    physicsDisabled: false,
    currentLayout: "project-spine",
    projectSpineSpacingScale: 1,
    projectSpineCompactRows: false,

    init(config) {
      this.config = config;
      this.container = document.getElementById(config.containerId);
      this.loadingIndicator = document.getElementById(
        config.loadingIndicatorId
      );
      this.filterForm = document.getElementById(config.filterFormId);
      this.focusForm = document.getElementById(config.focusFormId);
      this.focusSelect = document.getElementById(config.focusSelectId);
      this.focusDepth = document.getElementById(config.focusDepthId);
      this.clearFocusBtn = document.getElementById(config.clearFocusButtonId);
      this.resetViewBtn = document.getElementById(config.resetViewButtonId);
      this.resetPhysicsBtn = document.getElementById(
        config.resetPhysicsButtonId
      );
      this.projectSpineSpacingControl = config.projectSpineSpacingControlId
        ? document.getElementById(config.projectSpineSpacingControlId)
        : null;
      this.projectSpineSpacingInput = config.projectSpineSpacingInputId
        ? document.getElementById(config.projectSpineSpacingInputId)
        : null;
      this.projectSpineSpacingValue = config.projectSpineSpacingValueId
        ? document.getElementById(config.projectSpineSpacingValueId)
        : null;
      this.projectSpineCompactInput = config.projectSpineCompactInputId
        ? document.getElementById(config.projectSpineCompactInputId)
        : null;
      this.statsDom = config.statsSelectors;
      this.detailPanel = config.detailPanel;

      if (!this.container) {
        console.error("Network container not found");
        return;
      }

      this.ensureVisAvailable(() => {
        this.attachEventListeners();
        this.readFiltersFromForm();
        this.fetchAndRender();
      });
    },

    ensureVisAvailable(onReady) {
      if (
        global.vis &&
        typeof global.vis.Network === "function" &&
        typeof global.vis.DataSet === "function"
      ) {
        this._visWaitAttempts = 0;
        onReady();
        return;
      }

      if (global.__visLibraryLoading) {
        const attempts = this._visWaitAttempts || 0;
        if (attempts < 40) {
          this._visWaitAttempts = attempts + 1;
          setTimeout(() => this.ensureVisAvailable(onReady), 150);
          return;
        }
      }

      this.hideLoading();
      this.showError(
        "Visualization library failed to load. Please ensure Vis.js is available (the CDN may be blocked)."
      );
      console.error("Vis.js not available.");
    },

    attachEventListeners() {
      if (this.filterForm) {
        this.filterForm.addEventListener("submit", (event) => {
          event.preventDefault();
          if (this.updateFiltersFromForm()) {
            this.fetchAndRender();
          }
        });
      }

      if (this.focusForm) {
        this.focusForm.addEventListener("submit", (event) => {
          event.preventDefault();
          const selected = this.focusSelect ? this.focusSelect.value : "";
          const depth = this.focusDepth ? this.focusDepth.value : "all";
          this.applyFocus(selected, depth);
        });
      }

      if (this.clearFocusBtn) {
        this.clearFocusBtn.addEventListener("click", () => {
          this.clearFocus();
        });
      }

      if (this.resetViewBtn) {
        this.resetViewBtn.addEventListener("click", () => {
          if (this.network) {
            this.network.fit({
              animation: { duration: 600, easingFunction: "easeInOutQuad" },
            });
          }
        });
      }

      if (this.resetPhysicsBtn) {
        this.resetPhysicsBtn.addEventListener("click", () => {
          if (this.network) {
            this.physicsDisabled = false;
            this.network.setOptions({ physics: { enabled: true } });
            this.network.stabilize();
          }
        });
      }

      if (this.projectSpineSpacingInput) {
        this.updateProjectSpineSpacing();
        this.updateProjectSpineControlsVisibility();
        this.projectSpineSpacingInput.addEventListener("input", () => {
          this.updateProjectSpineSpacing();
          if (this.currentLayout === "project-spine") {
            this.setLayout("project-spine");
          }
        });
      }
      if (this.projectSpineCompactInput) {
        this.updateProjectSpineCompactRows();
        this.projectSpineCompactInput.addEventListener("change", () => {
          this.updateProjectSpineCompactRows();
          if (this.currentLayout === "project-spine") {
            this.setLayout("project-spine");
          }
        });
      }

      // Layout button group
      const layoutGroup = this.config.layoutButtonGroupId
        ? document.getElementById(this.config.layoutButtonGroupId)
        : null;
      if (layoutGroup) {
        layoutGroup.querySelectorAll("button[data-layout]").forEach((btn) => {
          btn.addEventListener("click", () => {
            this.setLayout(btn.dataset.layout);
          });
        });
      }
      this.updateProjectSpineControlsVisibility();
    },

    updateProjectSpineControlsVisibility() {
      if (!this.projectSpineSpacingControl) {
        return;
      }
      this.projectSpineSpacingControl.classList.toggle(
        "d-none",
        this.currentLayout !== "project-spine"
      );
    },

    readFiltersFromForm() {
      if (!this.filterForm) {
        return;
      }
      const entityInputs = this.filterForm.querySelectorAll(
        'input[name="entity_types"]'
      );
      const relationshipInputs = this.filterForm.querySelectorAll(
        'input[name="relationship_types"]'
      );
      const showOrphanInput = this.filterForm.querySelector(
        'input[name="show_orphan_nodes"]'
      );

      const selectedEntities = Array.from(entityInputs)
        .filter((input) => input.checked)
        .map((input) => input.value);
      const selectedRelationships = Array.from(relationshipInputs)
        .filter((input) => input.checked)
        .map((input) => input.value);

      if (selectedEntities.length > 0) {
        this.currentFilters.entity_types = selectedEntities;
      }
      if (selectedRelationships.length > 0) {
        this.currentFilters.relationship_types = selectedRelationships;
      }
      if (showOrphanInput) {
        this.currentFilters.show_orphan_nodes = showOrphanInput.checked;
      }
    },

    updateFiltersFromForm() {
      if (!this.filterForm) {
        return false;
      }
      const entityInputs = this.filterForm.querySelectorAll(
        'input[name="entity_types"]'
      );
      const relationshipInputs = this.filterForm.querySelectorAll(
        'input[name="relationship_types"]'
      );
      const showOrphanInput = this.filterForm.querySelector(
        'input[name="show_orphan_nodes"]'
      );

      const selectedEntities = Array.from(entityInputs)
        .filter((input) => input.checked)
        .map((input) => input.value);
      const selectedRelationships = Array.from(relationshipInputs)
        .filter((input) => input.checked)
        .map((input) => input.value);

      if (selectedEntities.length === 0) {
        alert("Select at least one entity type.");
        return false;
      }
      if (selectedRelationships.length === 0) {
        alert("Select at least one relationship type.");
        return false;
      }

      this.currentFilters.entity_types = selectedEntities;
      this.currentFilters.relationship_types = selectedRelationships;
      if (showOrphanInput) {
        this.currentFilters.show_orphan_nodes = showOrphanInput.checked;
      }

      // Clear focus if it conflicts with new filters
      if (
        this.currentFilters.focus_entity &&
        !this.currentFilters.entity_types.includes(
          this.currentFilters.focus_entity.type
        )
      ) {
        this.clearFocus(false);
      }
      return true;
    },

    showLoading() {
      if (this.loadingIndicator) {
        this.loadingIndicator.classList.remove("d-none");
      }
    },

    hideLoading() {
      if (this.loadingIndicator) {
        this.loadingIndicator.classList.add("d-none");
      }
    },

    async fetchAndRender() {
      if (!this.config.dataUrl) {
        console.error("Data URL is not configured");
        return;
      }
      this.showLoading();

      const payload = Object.assign({}, this.currentFilters);
      if (!payload.focus_entity) {
        delete payload.focus_entity;
        payload.depth = "all";
      }

      try {
        const response = await fetch(this.config.dataUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          throw new Error("Failed to load network data");
        }

        let data;
        try {
          data = await response.json();
        } catch (jsonError) {
          throw new Error("Unable to parse network data response.");
        }
        this.updateData(data);
      } catch (error) {
        console.error(error);
        this.showError(
          "Unable to load network diagram data. Check your session or reload the page."
        );
      } finally {
        this.hideLoading();
      }
    },

    updateData(data) {
      this.nodeIndex.clear();

      // Filter out orphaned nodes if the option is enabled
      let filteredNodes = data.nodes.map((node) =>
        Object.assign({}, node, {
          group: node.group === "project" ? "project" : "company",
        })
      );
      let filteredEdges = assignParallelEdgeCurves(
        (data.edges || []).map((edge) => normalizeEdge(edge))
      );

      if (!this.currentFilters.show_orphan_nodes) {
        const connectedNodeIds = new Set();
        filteredEdges.forEach((edge) => {
          if (edge.from) {
            connectedNodeIds.add(edge.from);
          }
          if (edge.to) {
            connectedNodeIds.add(edge.to);
          }
        });

        filteredNodes = filteredNodes.filter((node) => {
          return connectedNodeIds.has(node.id);
        });
        filteredEdges = filteredEdges.filter(
          (edge) =>
            connectedNodeIds.has(edge.from) && connectedNodeIds.has(edge.to)
        );
      }

      filteredNodes.forEach((node) => {
        this.nodeIndex.set(node.id, node);
      });

      if (!this.nodesDataSet || !this.edgesDataSet) {
        this.nodesDataSet = new vis.DataSet(
          filteredNodes.map((node) => withCanvasLabelOffset(node))
        );
        this.edgesDataSet = new vis.DataSet(filteredEdges);
        this.createNetwork();
      } else {
        this.nodesDataSet.clear();
        this.edgesDataSet.clear();
        if (filteredNodes.length > 0) {
          this.nodesDataSet.add(
            filteredNodes.map((node) => withCanvasLabelOffset(node))
          );
        }
        if (filteredEdges.length > 0) {
          this.edgesDataSet.add(filteredEdges);
        }
      }

      if (this.network) {
        // Re-apply the current layout mode after data changes
        this.setLayout(this.currentLayout, {
          fit: !this.currentFilters.focus_entity,
        });
      }

      this.populateFocusOptions();
      this.updateStats(data.stats);

      if (this.network) {
        if (this.currentFilters.focus_entity) {
          const focusNodeId =
            this.currentFilters.focus_entity.type +
            "_" +
            this.currentFilters.focus_entity.id;
          if (this.nodeIndex.has(focusNodeId)) {
            this.network.focus(focusNodeId, {
              scale: 1.2,
              animation: { duration: 600, easingFunction: "easeInOutQuad" },
            });
          }
        }
      }
    },

    showError(message) {
      if (!this.container) {
        return;
      }

      const alertId = this.config.errorBannerId;
      let alertEl = alertId ? document.getElementById(alertId) : null;
      if (!alertEl) {
        alertEl = document.createElement("div");
        alertEl.className = "alert alert-warning m-3";
        alertEl.setAttribute("role", "alert");
        if (alertId) {
          alertEl.id = alertId;
        }
        this.container.innerHTML = "";
        this.container.appendChild(alertEl);
      }
      alertEl.textContent = message;
    },

    createNetwork() {
      const options = {
        groups: GROUP_STYLES,
        nodes: {
          borderWidth: 2,
          borderWidthSelected: 3,
          font: NODE_LABEL_FONT,
          shape: "dot",
        },
        edges: {
          color: { color: "#95a5a6", highlight: "#7f8c8d" },
          width: 2,
          smooth: { enabled: true, type: "continuous", roundness: 0.1 },
          font: { size: 12, align: "horizontal" },
        },
        physics: {
          enabled: true,
          barnesHut: {
            gravitationalConstant: -2000,
            centralGravity: 0.3,
            springLength: 95,
            springConstant: 0.04,
            damping: 0.09,
          },
          stabilization: { iterations: 200 },
        },
        interaction: this.getInteractionOptions(),
      };

      this.network = new vis.Network(
        this.container,
        { nodes: this.nodesDataSet, edges: this.edgesDataSet },
        options
      );
      this.registerNetworkEvents();
    },

    getInteractionOptions() {
      return Object.assign({}, INTERACTION_OPTIONS, {
        dragNodes: true,
      });
    },

    setLayout(mode, options = {}) {
      if (!this.network || !this.nodesDataSet) return;
      this.currentLayout = mode;
      const shouldFit = options.fit !== false;

      // Update active button state
      const layoutGroup = this.config.layoutButtonGroupId
        ? document.getElementById(this.config.layoutButtonGroupId)
        : null;
      if (layoutGroup) {
        layoutGroup.querySelectorAll("button[data-layout]").forEach((btn) => {
          btn.classList.toggle("active", btn.dataset.layout === mode);
        });
      }
      this.updateProjectSpineControlsVisibility();

      if (mode === "organic") {
        // Remove any level/x/y overrides, re-enable physics
        const updates = Array.from(this.nodeIndex.keys()).map((id) => ({
          id,
          level: undefined,
          x: undefined,
          y: undefined,
          fixed: false,
        }));
        this.nodesDataSet.update(updates);
        this.physicsDisabled = false;
        this.network.setOptions({
          layout: { hierarchical: { enabled: false } },
          interaction: this.getInteractionOptions(),
          physics: {
            enabled: true,
            barnesHut: {
              gravitationalConstant: -2000,
              centralGravity: 0.3,
              springLength: 95,
              springConstant: 0.04,
              damping: 0.09,
            },
            stabilization: { iterations: 200 },
          },
        });
        this.network.stabilize();

      } else if (mode === "hierarchical") {
        // Custom hierarchical layout. Nodes are freely draggable after initial
        // placement. Horizontal order within each row uses iterative barycenter
        // passes so nodes sharing the same neighbours cluster together.
        const byGroup = Object.create(null);
        const edges = this.edgesDataSet ? this.edgesDataSet.get() : [];
        const roleGroupsByNode = new Map();

        edges.forEach((edge) => {
          const roleGroup = normalizeRoleGroup(edge.role_group || edge.role_code);
          if (!roleGroup) return;
          [edge.from, edge.to].forEach((nodeId) => {
            const node = this.nodeIndex.get(nodeId);
            if (!node || node.group === "project") return;
            if (!roleGroupsByNode.has(nodeId)) {
              roleGroupsByNode.set(nodeId, new Map());
            }
            const counts = roleGroupsByNode.get(nodeId);
            counts.set(roleGroup, (counts.get(roleGroup) || 0) + 1);
          });
        });

        for (const node of this.nodeIndex.values()) {
          let group = node.group === "project"
            ? "project"
            : chooseRoleGroup(roleGroupsByNode.get(node.id) || new Map());
          group = normalizeRoleGroup(group || node.group) || "company";
          if (!byGroup[group]) byGroup[group] = [];
          byGroup[group].push(node);
        }

        // Build adjacency for barycenter ordering
        const adjacency = new Map();
        for (const nodeId of this.nodeIndex.keys()) {
          adjacency.set(nodeId, new Set());
        }
        edges.forEach((edge) => {
          if (this.nodeIndex.has(edge.from) && this.nodeIndex.has(edge.to)) {
            adjacency.get(edge.from).add(edge.to);
            adjacency.get(edge.to).add(edge.from);
          }
        });

        // Seed with alphabetical order
        Object.values(byGroup).forEach((nodes) => {
          nodes.sort((a, b) => String(a.label).localeCompare(String(b.label)));
        });

        // Iterative barycenter passes: each row's nodes are sorted by the average
        // normalised position of their cross-row neighbours, pulling nodes that
        // share connections toward the same horizontal region.
        for (let pass = 0; pass < 5; pass++) {
          const posIdx = new Map();
          HIERARCHICAL_GROUP_ORDER.forEach((group) => {
            const nodes = byGroup[group] || [];
            nodes.forEach((node, i) => {
              posIdx.set(node.id, nodes.length > 1 ? i / (nodes.length - 1) : 0.5);
            });
          });

          HIERARCHICAL_GROUP_ORDER.forEach((group) => {
            const nodes = byGroup[group];
            if (!nodes || nodes.length < 2) return;
            const inGroup = new Set(nodes.map((n) => n.id));
            nodes.sort((a, b) => {
              const aExt = Array.from(adjacency.get(a.id) || []).filter(
                (id) => !inGroup.has(id) && posIdx.has(id)
              );
              const bExt = Array.from(adjacency.get(b.id) || []).filter(
                (id) => !inGroup.has(id) && posIdx.has(id)
              );
              const avgA = aExt.length
                ? aExt.reduce((s, id) => s + posIdx.get(id), 0) / aExt.length
                : 0.5;
              const avgB = bExt.length
                ? bExt.reduce((s, id) => s + posIdx.get(id), 0) / bExt.length
                : 0.5;
              return avgA - avgB || String(a.label).localeCompare(String(b.label));
            });
          });
        }

        // Swap refinement: measure actual edge crossings and try adjacent swaps.
        // Barycenter can settle in a local minimum; this pass makes exact
        // crossing-count decisions so it always improves or terminates.
        const countRowPairCrossings = (rowA, rowB) => {
          const posB = new Map(rowB.map((n, i) => [n.id, i]));
          const edges = [];
          rowA.forEach((n, i) => {
            for (const nbId of (adjacency.get(n.id) || new Set())) {
              if (posB.has(nbId)) edges.push([i, posB.get(nbId)]);
            }
          });
          let count = 0;
          for (let i = 0; i < edges.length - 1; i++) {
            for (let j = i + 1; j < edges.length; j++) {
              if ((edges[i][0] - edges[j][0]) * (edges[i][1] - edges[j][1]) < 0) count++;
            }
          }
          return count;
        };

        const totalCrossingsForGroup = (group) => {
          const row = byGroup[group] || [];
          let total = 0;
          HIERARCHICAL_GROUP_ORDER.forEach((other) => {
            if (other === group) return;
            const otherRow = byGroup[other] || [];
            if (otherRow.length) total += countRowPairCrossings(row, otherRow);
          });
          return total;
        };

        for (let iter = 0; iter < 20; iter++) {
          let improved = false;
          HIERARCHICAL_GROUP_ORDER.forEach((group) => {
            const nodes = byGroup[group];
            if (!nodes || nodes.length < 2) return;
            for (let i = 0; i < nodes.length - 1; i++) {
              const before = totalCrossingsForGroup(group);
              [nodes[i], nodes[i + 1]] = [nodes[i + 1], nodes[i]];
              if (totalCrossingsForGroup(group) < before) {
                improved = true;
              } else {
                [nodes[i], nodes[i + 1]] = [nodes[i + 1], nodes[i]];
              }
            }
          });
          if (!improved) break;
        }

        const X_SPACING = 260;
        const Y_SPACING = 120;
        const GROUP_GAP = 190;
        const MAX_PER_LANE = 8;
        const groupLayout = Object.create(null);
        let yCursor = 0;

        HIERARCHICAL_GROUP_ORDER.forEach((group) => {
          const nodes = byGroup[group] || [];
          if (!nodes.length) return;
          const laneCount = Math.ceil(nodes.length / MAX_PER_LANE);
          groupLayout[group] = {
            startY: yCursor,
            height: (laneCount - 1) * Y_SPACING,
          };
          yCursor += groupLayout[group].height + GROUP_GAP;
        });

        const yOffset = yCursor > 0 ? (yCursor - GROUP_GAP) / 2 : 0;
        const updates = [];
        HIERARCHICAL_GROUP_ORDER.forEach((group) => {
          const nodes = byGroup[group] || [];
          const layout = groupLayout[group];
          if (!layout) return;
          nodes.forEach((node, i) => {
            const lane = Math.floor(i / MAX_PER_LANE);
            const indexInLane = i % MAX_PER_LANE;
            const laneSize = Math.min(MAX_PER_LANE, nodes.length - lane * MAX_PER_LANE);
            const totalWidth = (laneSize - 1) * X_SPACING;
            updates.push({
              id: node.id,
              x: -totalWidth / 2 + indexInLane * X_SPACING,
              y: layout.startY + lane * Y_SPACING - yOffset,
              fixed: false,
              level: undefined,
            });
          });
        });
        this.physicsDisabled = true;
        this.network.setOptions({
          layout: { hierarchical: { enabled: false } },
          interaction: this.getInteractionOptions(),
          physics: { enabled: false },
        });
        this.nodesDataSet.update(updates);
        if (shouldFit) {
          this.network.fit({
            animation: { duration: 600, easingFunction: "easeInOutQuad" },
          });
        }
        // After fit, enforce a minimum scale so node dots stay large enough
        // to grab — fit() on a tall graph can zoom out to where nodes are
        // only ~16px wide, making drag feel broken.
        setTimeout(() => {
          if (shouldFit && this.network && this.currentLayout === "hierarchical" && this.network.getScale() < 0.5) {
            this.network.moveTo({
              scale: 0.5,
              animation: { duration: 300, easingFunction: "easeInOutQuad" },
            });
          }
        }, 700);

      } else if (mode === "columns") {
        // Pre-position nodes in x-bands by group, then let physics settle y
        const updates = Array.from(this.nodeIndex.values()).map((node) => ({
          id: node.id,
          x: COLUMN_X[node.group] ?? 0,
          y: undefined,
          level: undefined,
          fixed: { x: true, y: false },
        }));
        this.nodesDataSet.update(updates);
        this.physicsDisabled = false;
        this.network.setOptions({
          layout: { hierarchical: { enabled: false } },
          interaction: this.getInteractionOptions(),
          physics: {
            enabled: true,
            barnesHut: {
              gravitationalConstant: -3000,
              centralGravity: 0.05,
              springLength: 120,
              springConstant: 0.04,
              damping: 0.12,
            },
            stabilization: { iterations: 300 },
          },
        });
        this.network.stabilize();

      } else if (mode === "project-spine") {
        const edges = this.edgesDataSet ? this.edgesDataSet.get() : [];
        const projects = [];
        const companies = [];
        const projectCompanies = new Map();
        const companyProjects = new Map();

        for (const node of this.nodeIndex.values()) {
          if (node.group === "project") {
            projects.push(node);
            projectCompanies.set(node.id, new Set());
          } else {
            companies.push(node);
            companyProjects.set(node.id, new Set());
          }
        }

        edges.forEach((edge) => {
          const from = this.nodeIndex.get(edge.from);
          const to = this.nodeIndex.get(edge.to);
          if (!from || !to || from.group === to.group) return;
          const projectId = from.group === "project" ? from.id : to.id;
          const companyId = from.group === "project" ? to.id : from.id;
          if (projectCompanies.has(projectId) && companyProjects.has(companyId)) {
            projectCompanies.get(projectId).add(companyId);
            companyProjects.get(companyId).add(projectId);
          }
        });

        projects.sort((a, b) => String(a.label).localeCompare(String(b.label)));
        let projectOrder = projects.map((node) => node.id);
        const sharedCompanies = companies
          .filter((node) => (companyProjects.get(node.id) || new Set()).size > 1)
          .map((node) => node.id);

        // Repeated barycenter passes: order projects near the shared companies
        // they have in common, then order shared companies near their projects.
        let sharedOrder = sharedCompanies.slice();
        for (let pass = 0; pass < 6; pass += 1) {
          const projectIndex = new Map(projectOrder.map((id, index) => [id, index]));
          sharedOrder.sort((a, b) => {
            const aProjects = Array.from(companyProjects.get(a) || []);
            const bProjects = Array.from(companyProjects.get(b) || []);
            const avgA = aProjects.reduce((sum, id) => sum + projectIndex.get(id), 0) / aProjects.length;
            const avgB = bProjects.reduce((sum, id) => sum + projectIndex.get(id), 0) / bProjects.length;
            const degreeDiff = bProjects.length - aProjects.length;
            return avgA - avgB || degreeDiff || String(this.nodeIndex.get(a).label).localeCompare(String(this.nodeIndex.get(b).label));
          });

          const sharedIndex = new Map(sharedOrder.map((id, index) => [id, index]));
          projectOrder.sort((a, b) => {
            const aShared = Array.from(projectCompanies.get(a) || []).filter((id) => sharedIndex.has(id));
            const bShared = Array.from(projectCompanies.get(b) || []).filter((id) => sharedIndex.has(id));
            const avgA = aShared.length
              ? aShared.reduce((sum, id) => sum + sharedIndex.get(id), 0) / aShared.length
              : Number.MAX_SAFE_INTEGER;
            const avgB = bShared.length
              ? bShared.reduce((sum, id) => sum + sharedIndex.get(id), 0) / bShared.length
              : Number.MAX_SAFE_INTEGER;
            return avgA - avgB || String(this.nodeIndex.get(a).label).localeCompare(String(this.nodeIndex.get(b).label));
          });
        }

        const horizontalScale = this.projectSpineSpacingScale || 1;
        const PROJECT_X = 0;
        const SINGLE_X = 560 * horizontalScale;
        const SHARED_BASE_X = -560 * horizontalScale;
        const SHARED_LANE_X = 210 * horizontalScale;
        const SINGLE_Y_SPACING = this.projectSpineCompactRows ? 68 : 78;
        const SHARED_Y_SPACING = this.projectSpineCompactRows ? 72 : 82;
        const singleCompaniesByProject = new Map();
        const projectRightRows = new Map();

        projectOrder.forEach((projectId) => {
          const connectedCompanies = Array.from(projectCompanies.get(projectId) || []);
          const singleCompanies = connectedCompanies
            .filter((companyId) => (companyProjects.get(companyId) || new Set()).size === 1)
            .sort((a, b) => String(this.nodeIndex.get(a).label).localeCompare(String(this.nodeIndex.get(b).label)));
          singleCompaniesByProject.set(projectId, singleCompanies);
          projectRightRows.set(projectId, Math.max(1, singleCompanies.length));
        });

        const projectY = new Map();
        const singleCompanyY = new Map();
        const updates = [];

        if (this.projectSpineCompactRows) {
          const projectSpan = Math.max(0, projectOrder.length - 1) * SINGLE_Y_SPACING;
          projectOrder.forEach((id, index) => {
            const y = -projectSpan / 2 + index * SINGLE_Y_SPACING;
            projectY.set(id, y);
            updates.push({ id, x: PROJECT_X, y, fixed: false, level: undefined });
          });

          const singleCompanyOrder = [];
          projectOrder.forEach((projectId) => {
            singleCompanyOrder.push(...(singleCompaniesByProject.get(projectId) || []));
          });
          const singleSpan = Math.max(0, singleCompanyOrder.length - 1) * SINGLE_Y_SPACING;
          singleCompanyOrder.forEach((companyId, index) => {
            singleCompanyY.set(companyId, -singleSpan / 2 + index * SINGLE_Y_SPACING);
          });
        } else {
          const totalRightRows = projectOrder.reduce(
            (sum, id) => sum + projectRightRows.get(id),
            0
          );
          const totalProjectSpan = Math.max(0, totalRightRows - 1) * SINGLE_Y_SPACING;
          let yCursor = -totalProjectSpan / 2;

          projectOrder.forEach((id) => {
            const singleCompanies = singleCompaniesByProject.get(id) || [];
            const rows = projectRightRows.get(id);
            const firstY = yCursor;
            const lastY = firstY + (rows - 1) * SINGLE_Y_SPACING;
            const y = (firstY + lastY) / 2;
            singleCompanies.forEach((companyId, index) => {
              singleCompanyY.set(companyId, firstY + index * SINGLE_Y_SPACING);
            });
            projectY.set(id, y);
            updates.push({ id, x: PROJECT_X, y, fixed: false, level: undefined });
            yCursor = lastY + SINGLE_Y_SPACING;
          });
        }

        projectOrder.forEach((projectId) => {
          const singleCompanies = singleCompaniesByProject.get(projectId) || [];
          singleCompanies.forEach((companyId) => {
            updates.push({
              id: companyId,
              x: SINGLE_X,
              y: singleCompanyY.get(companyId),
              fixed: false,
              level: undefined,
            });
          });
        });

        const sharedUpdates = sharedOrder.map((companyId) => {
          const connectedProjects = Array.from(companyProjects.get(companyId) || []);
          const degree = connectedProjects.length;
          const avgY = connectedProjects.reduce((sum, id) => sum + projectY.get(id), 0) / degree;
          return {
            id: companyId,
            degree,
            x: SHARED_BASE_X - Math.max(0, degree - 2) * SHARED_LANE_X,
            y: avgY,
            idealY: avgY,
            label: this.nodeIndex.get(companyId).label,
          };
        });

        sharedUpdates.sort((a, b) => a.idealY - b.idealY || b.degree - a.degree || String(a.label).localeCompare(String(b.label)));
        for (let i = 1; i < sharedUpdates.length; i += 1) {
          if (sharedUpdates[i].y - sharedUpdates[i - 1].y < SHARED_Y_SPACING) {
            sharedUpdates[i].y = sharedUpdates[i - 1].y + SHARED_Y_SPACING;
          }
        }
        for (let i = sharedUpdates.length - 2; i >= 0; i -= 1) {
          if (sharedUpdates[i + 1].y - sharedUpdates[i].y < SHARED_Y_SPACING) {
            sharedUpdates[i].y = sharedUpdates[i + 1].y - SHARED_Y_SPACING;
          }
        }
        sharedUpdates.forEach((item) => {
          updates.push({
            id: item.id,
            x: item.x,
            y: item.y,
            fixed: false,
            level: undefined,
          });
        });

        this.physicsDisabled = true;
        this.network.setOptions({
          layout: { hierarchical: { enabled: false } },
          interaction: this.getInteractionOptions(),
          physics: { enabled: false },
        });
        this.nodesDataSet.update(updates);
        if (shouldFit) {
          this.network.fit({
            animation: { duration: 600, easingFunction: "easeInOutQuad" },
          });
        }
      }
    },

    updateProjectSpineSpacing() {
      if (!this.projectSpineSpacingInput) {
        this.projectSpineSpacingScale = 1;
        return;
      }
      const value = Number(this.projectSpineSpacingInput.value) || 100;
      const clamped = Math.min(200, Math.max(25, value));
      this.projectSpineSpacingScale = clamped / 100;
      if (this.projectSpineSpacingValue) {
        this.projectSpineSpacingValue.textContent = `${clamped}%`;
      }
    },

    updateProjectSpineCompactRows() {
      this.projectSpineCompactRows = !!(
        this.projectSpineCompactInput && this.projectSpineCompactInput.checked
      );
    },

    registerNetworkEvents() {
      if (!this.network) {
        return;
      }

      this.network.on("hoverNode", (params) => {
        const node = this.nodeIndex.get(params.node);
        if (node) {
          this.updateDetailPanel(node);
        }
      });

      this.network.on("blurNode", () => {
        this.clearDetailPanel();
      });

      this.network.on("doubleClick", (params) => {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0];
          const node = this.nodeIndex.get(nodeId);
          if (node && node.url) {
            window.location.href = node.url;
          }
        }
      });

      // Hold-to-open context menu (fires after ~600ms press on a node)
      const ctxMenu = document.getElementById("network-context-menu");
      const ctxFocus = document.getElementById("ctx-focus");
      const ctxOpen  = document.getElementById("ctx-open");
      let _ctxNodeId = null;

      const hideCtxMenu = () => {
        if (ctxMenu) ctxMenu.style.display = "none";
        _ctxNodeId = null;
      };

      if (ctxMenu) {
        // Manual hold detection on the canvas element directly (vis.js hold event unreliable)
        const canvas = this.container.querySelector("canvas");
        let _holdTimer = null;

        const startHold = (e) => {
          if (e.button !== 0) return;
          const rect = this.container.getBoundingClientRect();
          const nodeId = this.network.getNodeAt({
            x: e.clientX - rect.left,
            y: e.clientY - rect.top,
          });
          if (!nodeId) return;
          _holdTimer = setTimeout(() => {
            _ctxNodeId = nodeId;
            ctxMenu.style.left    = e.clientX + "px";
            ctxMenu.style.top     = e.clientY + "px";
            ctxMenu.style.display = "block";
            const node = this.nodeIndex.get(nodeId);
            if (ctxOpen) ctxOpen.style.display = (node && node.url) ? "flex" : "none";
          }, 600);
        };

        const cancelHold = () => { clearTimeout(_holdTimer); _holdTimer = null; };

        if (canvas) {
          canvas.addEventListener("mousedown", startHold);
          canvas.addEventListener("mouseup",   cancelHold);
          canvas.addEventListener("mousemove", cancelHold);
        }

        document.addEventListener("click", hideCtxMenu);
        document.addEventListener("keydown", (e) => {
          if (e.key === "Escape") hideCtxMenu();
        });

        if (ctxFocus) {
          ctxFocus.addEventListener("click", () => {
            if (_ctxNodeId) {
              if (this.focusSelect) this.focusSelect.value = _ctxNodeId;
              this.applyFocus(_ctxNodeId, this.focusDepth ? this.focusDepth.value : "2");
            }
            hideCtxMenu();
          });
        }

        if (ctxOpen) {
          ctxOpen.addEventListener("click", () => {
            if (_ctxNodeId) {
              const node = this.nodeIndex.get(_ctxNodeId);
              if (node && node.url) window.location.href = node.url;
            }
            hideCtxMenu();
          });
        }
      }

      this.network.on("stabilizationIterationsDone", () => {
        if (!this.physicsDisabled) {
          this.network.setOptions({ physics: false });
          this.physicsDisabled = true;
        }
      });

      this.network.on("afterDrawing", (ctx) => {
        this.drawNodeLabels(ctx);
      });
    },

    drawNodeLabels(ctx) {
      if (!this.network || !this.nodesDataSet) {
        return;
      }

      const nodes = this.nodesDataSet.get();
      if (!nodes.length) {
        return;
      }

      const positions = this.network.getPositions(nodes.map((node) => node.id));
      ctx.save();
      ctx.font = `${NODE_LABEL_FONT.weight} ${NODE_LABEL_FONT.size}px ${NODE_LABEL_FONT.face}`;
      ctx.fillStyle = NODE_LABEL_FONT.color;
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";

      nodes.forEach((node) => {
        const position = positions[node.id];
        const label = node.raw_label || node.label;
        if (!position || !label) {
          return;
        }

        const size = node.group === "project" ? 30 : 25;
        ctx.fillText(label, position.x + size * 1.05, position.y + size * 0.55);
      });

      ctx.restore();
    },

    populateFocusOptions() {
      if (!this.focusSelect) {
        return;
      }
      const currentValue = this.focusSelect.value;
      const firstOption = this.focusSelect.querySelector("option");

      this.focusSelect.innerHTML = "";
      if (firstOption) {
        this.focusSelect.appendChild(firstOption);
      } else {
        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "-- Show Entire Network --";
        this.focusSelect.appendChild(placeholder);
      }

      const nodes = Array.from(this.nodeIndex.values())
        .map((node) => ({ id: node.id, label: formatNodeLabel(node) }))
        .sort((a, b) => a.label.localeCompare(b.label));

      nodes.forEach((entry) => {
        const option = document.createElement("option");
        option.value = entry.id;
        option.textContent = entry.label;
        this.focusSelect.appendChild(option);
      });

      if (currentValue && this.nodeIndex.has(currentValue)) {
        this.focusSelect.value = currentValue;
      } else {
        this.focusSelect.value = "";
      }
    },

    updateStats(stats) {
      if (!stats || !this.statsDom) {
        return;
      }
      const totalNodesEl = document.querySelector(this.statsDom.totalNodes);
      const totalEdgesEl = document.querySelector(this.statsDom.totalEdges);
      const hiddenEl = document.querySelector(this.statsDom.hidden);

      if (totalNodesEl) {
        totalNodesEl.textContent =
          typeof stats.total_nodes === "number" ? stats.total_nodes : 0;
      }
      if (totalEdgesEl) {
        totalEdgesEl.textContent =
          typeof stats.total_edges === "number" ? stats.total_edges : 0;
      }
      if (hiddenEl) {
        hiddenEl.textContent =
          typeof stats.confidential_hidden === "number"
            ? stats.confidential_hidden
            : 0;
      }
    },

    updateDetailPanel(node) {
      if (!this.detailPanel) {
        return;
      }
      const placeholder = document.querySelector(
        this.detailPanel.placeholderSelector
      );
      const container = document.querySelector(
        this.detailPanel.containerSelector
      );
      const labelEl = document.querySelector(this.detailPanel.labelSelector);
      const descriptionEl = document.querySelector(
        this.detailPanel.descriptionSelector
      );

      if (!container || !labelEl || !descriptionEl) {
        return;
      }

      if (placeholder) {
        placeholder.classList.add("d-none");
      }
      container.classList.remove("d-none");
      labelEl.textContent = formatNodeLabel(node);
      descriptionEl.textContent = node.title || "";
    },

    clearDetailPanel() {
      if (!this.detailPanel) {
        return;
      }
      const placeholder = document.querySelector(
        this.detailPanel.placeholderSelector
      );
      const container = document.querySelector(
        this.detailPanel.containerSelector
      );

      if (placeholder) {
        placeholder.classList.remove("d-none");
      }
      if (container) {
        container.classList.add("d-none");
      }
    },

    applyFocus(nodeId, depth) {
      if (!nodeId) {
        this.clearFocus();
        return;
      }
      const parts = nodeId.split("_");
      if (parts.length < 2) {
        console.warn("Unexpected node id format", nodeId);
        return;
      }
      const type = parts[0];
      const rawId = parts.slice(1).join("_");
      const numericId = Number(rawId);
      this.currentFilters.focus_entity = {
        type: type,
        id: Number.isNaN(numericId) ? rawId : numericId,
      };
      this.currentFilters.depth = depth || "2";
      this.fetchAndRender();
    },

    clearFocus(triggerFetch = true) {
      this.currentFilters.focus_entity = null;
      this.currentFilters.depth = "all";
      if (this.focusSelect) {
        this.focusSelect.value = "";
      }
      if (this.focusDepth) {
        this.focusDepth.value = "all";
      }
      if (triggerFetch) {
        this.fetchAndRender();
      }
    },
  };

  global.NetworkDiagram = NetworkDiagram;
})(window);

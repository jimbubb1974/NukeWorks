(function (global) {
  const GROUP_LABELS = {
    company: "Company",
    project: "Project",
  };

  const GROUP_STYLES = {
    company: {
      shape: "dot",
      size: 25,
      color: {
        background: "#3498db",
        border: "#2980b9",
        highlight: { background: "#2980b9", border: "#21618c" },
      },
      font: { color: "#2c3e50", size: 14 },
    },
    project: {
      shape: "diamond",
      size: 30,
      color: {
        background: "#2ecc71",
        border: "#27ae60",
        highlight: { background: "#27ae60", border: "#1e8449" },
      },
      font: { color: "#2c3e50", size: 14 },
    },
  };

  function formatNodeLabel(node) {
    const groupLabel = GROUP_LABELS[node.group] || node.group;
    return groupLabel + " • " + node.label;
  }

  const NetworkDiagram = {
    config: {},
    network: null,
    nodesDataSet: null,
    edgesDataSet: null,
    nodeIndex: new Map(),
    currentFilters: {
      entity_types: ["company", "project"],
      relationship_types: ["project_company"],
      hide_unconnected_companies: false,
      show_edge_labels: true,
      focus_entity: null,
      depth: "all",
    },
    physicsDisabled: false,

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
      this.statsDom = config.statsSelectors;

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

      // Add live toggle for edge labels
      const showEdgeLabelsInput = this.filterForm
        ? this.filterForm.querySelector('input[name="show_edge_labels"]')
        : null;
      if (showEdgeLabelsInput) {
        showEdgeLabelsInput.addEventListener("change", () => {
          this.currentFilters.show_edge_labels = showEdgeLabelsInput.checked;
          this.toggleEdgeLabels(showEdgeLabelsInput.checked);
        });
      }
    },

    toggleEdgeLabels(show) {
      if (!this.edgesDataSet) return;

      const edges = this.edgesDataSet.get();
      const updatedEdges = edges.map((edge) => {
        // Keep the original label in title (tooltip), but remove/restore the visible label
        if (show) {
          // Restore label from title if it exists
          const match = edge.title ? edge.title.match(/\(([^)]+)\)/) : null;
          return {
            ...edge,
            label: match ? match[1] : edge.label,
          };
        } else {
          return {
            ...edge,
            label: undefined,
          };
        }
      });

      this.edgesDataSet.update(updatedEdges);
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
      const hideUnconnectedInput = this.filterForm.querySelector(
        'input[name="hide_unconnected_companies"]'
      );
      const showEdgeLabelsInput = this.filterForm.querySelector(
        'input[name="show_edge_labels"]'
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
      if (hideUnconnectedInput) {
        this.currentFilters.hide_unconnected_companies =
          hideUnconnectedInput.checked;
      }
      if (showEdgeLabelsInput) {
        this.currentFilters.show_edge_labels = showEdgeLabelsInput.checked;
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
      const hideUnconnectedInput = this.filterForm.querySelector(
        'input[name="hide_unconnected_companies"]'
      );
      const showEdgeLabelsInput = this.filterForm.querySelector(
        'input[name="show_edge_labels"]'
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
      if (hideUnconnectedInput) {
        this.currentFilters.hide_unconnected_companies =
          hideUnconnectedInput.checked;
      }
      if (showEdgeLabelsInput) {
        this.currentFilters.show_edge_labels = showEdgeLabelsInput.checked;
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

      // Filter out unconnected companies if the option is enabled
      let filteredNodes = data.nodes;
      let filteredEdges = data.edges;

      if (this.currentFilters.hide_unconnected_companies) {
        // Build a set of company IDs that have connections to projects
        const connectedCompanyIds = new Set();
        data.edges.forEach((edge) => {
          // Extract company node IDs from edges (format: "company_123")
          if (edge.from && edge.from.startsWith("company_")) {
            connectedCompanyIds.add(edge.from);
          }
          if (edge.to && edge.to.startsWith("company_")) {
            connectedCompanyIds.add(edge.to);
          }
        });

        // Filter nodes to keep only: projects + connected companies
        filteredNodes = data.nodes.filter((node) => {
          if (node.group === "project") {
            return true; // Always keep projects
          }
          if (node.group === "company") {
            return connectedCompanyIds.has(node.id); // Only keep connected companies
          }
          return true; // Keep other node types
        });
      }

      filteredNodes.forEach((node) => {
        this.nodeIndex.set(node.id, node);
      });

      // Debug: Log edge colors
      console.log("Sample edges:", filteredEdges.slice(0, 3));

      // Apply edge label visibility setting
      if (!this.currentFilters.show_edge_labels) {
        filteredEdges = filteredEdges.map((edge) => ({
          ...edge,
          label: undefined, // Remove labels when toggle is off
        }));
      }

      if (!this.nodesDataSet || !this.edgesDataSet) {
        this.nodesDataSet = new vis.DataSet(filteredNodes);
        this.edgesDataSet = new vis.DataSet(filteredEdges);
        this.createNetwork();
      } else {
        this.nodesDataSet.clear();
        this.edgesDataSet.clear();
        if (filteredNodes.length > 0) {
          this.nodesDataSet.add(filteredNodes);
        }
        if (filteredEdges.length > 0) {
          this.edgesDataSet.add(filteredEdges);
        }
      }

      if (this.network) {
        // Re-enable physics for new layout and let stabilization disable it again
        this.physicsDisabled = false;
        this.network.setOptions({ physics: { enabled: true } });
        this.network.stabilize();
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
        } else {
          this.network.fit({
            animation: { duration: 600, easingFunction: "easeInOutQuad" },
          });
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
          font: { size: 14, face: "Arial" },
          shape: "dot",
        },
        edges: {
          width: 2,
          smooth: { type: "continuous" },
          font: { size: 12, align: "horizontal" },
          color: { inherit: false },
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
        interaction: {
          hover: true,
          tooltipDelay: 200,
          navigationButtons: false,
          keyboard: true,
        },
      };

      this.network = new vis.Network(
        this.container,
        { nodes: this.nodesDataSet, edges: this.edgesDataSet },
        options
      );
      this.registerNetworkEvents();
    },

    registerNetworkEvents() {
      if (!this.network) {
        return;
      }

      this.network.on("click", (params) => {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0];
          const node = this.nodeIndex.get(nodeId);
          if (node && node.url) {
            window.location.href = node.url;
          }
        }
      });

      // Node detail panel removed - tooltips provide node information

      this.network.on("doubleClick", (params) => {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0];
          const node = this.nodeIndex.get(nodeId);
          if (node) {
            if (this.focusSelect) {
              this.focusSelect.value = nodeId;
            }
            this.applyFocus(
              nodeId,
              this.focusDepth ? this.focusDepth.value : "2"
            );
          }
        }
      });

      this.network.on("stabilizationIterationsDone", () => {
        if (!this.physicsDisabled) {
          this.network.setOptions({ physics: false });
          this.physicsDisabled = true;
        }
      });
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

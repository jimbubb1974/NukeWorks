(function (global) {
    const GROUP_LABELS = {
        vendor: 'Vendor',
        owner: 'Owner',
        project: 'Project',
        constructor: 'Constructor',
        operator: 'Operator',
        offtaker: 'Off-taker'
    };

    const GROUP_STYLES = {
        vendor: {
            shape: 'dot',
            size: 25,
            color: {
                background: '#e74c3c',
                border: '#c0392b',
                highlight: { background: '#c0392b', border: '#a93226' }
            },
            font: { color: '#2c3e50', size: 14 }
        },
        owner: {
            shape: 'box',
            color: {
                background: '#3498db',
                border: '#2980b9',
                highlight: { background: '#2980b9', border: '#21618c' }
            },
            font: { color: '#2c3e50', size: 14 }
        },
        project: {
            shape: 'diamond',
            size: 30,
            color: {
                background: '#2ecc71',
                border: '#27ae60',
                highlight: { background: '#27ae60', border: '#1e8449' }
            },
            font: { color: '#2c3e50', size: 14 }
        },
        constructor: {
            shape: 'triangle',
            size: 25,
            color: {
                background: '#f39c12',
                border: '#d68910',
                highlight: { background: '#d68910', border: '#b9770e' }
            },
            font: { color: '#2c3e50', size: 14 }
        },
        operator: {
            shape: 'triangleDown',
            size: 25,
            color: {
                background: '#9b59b6',
                border: '#8e44ad',
                highlight: { background: '#8e44ad', border: '#76448a' }
            },
            font: { color: '#2c3e50', size: 14 }
        },
        offtaker: {
            shape: 'hexagon',
            size: 26,
            color: {
                background: '#16a085',
                border: '#13856d',
                highlight: { background: '#13856d', border: '#0e5f4a' }
            },
            font: { color: '#2c3e50', size: 14 }
        }
    };

    function formatNodeLabel(node) {
        const groupLabel = GROUP_LABELS[node.group] || node.group;
        return groupLabel + ' • ' + node.label;
    }

    const NetworkDiagram = {
        config: {},
        network: null,
        nodesDataSet: null,
        edgesDataSet: null,
        nodeIndex: new Map(),
        currentFilters: {
            entity_types: ['vendor', 'owner', 'project', 'constructor', 'operator', 'offtaker'],
            relationship_types: ['owner_vendor', 'project_vendor', 'project_owner', 'project_constructor', 'project_operator', 'vendor_supplier', 'vendor_constructor', 'project_offtaker'],
            focus_entity: null,
            depth: 'all'
        },
        physicsDisabled: false,

        init(config) {
            this.config = config;
            this.container = document.getElementById(config.containerId);
            this.loadingIndicator = document.getElementById(config.loadingIndicatorId);
            this.filterForm = document.getElementById(config.filterFormId);
            this.focusForm = document.getElementById(config.focusFormId);
            this.focusSelect = document.getElementById(config.focusSelectId);
            this.focusDepth = document.getElementById(config.focusDepthId);
            this.clearFocusBtn = document.getElementById(config.clearFocusButtonId);
            this.resetViewBtn = document.getElementById(config.resetViewButtonId);
            this.resetPhysicsBtn = document.getElementById(config.resetPhysicsButtonId);
            this.statsDom = config.statsSelectors;
            this.detailPanel = config.detailPanel;

            if (!this.container) {
                console.error('Network container not found');
                return;
            }

            this.ensureVisAvailable(() => {
                this.attachEventListeners();
                this.readFiltersFromForm();
                this.fetchAndRender();
            });
        },

        ensureVisAvailable(onReady) {
            if (global.vis && typeof global.vis.Network === 'function' && typeof global.vis.DataSet === 'function') {
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
            this.showError('Visualization library failed to load. Please ensure Vis.js is available (the CDN may be blocked).');
            console.error('Vis.js not available.');
        },

        attachEventListeners() {
            if (this.filterForm) {
                this.filterForm.addEventListener('submit', (event) => {
                    event.preventDefault();
                    if (this.updateFiltersFromForm()) {
                        this.fetchAndRender();
                    }
                });
            }

            if (this.focusForm) {
                this.focusForm.addEventListener('submit', (event) => {
                    event.preventDefault();
                    const selected = this.focusSelect ? this.focusSelect.value : '';
                    const depth = this.focusDepth ? this.focusDepth.value : 'all';
                    this.applyFocus(selected, depth);
                });
            }

            if (this.clearFocusBtn) {
                this.clearFocusBtn.addEventListener('click', () => {
                    this.clearFocus();
                });
            }

            if (this.resetViewBtn) {
                this.resetViewBtn.addEventListener('click', () => {
                    if (this.network) {
                        this.network.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } });
                    }
                });
            }

            if (this.resetPhysicsBtn) {
                this.resetPhysicsBtn.addEventListener('click', () => {
                    if (this.network) {
                        this.physicsDisabled = false;
                        this.network.setOptions({ physics: { enabled: true } });
                        this.network.stabilize();
                    }
                });
            }
        },

        readFiltersFromForm() {
            if (!this.filterForm) {
                return;
            }
            const entityInputs = this.filterForm.querySelectorAll('input[name="entity_types"]');
            const relationshipInputs = this.filterForm.querySelectorAll('input[name="relationship_types"]');

            const selectedEntities = Array.from(entityInputs).filter((input) => input.checked).map((input) => input.value);
            const selectedRelationships = Array.from(relationshipInputs).filter((input) => input.checked).map((input) => input.value);

            if (selectedEntities.length > 0) {
                this.currentFilters.entity_types = selectedEntities;
            }
            if (selectedRelationships.length > 0) {
                this.currentFilters.relationship_types = selectedRelationships;
            }
        },

        updateFiltersFromForm() {
            if (!this.filterForm) {
                return false;
            }
            const entityInputs = this.filterForm.querySelectorAll('input[name="entity_types"]');
            const relationshipInputs = this.filterForm.querySelectorAll('input[name="relationship_types"]');

            const selectedEntities = Array.from(entityInputs).filter((input) => input.checked).map((input) => input.value);
            const selectedRelationships = Array.from(relationshipInputs).filter((input) => input.checked).map((input) => input.value);

            if (selectedEntities.length === 0) {
                alert('Select at least one entity type.');
                return false;
            }
            if (selectedRelationships.length === 0) {
                alert('Select at least one relationship type.');
                return false;
            }

            this.currentFilters.entity_types = selectedEntities;
            this.currentFilters.relationship_types = selectedRelationships;

            // Clear focus if it conflicts with new filters
            if (this.currentFilters.focus_entity && !this.currentFilters.entity_types.includes(this.currentFilters.focus_entity.type)) {
                this.clearFocus(false);
            }
            return true;
        },

        showLoading() {
            if (this.loadingIndicator) {
                this.loadingIndicator.classList.remove('d-none');
            }
        },

        hideLoading() {
            if (this.loadingIndicator) {
                this.loadingIndicator.classList.add('d-none');
            }
        },

        async fetchAndRender() {
            if (!this.config.dataUrl) {
                console.error('Data URL is not configured');
                return;
            }
            this.showLoading();

            const payload = Object.assign({}, this.currentFilters);
            if (!payload.focus_entity) {
                delete payload.focus_entity;
                payload.depth = 'all';
            }

            try {
                const response = await fetch(this.config.dataUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'same-origin',
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    throw new Error('Failed to load network data');
                }

                let data;
                try {
                    data = await response.json();
                } catch (jsonError) {
                    throw new Error('Unable to parse network data response.');
                }
                this.updateData(data);
            } catch (error) {
                console.error(error);
                this.showError('Unable to load network diagram data. Check your session or reload the page.');
            } finally {
                this.hideLoading();
            }
        },

        updateData(data) {
            this.nodeIndex.clear();
            data.nodes.forEach((node) => {
                this.nodeIndex.set(node.id, node);
            });

            if (!this.nodesDataSet || !this.edgesDataSet) {
                this.nodesDataSet = new vis.DataSet(data.nodes);
                this.edgesDataSet = new vis.DataSet(data.edges);
                this.createNetwork();
            } else {
                this.nodesDataSet.clear();
                this.edgesDataSet.clear();
                if (data.nodes.length > 0) {
                    this.nodesDataSet.add(data.nodes);
                }
                if (data.edges.length > 0) {
                    this.edgesDataSet.add(data.edges);
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
                    const focusNodeId = this.currentFilters.focus_entity.type + '_' + this.currentFilters.focus_entity.id;
                    if (this.nodeIndex.has(focusNodeId)) {
                        this.network.focus(focusNodeId, {
                            scale: 1.2,
                            animation: { duration: 600, easingFunction: 'easeInOutQuad' }
                        });
                    }
                } else {
                    this.network.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } });
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
                alertEl = document.createElement('div');
                alertEl.className = 'alert alert-warning m-3';
                alertEl.setAttribute('role', 'alert');
                if (alertId) {
                    alertEl.id = alertId;
                }
                this.container.innerHTML = '';
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
                    font: { size: 14, face: 'Arial' },
                    shape: 'dot'
                },
                edges: {
                    color: { color: '#95a5a6', highlight: '#7f8c8d' },
                    width: 2,
                    smooth: { type: 'continuous' },
                    font: { size: 12, align: 'horizontal' }
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
                    stabilization: { iterations: 200 }
                },
                interaction: {
                    hover: true,
                    tooltipDelay: 200,
                    navigationButtons: true,
                    keyboard: true
                }
            };

            this.network = new vis.Network(this.container, { nodes: this.nodesDataSet, edges: this.edgesDataSet }, options);
            this.registerNetworkEvents();
        },

        registerNetworkEvents() {
            if (!this.network) {
                return;
            }

            this.network.on('click', (params) => {
                if (params.nodes.length > 0) {
                    const nodeId = params.nodes[0];
                    const node = this.nodeIndex.get(nodeId);
                    if (node && node.url) {
                        window.location.href = node.url;
                    }
                }
            });

            this.network.on('hoverNode', (params) => {
                const node = this.nodeIndex.get(params.node);
                if (node) {
                    this.updateDetailPanel(node);
                }
            });

            this.network.on('blurNode', () => {
                this.clearDetailPanel();
            });

            this.network.on('doubleClick', (params) => {
                if (params.nodes.length > 0) {
                    const nodeId = params.nodes[0];
                    const node = this.nodeIndex.get(nodeId);
                    if (node) {
                        if (this.focusSelect) {
                            this.focusSelect.value = nodeId;
                        }
                        this.applyFocus(nodeId, this.focusDepth ? this.focusDepth.value : '2');
                    }
                }
            });

            this.network.on('stabilizationIterationsDone', () => {
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
            const firstOption = this.focusSelect.querySelector('option');

            this.focusSelect.innerHTML = '';
            if (firstOption) {
                this.focusSelect.appendChild(firstOption);
            } else {
                const placeholder = document.createElement('option');
                placeholder.value = '';
                placeholder.textContent = '-- Show Entire Network --';
                this.focusSelect.appendChild(placeholder);
            }

            const nodes = Array.from(this.nodeIndex.values())
                .map((node) => ({ id: node.id, label: formatNodeLabel(node) }))
                .sort((a, b) => a.label.localeCompare(b.label));

            nodes.forEach((entry) => {
                const option = document.createElement('option');
                option.value = entry.id;
                option.textContent = entry.label;
                this.focusSelect.appendChild(option);
            });

            if (currentValue && this.nodeIndex.has(currentValue)) {
                this.focusSelect.value = currentValue;
            } else {
                this.focusSelect.value = '';
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
                totalNodesEl.textContent = typeof stats.total_nodes === 'number' ? stats.total_nodes : 0;
            }
            if (totalEdgesEl) {
                totalEdgesEl.textContent = typeof stats.total_edges === 'number' ? stats.total_edges : 0;
            }
            if (hiddenEl) {
                hiddenEl.textContent = typeof stats.confidential_hidden === 'number' ? stats.confidential_hidden : 0;
            }
        },

        updateDetailPanel(node) {
            if (!this.detailPanel) {
                return;
            }
            const placeholder = document.querySelector(this.detailPanel.placeholderSelector);
            const container = document.querySelector(this.detailPanel.containerSelector);
            const labelEl = document.querySelector(this.detailPanel.labelSelector);
            const descriptionEl = document.querySelector(this.detailPanel.descriptionSelector);

            if (!container || !labelEl || !descriptionEl) {
                return;
            }

            if (placeholder) {
                placeholder.classList.add('d-none');
            }
            container.classList.remove('d-none');
            labelEl.textContent = formatNodeLabel(node);
            descriptionEl.textContent = node.title || '';
        },

        clearDetailPanel() {
            if (!this.detailPanel) {
                return;
            }
            const placeholder = document.querySelector(this.detailPanel.placeholderSelector);
            const container = document.querySelector(this.detailPanel.containerSelector);

            if (placeholder) {
                placeholder.classList.remove('d-none');
            }
            if (container) {
                container.classList.add('d-none');
            }
        },

        applyFocus(nodeId, depth) {
            if (!nodeId) {
                this.clearFocus();
                return;
            }
            const parts = nodeId.split('_');
            if (parts.length < 2) {
                console.warn('Unexpected node id format', nodeId);
                return;
            }
            const type = parts[0];
            const rawId = parts.slice(1).join('_');
            const numericId = Number(rawId);
            this.currentFilters.focus_entity = {
                type: type,
                id: Number.isNaN(numericId) ? rawId : numericId
            };
            this.currentFilters.depth = depth || '2';
            this.fetchAndRender();
        },

        clearFocus(triggerFetch = true) {
            this.currentFilters.focus_entity = null;
            this.currentFilters.depth = 'all';
            if (this.focusSelect) {
                this.focusSelect.value = '';
            }
            if (this.focusDepth) {
                this.focusDepth.value = 'all';
            }
            if (triggerFetch) {
                this.fetchAndRender();
            }
        }
    };

    global.NetworkDiagram = NetworkDiagram;
})(window);

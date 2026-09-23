document.addEventListener('DOMContentLoaded', () => {
    // API Host Configuration (Parameterizable via window.API_BASE_URL)
    const API_BASE_URL = (window.API_BASE_URL || 'http://127.0.0.1:5000').replace(/\/$/, '');

    // DOM Elements
    const toastContainer = document.getElementById('toast-container');
    const backendStatusPill = document.getElementById('backend-status-pill');
    const backendStatusText = document.getElementById('backend-status-text');
    const navTabs = document.querySelectorAll('.nav-tab');
    const viewPanels = document.querySelectorAll('.view-panel');

    // Cytoscape Canvas Initialization
    const cy = cytoscape({
        container: document.getElementById('cy'),
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': '#3c3833',
                    'border-color': '#e6e3da',
                    'border-width': 2,
                    'color': '#ffffff',
                    'font-family': "'IBM Plex Mono', monospace",
                    'font-size': 11,
                    'font-weight': 500,
                    'height': 48,
                    'label': 'data(label)',
                    'overlay-opacity': 0,
                    'text-background-color': '#1c1b18',
                    'text-background-opacity': 0.82,
                    'text-background-padding': 4,
                    'text-margin-y': 8,
                    'text-max-width': 130,
                    'text-valign': 'bottom',
                    'text-wrap': 'ellipsis',
                    'transition-duration': '0.25s',
                    'transition-property': 'width, height, background-color, border-color',
                    'width': 48
                }
            },
            {
                selector: 'node.top-ranked',
                style: {
                    'background-color': '#b38234',
                    'border-color': '#f7e9cc',
                    'color': '#ffffff'
                }
            },
            {
                selector: 'edge',
                style: {
                    'arrow-scale': 1.15,
                    'curve-style': 'bezier',
                    'line-color': '#8c877c',
                    'target-arrow-color': '#8c877c',
                    'target-arrow-shape': 'triangle',
                    'transition-duration': '0.25s',
                    'transition-property': 'line-color, target-arrow-color, width',
                    'width': 2.2
                }
            },
            {
                selector: 'edge.top-inbound',
                style: {
                    'line-color': '#b38234',
                    'target-arrow-color': '#b38234',
                    'width': 4
                }
            }
        ],
        layout: { name: 'grid' },
        boxSelectionEnabled: false,
        userPanningEnabled: true,
        userZoomingEnabled: true
    });

    const addNodeBtn = document.getElementById('add-node-btn');
    const nodeInput = document.getElementById('node-name');
    const addLinkBtn = document.getElementById('add-link-btn');
    const sourceInput = document.getElementById('link-source');
    const targetInput = document.getElementById('link-target');
    const loadSampleBtn = document.getElementById('load-sample-btn');
    const clearBtn = document.getElementById('clear-btn');
    const calculateBtn = document.getElementById('calculate-btn');
    const relayoutBtn = document.getElementById('relayout-btn');
    const fitBtn = document.getElementById('fit-btn');
    const resultsSection = document.getElementById('results-section');
    const loadingText = document.getElementById('loading');
    const rankingList = document.getElementById('ranking-list');
    const crawlSummary = document.getElementById('crawl-summary');
    const crawlBtn = document.getElementById('crawl-btn');
    const crawlUrl = document.getElementById('crawl-url');
    const crawlLimit = document.getElementById('crawl-limit');
    const nodeCount = document.getElementById('graph-node-count');
    const linkCount = document.getElementById('graph-link-count');
    const topNode = document.getElementById('top-node');
    const emptyState = document.getElementById('empty-state');

    // Explorer Canvas Control Elements
    const nodeDetailDrawer = document.getElementById('node-detail-drawer');
    const drawerNodeId = document.getElementById('drawer-node-id');
    const drawerCloseBtn = document.getElementById('drawer-close-btn');
    const drawerPageRank = document.getElementById('drawer-pagerank');
    const drawerInDegree = document.getElementById('drawer-indegree');
    const drawerOutDegree = document.getElementById('drawer-outdegree');
    const drawerInboundList = document.getElementById('drawer-inbound-list');
    const drawerOutboundList = document.getElementById('drawer-outbound-list');
    const drawerInboundCount = document.getElementById('drawer-inbound-count');
    const drawerOutboundCount = document.getElementById('drawer-outbound-count');
    const deleteNodeBtn = document.getElementById('delete-node-btn');
    const searchInput = document.getElementById('node-search-input');
    const layoutSelect = document.getElementById('layout-select');
    const zoomInBtn = document.getElementById('zoom-in-btn');
    const zoomOutBtn = document.getElementById('zoom-out-btn');
    const zoomResetBtn = document.getElementById('zoom-reset-btn');

    let activeSelectedNode = null;
    let lastComputedScores = null;

    // ==========================================================================
    // Non-Modal Toast Notification System (Replaces browser alert())
    // ==========================================================================
    function showToast(message, type = 'error', duration = 4500) {
        if (!toastContainer) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const msgSpan = document.createElement('span');
        msgSpan.className = 'toast-message';
        msgSpan.textContent = message;

        const closeBtn = document.createElement('button');
        closeBtn.className = 'toast-close';
        closeBtn.setAttribute('aria-label', 'Close notification');
        closeBtn.textContent = '×';
        closeBtn.onclick = () => toast.remove();

        toast.append(msgSpan, closeBtn);
        toastContainer.appendChild(toast);

        if (duration > 0) {
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.style.opacity = '0';
                    toast.style.transition = 'opacity 0.25s ease';
                    setTimeout(() => toast.remove(), 250);
                }
            }, duration);
        }
    }

    // ==========================================================================
    // Backend Connection Status Ping
    // ==========================================================================
    async function checkBackendHealth() {
        if (!backendStatusPill || !backendStatusText) return;

        try {
            const displayHost = API_BASE_URL.replace(/^https?:\/\//, '');
            const response = await fetch(`${API_BASE_URL}/calculate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pages: ['A'], links: [] })
            });

            if (response.ok) {
                backendStatusPill.classList.remove('status-offline');
                backendStatusPill.classList.add('status-online');
                backendStatusPill.title = `Backend Connected (${API_BASE_URL})`;
                backendStatusText.textContent = displayHost;
            } else {
                throw new Error('Backend returned status ' + response.status);
            }
        } catch {
            backendStatusPill.classList.remove('status-online');
            backendStatusPill.classList.add('status-offline');
            backendStatusPill.title = `Backend Disconnected (${API_BASE_URL})`;
            const displayHost = API_BASE_URL.replace(/^https?:\/\//, '');
            backendStatusText.textContent = `${displayHost} (Offline)`;
        }
    }

    // ==========================================================================
    // Navigation & View Panel Routing
    // ==========================================================================
    navTabs.forEach((tab) => {
        tab.addEventListener('click', () => {
            const targetTab = tab.getAttribute('data-tab');

            navTabs.forEach((t) => {
                t.classList.remove('active');
                t.setAttribute('aria-selected', 'false');
            });
            tab.classList.add('active');
            tab.setAttribute('aria-selected', 'true');

            viewPanels.forEach((panel) => {
                panel.classList.remove('active-view');
            });

            const activePanel = document.getElementById(`view-${targetTab}`);
            if (activePanel) {
                activePanel.classList.add('active-view');
            }

            if (targetTab === 'explorer') {
                setTimeout(() => {
                    cy.resize();
                    if (cy.nodes().length > 0) {
                        cy.fit(undefined, 70);
                    }
                }, 50);
            }
        });
    });

    // ==========================================================================
    // Step 4: Interactive Graph Explorer & Node Inspector Drawer
    // ==========================================================================
    function openNodeDrawer(node) {
        if (!nodeDetailDrawer) return;
        activeSelectedNode = node;

        const nodeId = node.id();
        drawerNodeId.textContent = labelFromValue(nodeId);
        drawerNodeId.title = nodeId;

        // Calculate degrees and neighbor lists safely
        const inboundEdges = node.incomers('edge');
        const outboundEdges = node.outgoers('edge');

        drawerInDegree.textContent = inboundEdges.length;
        drawerOutDegree.textContent = outboundEdges.length;
        drawerInboundCount.textContent = inboundEdges.length;
        drawerOutboundCount.textContent = outboundEdges.length;

        // Display PageRank score
        if (lastComputedScores && lastComputedScores[nodeId] !== undefined) {
            drawerPageRank.textContent = lastComputedScores[nodeId].toFixed(4);
        } else {
            drawerPageRank.textContent = 'Uncomputed';
        }

        // Render Inbound neighbor items text-safely
        drawerInboundList.innerHTML = '';
        inboundEdges.forEach((edge) => {
            const li = document.createElement('li');
            li.className = 'neighbor-item';
            li.textContent = labelFromValue(edge.source().id());
            li.title = edge.source().id();
            drawerInboundList.appendChild(li);
        });
        if (inboundEdges.length === 0) {
            const emptyLi = document.createElement('li');
            emptyLi.className = 'neighbor-item';
            emptyLi.style.opacity = '0.6';
            emptyLi.textContent = 'None';
            drawerInboundList.appendChild(emptyLi);
        }

        // Render Outbound neighbor items text-safely
        drawerOutboundList.innerHTML = '';
        outboundEdges.forEach((edge) => {
            const li = document.createElement('li');
            li.className = 'neighbor-item';
            li.textContent = labelFromValue(edge.target().id());
            li.title = edge.target().id();
            drawerOutboundList.appendChild(li);
        });
        if (outboundEdges.length === 0) {
            const emptyLi = document.createElement('li');
            emptyLi.className = 'neighbor-item';
            emptyLi.style.opacity = '0.6';
            emptyLi.textContent = 'None';
            drawerOutboundList.appendChild(emptyLi);
        }

        nodeDetailDrawer.classList.remove('hidden');
    }

    function closeNodeDrawer() {
        if (!nodeDetailDrawer) return;
        nodeDetailDrawer.classList.add('hidden');
        activeSelectedNode = null;
    }

    if (drawerCloseBtn) {
        drawerCloseBtn.addEventListener('click', closeNodeDrawer);
    }

    if (deleteNodeBtn) {
        deleteNodeBtn.addEventListener('click', () => {
            if (!activeSelectedNode) return;
            const targetId = activeSelectedNode.id();
            cy.remove(activeSelectedNode);
            closeNodeDrawer();
            clearScores();
            applyLayout();
            showToast(`Node "${labelFromValue(targetId)}" removed from graph.`, 'info');
        });
    }

    // Cytoscape Canvas Interactive Event Binding
    cy.on('tap', 'node', (evt) => {
        openNodeDrawer(evt.target);
    });

    cy.on('tap', (evt) => {
        if (evt.target === cy) {
            closeNodeDrawer();
        }
    });

    // Right-Click Context Tap to Remove Edge
    cy.on('cxttap', 'edge', (evt) => {
        const edge = evt.target;
        const sourceId = labelFromValue(edge.data('source'));
        const targetId = labelFromValue(edge.data('target'));
        cy.remove(edge);
        clearScores();
        updateStats();
        if (activeSelectedNode) {
            openNodeDrawer(activeSelectedNode);
        }
        showToast(`Directed link "${sourceId} → ${targetId}" removed.`, 'info');
    });

    // Search Node Filter
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            const query = normalizeInput(searchInput.value).toLowerCase();
            cy.nodes().forEach((node) => {
                const match = node.id().toLowerCase().includes(query) || node.data('label').toLowerCase().includes(query);
                node.style('opacity', match || !query ? 1 : 0.15);
            });
        });
    }

    // Layout Selector
    if (layoutSelect) {
        layoutSelect.addEventListener('change', () => {
            const choice = layoutSelect.value;
            const layoutName = choice === 'auto' ? (cy.nodes().length > 8 ? 'cose' : 'circle') : choice;
            cy.layout({
                name: layoutName,
                animate: true,
                animationDuration: 450,
                fit: true,
                padding: 70
            }).run();
        });
    }

    // Canvas Zoom Controls
    if (zoomInBtn) {
        zoomInBtn.addEventListener('click', () => {
            cy.zoom({
                level: cy.zoom() * 1.25,
                renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 }
            });
        });
    }

    if (zoomOutBtn) {
        zoomOutBtn.addEventListener('click', () => {
            cy.zoom({
                level: cy.zoom() * 0.8,
                renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 }
            });
        });
    }

    if (zoomResetBtn) {
        zoomResetBtn.addEventListener('click', () => {
            cy.zoom(1);
            cy.center();
        });
    }

    // Data Helpers
    const normalizeInput = (value) => value.trim().replace(/\s+/g, ' ');

    const labelFromValue = (value) => {
        try {
            const url = new URL(value);
            const path = url.pathname === '/' ? '/' : url.pathname.replace(/\/$/, '');
            return `${url.hostname}${path}`.slice(0, 42);
        } catch {
            return value.slice(0, 42);
        }
    };

    const updateStats = (scores = null) => {
        nodeCount.textContent = cy.nodes().length;
        linkCount.textContent = cy.edges().length;
        emptyState.classList.toggle('hidden', cy.nodes().length > 0);

        if (!scores || Object.keys(scores).length === 0) {
            topNode.textContent = 'None';
            topNode.title = '';
            return;
        }

        const [winner] = Object.entries(scores).sort((a, b) => b[1] - a[1])[0];
        topNode.textContent = labelFromValue(winner);
        topNode.title = winner;
    };

    const applyLayout = () => {
        const choice = layoutSelect ? layoutSelect.value : 'auto';
        const layoutName = choice === 'auto' ? (cy.nodes().length > 8 ? 'cose' : 'circle') : choice;
        cy.layout({
            name: layoutName,
            animate: true,
            animationDuration: 450,
            fit: true,
            padding: 70,
            randomize: false
        }).run();
        updateStats();
    };

    const addGraphNode = (id) => {
        const cleanId = normalizeInput(id);
        if (!cleanId || !cy.getElementById(cleanId).empty()) {
            return false;
        }

        cy.add({
            group: 'nodes',
            data: { id: cleanId, label: labelFromValue(cleanId) }
        });
        updateStats();
        return true;
    };

    const addGraphEdge = (source, target) => {
        const cleanSource = normalizeInput(source);
        const cleanTarget = normalizeInput(target);
        if (!cleanSource || !cleanTarget) {
            return false;
        }

        addGraphNode(cleanSource);
        addGraphNode(cleanTarget);

        const edgeId = `${cleanSource}->${cleanTarget}`;
        if (!cy.getElementById(edgeId).empty()) {
            return false;
        }

        cy.add({
            group: 'edges',
            data: { id: edgeId, source: cleanSource, target: cleanTarget }
        });
        updateStats();
        return true;
    };

    const clearScores = () => {
        lastComputedScores = null;
        cy.nodes().removeClass('top-ranked');
        cy.edges().removeClass('top-inbound');
        cy.nodes().forEach((node) => {
            node.style({
                'width': 48,
                'height': 48,
                'font-size': 11,
                'background-color': '#3c3833'
            });
        });
        cy.edges().forEach((edge) => {
            edge.style({
                'line-color': '#8c877c',
                'target-arrow-color': '#8c877c',
                'width': 2.2
            });
        });
        updateStats();
    };

    addNodeBtn.addEventListener('click', () => {
        const id = normalizeInput(nodeInput.value);
        if (addGraphNode(id)) {
            nodeInput.value = '';
            clearScores();
            applyLayout();
        } else {
            showToast(id ? 'Page already exists in graph.' : 'Enter a page name or URL.', id ? 'warning' : 'error');
        }
    });

    nodeInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            addNodeBtn.click();
        }
    });

    addLinkBtn.addEventListener('click', () => {
        const source = normalizeInput(sourceInput.value);
        const target = normalizeInput(targetInput.value);

        if (!source || !target) {
            showToast('Enter both source and target pages.', 'error');
            return;
        }

        if (addGraphEdge(source, target)) {
            sourceInput.value = '';
            targetInput.value = '';
            clearScores();
            applyLayout();
        } else {
            showToast('That directed link already exists.', 'warning');
        }
    });

    [sourceInput, targetInput].forEach((input) => {
        input.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                addLinkBtn.click();
            }
        });
    });

    loadSampleBtn.addEventListener('click', () => {
        cy.elements().remove();
        closeNodeDrawer();
        ['Home', 'Docs', 'Pricing', 'Blog', 'Support', 'Changelog'].forEach(addGraphNode);
        [
            ['Home', 'Docs'],
            ['Home', 'Pricing'],
            ['Home', 'Blog'],
            ['Docs', 'Support'],
            ['Blog', 'Docs'],
            ['Pricing', 'Home'],
            ['Support', 'Docs'],
            ['Changelog', 'Docs'],
            ['Blog', 'Changelog']
        ].forEach(([source, target]) => addGraphEdge(source, target));
        resultsSection.classList.add('hidden');
        crawlSummary.classList.add('hidden');
        clearScores();
        applyLayout();
    });

    clearBtn.addEventListener('click', () => {
        cy.elements().remove();
        closeNodeDrawer();
        rankingList.innerHTML = '';
        resultsSection.classList.add('hidden');
        crawlSummary.classList.add('hidden');
        updateStats();
    });

    relayoutBtn.addEventListener('click', applyLayout);

    fitBtn.addEventListener('click', () => {
        cy.fit(undefined, 70);
        cy.center();
    });

    crawlBtn.addEventListener('click', async () => {
        const url = normalizeInput(crawlUrl.value);
        const maxPages = Number(crawlLimit.value) || 8;

        if (!url) {
            showToast('Enter a website URL first.', 'error');
            return;
        }

        resultsSection.classList.remove('hidden');
        loadingText.textContent = 'Crawling...';
        loadingText.classList.remove('hidden');
        rankingList.innerHTML = '';
        crawlSummary.classList.add('hidden');
        crawlBtn.disabled = true;

        try {
            const response = await fetch(`${API_BASE_URL}/crawl`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url, max_pages: maxPages })
            });

            const data = await response.json();
            if (!response.ok || data.error) {
                throw new Error(data.error || 'Failed to crawl website.');
            }

            cy.elements().remove();
            closeNodeDrawer();
            data.pages.forEach(addGraphNode);
            data.links.forEach(([source, target]) => addGraphEdge(source, target));
            applyLayout();
            lastComputedScores = data.scores;
            displayResults(data.scores);
            animateGraph(data.scores);

            const pagesCrawled = data.metadata ? data.metadata.pages_crawled : data.pages.length;
            const pagesFailed = data.metadata ? data.metadata.pages_failed : 0;
            crawlSummary.textContent = `Crawl Summary: Indexed ${data.pages.length} pages (${pagesCrawled} ok, ${pagesFailed} failed) & ${data.links.length} directed links.`;
            crawlSummary.classList.remove('hidden');
            showToast(`Crawl completed: ${data.pages.length} pages indexed.`, 'success');
        } catch (error) {
            showToast(error.message, 'error');
            resultsSection.classList.add('hidden');
        } finally {
            loadingText.textContent = 'Working...';
            loadingText.classList.add('hidden');
            crawlBtn.disabled = false;
        }
    });

    calculateBtn.addEventListener('click', async () => {
        const nodes = cy.nodes().map((node) => node.id());
        const edges = cy.edges().map((edge) => [edge.data('source'), edge.data('target')]);

        if (nodes.length === 0) {
            showToast('Add pages and directed links first.', 'error');
            return;
        }

        resultsSection.classList.remove('hidden');
        crawlSummary.classList.add('hidden');
        loadingText.textContent = 'Calculating...';
        loadingText.classList.remove('hidden');
        rankingList.innerHTML = '';
        calculateBtn.disabled = true;

        try {
            const response = await fetch(`${API_BASE_URL}/calculate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pages: nodes, links: edges })
            });

            const data = await response.json();
            if (!response.ok || data.error) {
                throw new Error(data.error || `Server returned ${response.status}`);
            }

            lastComputedScores = data;
            displayResults(data);
            animateGraph(data);
            if (activeSelectedNode) {
                openNodeDrawer(activeSelectedNode);
            }
        } catch (error) {
            showToast(error.message, 'error');
            resultsSection.classList.add('hidden');
        } finally {
            loadingText.classList.add('hidden');
            calculateBtn.disabled = false;
        }
    });

    function displayResults(scores) {
        rankingList.innerHTML = '';

        Object.entries(scores).forEach(([nodeId, score], index) => {
            const li = document.createElement('li');
            const rank = document.createElement('span');
            const name = document.createElement('span');
            const value = document.createElement('span');

            li.className = 'ranking-item';
            li.style.animationDelay = `${index * 0.045}s`;

            rank.className = 'rank';
            rank.textContent = `#${index + 1}`;

            name.className = 'node-name';
            name.title = nodeId;
            name.textContent = labelFromValue(nodeId);

            value.className = 'score';
            value.textContent = score.toFixed(4);

            li.append(rank, name, value);
            rankingList.appendChild(li);
        });
    }

    function animateGraph(scores) {
        const values = Object.values(scores);
        const maxScore = Math.max(...values);
        const topNodeId = Object.entries(scores).sort((a, b) => b[1] - a[1])[0]?.[0];

        cy.nodes().removeClass('top-ranked');
        cy.edges().removeClass('top-inbound');

        cy.nodes().forEach((node) => {
            const score = scores[node.id()] || 0;
            const ratio = maxScore ? score / maxScore : 0;
            const size = 42 + ratio * 54;

            node.style({
                'width': size,
                'height': size,
                'font-size': 10 + ratio * 4,
                'background-color': node.id() === topNodeId ? '#b38234' : '#3c3833'
            });

            if (node.id() === topNodeId) {
                node.addClass('top-ranked');
            }
        });

        cy.edges().forEach((edge) => {
            if (edge.target().id() === topNodeId) {
                edge.addClass('top-inbound');
            }
        });

        updateStats(scores);
    }

    // ==========================================================================
    // Step 5: PageRank Inspector — Detailed Convergence & Rank Breakdown
    // ==========================================================================
    const runInspectorBtn = document.getElementById('run-inspector-btn');
    const inspDamping = document.getElementById('insp-damping');
    const inspTol = document.getElementById('insp-tol');
    const inspMaxIter = document.getElementById('insp-max-iter');
    const inspMetricIter = document.getElementById('insp-metric-iter');
    const inspMetricStatus = document.getElementById('insp-metric-status');
    const inspMetricError = document.getElementById('insp-metric-error');
    const inspMetricMass = document.getElementById('insp-metric-mass');
    const inspectorTbody = document.getElementById('inspector-tbody');

    if (runInspectorBtn) {
        runInspectorBtn.addEventListener('click', async () => {
            // Pull graph state from Cytoscape (shared state)
            const nodes = cy.nodes().map((node) => node.id());
            const edges = cy.edges().map((edge) => [edge.data('source'), edge.data('target')]);

            if (nodes.length === 0) {
                showToast('Load a graph in the Explorer tab first, then run the Inspector.', 'error');
                return;
            }

            const dampingVal = parseFloat(inspDamping ? inspDamping.value : 0.85);
            const tolVal = parseFloat(inspTol ? inspTol.value : 1e-6);
            const maxIterVal = parseInt(inspMaxIter ? inspMaxIter.value : 100, 10);

            if (isNaN(dampingVal) || dampingVal <= 0 || dampingVal >= 1) {
                showToast('Damping factor must be strictly between 0 and 1.', 'error');
                return;
            }
            if (isNaN(maxIterVal) || maxIterVal < 1) {
                showToast('Max iterations must be an integer ≥ 1.', 'error');
                return;
            }

            runInspectorBtn.disabled = true;
            runInspectorBtn.textContent = 'Computing...';

            try {
                const response = await fetch(`${API_BASE_URL}/calculate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        pages: nodes,
                        links: edges,
                        damping: dampingVal,
                        tol: tolVal,
                        max_iterations: maxIterVal,
                        detailed: true
                    })
                });

                const data = await response.json();
                if (!response.ok || data.error) {
                    throw new Error(data.error || `Server returned ${response.status}`);
                }

                const { ranking, iterations, converged, final_error } = data;
                const rankEntries = Object.entries(ranking).sort((a, b) => b[1] - a[1]);

                // Compute total rank mass (should equal 1.0 for conservation verification)
                const totalMass = rankEntries.reduce((sum, [, score]) => sum + score, 0);

                // Update metric summary cards
                if (inspMetricIter) inspMetricIter.textContent = iterations;
                if (inspMetricStatus) {
                    inspMetricStatus.textContent = converged ? 'Converged' : 'Max Iters';
                    inspMetricStatus.style.color = converged ? '#3c5e44' : '#9a3a3a';
                }
                if (inspMetricError) inspMetricError.textContent = final_error.toExponential(4);
                if (inspMetricMass) {
                    inspMetricMass.textContent = totalMass.toFixed(8);
                    inspMetricMass.style.color = Math.abs(totalMass - 1.0) < 1e-6 ? '#3c5e44' : '#9a3a3a';
                }

                // Build breakdown table rows safely using DOM methods
                if (inspectorTbody) {
                    inspectorTbody.innerHTML = '';

                    rankEntries.forEach(([nodeId, score], index) => {
                        const cyNode = cy.getElementById(nodeId);
                        const outDegree = cyNode.length ? cyNode.outgoers('edge').length : '—';
                        const inboundCount = cyNode.length ? cyNode.incomers('edge').length : '—';
                        const isDangling = cyNode.length && cyNode.outgoers('edge').length === 0;

                        const tr = document.createElement('tr');

                        // Rank number
                        const tdRank = document.createElement('td');
                        tdRank.textContent = `#${index + 1}`;
                        tdRank.style.fontWeight = '600';

                        // Node ID
                        const tdNode = document.createElement('td');
                        tdNode.title = nodeId;
                        tdNode.textContent = labelFromValue(nodeId);

                        // Score
                        const tdScore = document.createElement('td');
                        tdScore.textContent = score.toFixed(6);
                        if (index === 0) {
                            tdScore.style.color = '#b38234';
                            tdScore.style.fontWeight = '700';
                        }

                        // Out-degree
                        const tdOut = document.createElement('td');
                        tdOut.textContent = outDegree;

                        // Node type badge
                        const tdType = document.createElement('td');
                        const badge = document.createElement('span');
                        badge.className = isDangling ? 'badge-dangling' : 'badge-standard';
                        badge.textContent = isDangling ? 'Dangling' : 'Standard';
                        tdType.appendChild(badge);

                        // Inbound count
                        const tdIn = document.createElement('td');
                        tdIn.textContent = inboundCount;

                        tr.append(tdRank, tdNode, tdScore, tdOut, tdType, tdIn);
                        inspectorTbody.appendChild(tr);
                    });
                }

                showToast(`Inspector: ${rankEntries.length} nodes computed, ${iterations} iterations.`, 'success');

            } catch (error) {
                showToast(error.message, 'error');
            } finally {
                runInspectorBtn.disabled = false;
                runInspectorBtn.textContent = 'Run Inspector';
            }
        });
    }

    // ==========================================================================
    // Step 6: Structural Graph Analysis Interface
    // ==========================================================================
    const runAnalysisBtn = document.getElementById('run-analysis-btn');
    const anaNodeCount = document.getElementById('ana-node-count');
    const anaEdgeCount = document.getElementById('ana-edge-count');
    const anaDensity = document.getElementById('ana-density');
    const anaWccCount = document.getElementById('ana-wcc-count');
    const anaSccCount = document.getElementById('ana-scc-count');
    const anaDanglingIsolated = document.getElementById('ana-dangling-isolated');
    const anaWccContainer = document.getElementById('ana-wcc-container');
    const anaSccContainer = document.getElementById('ana-scc-container');
    const analysisTbody = document.getElementById('analysis-tbody');

    if (runAnalysisBtn) {
        runAnalysisBtn.addEventListener('click', async () => {
            const nodes = cy.nodes().map((node) => node.id());
            const edges = cy.edges().map((edge) => [edge.data('source'), edge.data('target')]);

            if (nodes.length === 0) {
                showToast('Load a graph in the Explorer tab first, then run Structural Analysis.', 'error');
                return;
            }

            runAnalysisBtn.disabled = true;
            runAnalysisBtn.textContent = 'Analyzing...';

            try {
                const response = await fetch(`${API_BASE_URL}/analyze`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ pages: nodes, links: edges })
                });

                const data = await response.json();
                if (!response.ok || data.error) {
                    throw new Error(data.error || `Server returned ${response.status}`);
                }

                const {
                    node_count,
                    edge_count,
                    density,
                    in_degree,
                    out_degree,
                    dangling_node_count,
                    isolated_node_count,
                    weakly_connected_components,
                    strongly_connected_components
                } = data;

                // Update Metric Cards
                if (anaNodeCount) anaNodeCount.textContent = node_count;
                if (anaEdgeCount) anaEdgeCount.textContent = edge_count;
                if (anaDensity) anaDensity.textContent = density.toFixed(4);
                if (anaWccCount) anaWccCount.textContent = weakly_connected_components.length;
                if (anaSccCount) anaSccCount.textContent = strongly_connected_components.length;
                if (anaDanglingIsolated) {
                    anaDanglingIsolated.textContent = `${dangling_node_count} / ${isolated_node_count}`;
                }

                // Render WCC Container
                if (anaWccContainer) {
                    anaWccContainer.innerHTML = '';
                    if (weakly_connected_components.length === 0) {
                        anaWccContainer.innerHTML = '<p class="empty-text">No components found.</p>';
                    } else {
                        weakly_connected_components.forEach((comp, idx) => {
                            const row = document.createElement('div');
                            row.className = 'component-row';

                            const label = document.createElement('span');
                            label.className = 'component-label';
                            label.textContent = `WCC #${idx + 1} (${comp.length}):`;

                            const members = document.createElement('span');
                            members.className = 'component-members';
                            members.textContent = comp.map(labelFromValue).join(', ');

                            row.append(label, members);
                            anaWccContainer.appendChild(row);
                        });
                    }
                }

                // Render SCC Container
                if (anaSccContainer) {
                    anaSccContainer.innerHTML = '';
                    if (strongly_connected_components.length === 0) {
                        anaSccContainer.innerHTML = '<p class="empty-text">No components found.</p>';
                    } else {
                        strongly_connected_components.forEach((comp, idx) => {
                            const row = document.createElement('div');
                            row.className = 'component-row';

                            const label = document.createElement('span');
                            label.className = 'component-label';
                            label.textContent = `SCC #${idx + 1} (${comp.length}):`;

                            const members = document.createElement('span');
                            members.className = 'component-members';
                            members.textContent = comp.map(labelFromValue).join(', ');

                            row.append(label, members);
                            anaSccContainer.appendChild(row);
                        });
                    }
                }

                // Render Node Degrees Table
                if (analysisTbody) {
                    analysisTbody.innerHTML = '';

                    // Sort nodes alphabetically for clear tabular viewing
                    const sortedNodes = [...nodes].sort();

                    sortedNodes.forEach((nodeId) => {
                        const inDeg = in_degree[nodeId] || 0;
                        const outDeg = out_degree[nodeId] || 0;

                        let classification = 'Standard';
                        let badgeClass = 'badge-standard';

                        if (inDeg === 0 && outDeg === 0) {
                            classification = 'Isolated';
                            badgeClass = 'badge-isolated';
                        } else if (outDeg === 0) {
                            classification = 'Dangling';
                            badgeClass = 'badge-dangling';
                        }

                        const tr = document.createElement('tr');

                        const tdNode = document.createElement('td');
                        tdNode.title = nodeId;
                        tdNode.textContent = labelFromValue(nodeId);

                        const tdIn = document.createElement('td');
                        tdIn.textContent = inDeg;

                        const tdOut = document.createElement('td');
                        tdOut.textContent = outDeg;

                        const tdClass = document.createElement('td');
                        const badge = document.createElement('span');
                        badge.className = badgeClass;
                        badge.textContent = classification;
                        tdClass.appendChild(badge);

                        tr.append(tdNode, tdIn, tdOut, tdClass);
                        analysisTbody.appendChild(tr);
                    });
                }

                showToast(`Analysis complete: ${node_count} nodes, ${weakly_connected_components.length} WCC, ${strongly_connected_components.length} SCC.`, 'success');

            } catch (error) {
                showToast(error.message, 'error');
            } finally {
                runAnalysisBtn.disabled = false;
                runAnalysisBtn.textContent = 'Run Structural Analysis';
            }
        });
    }

    // ==========================================================================
    // Step 8: Ranking Comparison Studio
    // ==========================================================================
    const runCompareBtn = document.getElementById('run-compare-btn');
    const loadPresetCompareBtn = document.getElementById('load-preset-compare-btn');
    const compVectorAInput = document.getElementById('comp-vector-a');
    const compVectorBInput = document.getElementById('comp-vector-b');
    const compMetricL1 = document.getElementById('comp-metric-l1');
    const compMetricL2 = document.getElementById('comp-metric-l2');
    const compMetricCosine = document.getElementById('comp-metric-cosine');
    const compMetricSpearman = document.getElementById('comp-metric-spearman');
    const compMetricKendall = document.getElementById('comp-metric-kendall');
    const compMetricDisp = document.getElementById('comp-metric-disp');
    const compTopkContainer = document.getElementById('comp-topk-container');
    const comparisonTbody = document.getElementById('comparison-tbody');

    if (loadPresetCompareBtn) {
        loadPresetCompareBtn.addEventListener('click', async () => {
            const nodes = cy.nodes().map((node) => node.id());
            const edges = cy.edges().map((edge) => [edge.data('source'), edge.data('target')]);

            if (nodes.length === 0) {
                // Populate sample vectors if graph is empty
                if (compVectorAInput) compVectorAInput.value = JSON.stringify({ Home: 0.45, Docs: 0.30, Blog: 0.25 }, null, 2);
                if (compVectorBInput) compVectorBInput.value = JSON.stringify({ Home: 0.33, Docs: 0.42, Blog: 0.25 }, null, 2);
                showToast('Sample preset ranking vectors loaded.', 'info');
                return;
            }

            loadPresetCompareBtn.disabled = true;
            loadPresetCompareBtn.textContent = 'Computing Presets...';

            try {
                // Vector A: Standard d = 0.85
                const resA = await fetch(`${API_BASE_URL}/calculate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ pages: nodes, links: edges, damping: 0.85 })
                });
                const dataA = await resA.json();

                // Vector B: Low damping d = 0.50
                const resB = await fetch(`${API_BASE_URL}/calculate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ pages: nodes, links: edges, damping: 0.50 })
                });
                const dataB = await resB.json();

                if (compVectorAInput) compVectorAInput.value = JSON.stringify(dataA, null, 2);
                if (compVectorBInput) compVectorBInput.value = JSON.stringify(dataB, null, 2);

                showToast('Loaded current graph rankings (d=0.85 vs d=0.50). Click "Compare Vectors".', 'success');

            } catch (error) {
                showToast(error.message, 'error');
            } finally {
                loadPresetCompareBtn.disabled = false;
                loadPresetCompareBtn.textContent = 'Load Graph (d=0.85 vs d=0.50)';
            }
        });
    }

    if (runCompareBtn) {
        runCompareBtn.addEventListener('click', async () => {
            if (!compVectorAInput || !compVectorBInput) return;

            let rankingA, rankingB;
            try {
                rankingA = JSON.parse(compVectorAInput.value.trim() || '{}');
            } catch {
                showToast('Invalid JSON syntax in Ranking Vector A.', 'error');
                return;
            }

            try {
                rankingB = JSON.parse(compVectorBInput.value.trim() || '{}');
            } catch {
                showToast('Invalid JSON syntax in Ranking Vector B.', 'error');
                return;
            }

            if (Object.keys(rankingA).length === 0 || Object.keys(rankingB).length === 0) {
                showToast('Ranking vectors A and B cannot be empty.', 'error');
                return;
            }

            runCompareBtn.disabled = true;
            runCompareBtn.textContent = 'Comparing...';

            try {
                const response = await fetch(`${API_BASE_URL}/compare`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ranking_a: rankingA, ranking_b: rankingB })
                });

                const data = await response.json();
                if (!response.ok || data.error) {
                    throw new Error(data.error || `Server returned ${response.status}`);
                }

                const {
                    l1_distance,
                    l2_distance,
                    cosine_similarity,
                    spearman_correlation,
                    kendall_tau,
                    top_k_overlap,
                    max_rank_displacement,
                    mean_rank_displacement,
                    rank_displacements
                } = data;

                // Update Metric Summary Cards
                if (compMetricL1) compMetricL1.textContent = l1_distance.toFixed(6);
                if (compMetricL2) compMetricL2.textContent = l2_distance.toFixed(6);
                if (compMetricCosine) compMetricCosine.textContent = cosine_similarity.toFixed(6);
                if (compMetricSpearman) compMetricSpearman.textContent = spearman_correlation.toFixed(4);
                if (compMetricKendall) compMetricKendall.textContent = kendall_tau.toFixed(4);
                if (compMetricDisp) {
                    compMetricDisp.textContent = `${max_rank_displacement} / ${mean_rank_displacement.toFixed(2)}`;
                }

                // Render Top-K Overlap Container
                if (compTopkContainer) {
                    compTopkContainer.innerHTML = '';
                    const entries = Object.entries(top_k_overlap);
                    if (entries.length === 0) {
                        compTopkContainer.innerHTML = '<p class="empty-text">No overlap metrics computed.</p>';
                    } else {
                        entries.forEach(([k, ratio]) => {
                            const card = document.createElement('div');
                            card.className = 'topk-card-item';

                            const kLabel = document.createElement('span');
                            kLabel.className = 'topk-k-label';
                            kLabel.textContent = `Top-${k} Overlap`;

                            const ratioVal = document.createElement('span');
                            ratioVal.className = 'topk-ratio-val';
                            ratioVal.textContent = `${(ratio * 100).toFixed(1)}%`;

                            card.append(kLabel, ratioVal);
                            compTopkContainer.appendChild(card);
                        });
                    }
                }

                // Render Per-Node Shift Breakdown Table
                if (comparisonTbody) {
                    comparisonTbody.innerHTML = '';

                    const commonNodes = Object.keys(rankingA).sort();

                    commonNodes.forEach((nodeId) => {
                        const scoreA = rankingA[nodeId] !== undefined ? rankingA[nodeId] : 0;
                        const scoreB = rankingB[nodeId] !== undefined ? rankingB[nodeId] : 0;
                        const scoreDelta = Math.abs(scoreA - scoreB);
                        const rankShift = rank_displacements[nodeId] !== undefined ? rank_displacements[nodeId] : 0;

                        const tr = document.createElement('tr');

                        const tdNode = document.createElement('td');
                        tdNode.title = nodeId;
                        tdNode.textContent = labelFromValue(nodeId);

                        const tdScoreA = document.createElement('td');
                        tdScoreA.textContent = scoreA.toFixed(6);

                        const tdScoreB = document.createElement('td');
                        tdScoreB.textContent = scoreB.toFixed(6);

                        const tdDelta = document.createElement('td');
                        tdDelta.textContent = scoreDelta.toFixed(6);

                        const tdShift = document.createElement('td');
                        tdShift.textContent = `|Δr| = ${rankShift}`;
                        if (rankShift > 0) {
                            tdShift.style.color = '#b38234';
                            tdShift.style.fontWeight = '600';
                        }

                        tr.append(tdNode, tdScoreA, tdScoreB, tdDelta, tdShift);
                        comparisonTbody.appendChild(tr);
                    });
                }

                showToast(`Comparison complete: Cosine=${cosine_similarity.toFixed(4)}, Spearman=${spearman_correlation.toFixed(4)}.`, 'success');

            } catch (error) {
                showToast(error.message, 'error');
            } finally {
                runCompareBtn.disabled = false;
                runCompareBtn.textContent = 'Compare Vectors';
            }
        });
    }

    // ==========================================================================
    // Step 9: Experiment Lab & Research Suite
    // ==========================================================================
    const datasetCatalog = {
        A: {
            id: 'chain-4',
            name: 'Dataset A (Chain-4)',
            pages: ['A', 'B', 'C', 'D'],
            links: [['A', 'B'], ['B', 'C'], ['C', 'D']]
        },
        B: {
            id: 'cycle-3',
            name: 'Dataset B (Cycle-3)',
            pages: ['A', 'B', 'C'],
            links: [['A', 'B'], ['B', 'C'], ['C', 'A']]
        },
        C: {
            id: 'dangling-3',
            name: 'Dataset C (Dangling-3)',
            pages: ['A', 'B', 'C'],
            links: [['A', 'B'], ['B', 'C']]
        },
        D: {
            id: 'disconnected-5',
            name: 'Dataset D (Disconnected-5)',
            pages: ['A', 'B', 'C', 'D', 'E'],
            links: [['A', 'B'], ['B', 'A'], ['C', 'D']]
        },
        E: {
            id: 'hub-4',
            name: 'Dataset E (Hub-4)',
            pages: ['Hub', 'Node1', 'Node2', 'Node3'],
            links: [['Node1', 'Hub'], ['Node2', 'Hub'], ['Node3', 'Hub']]
        },
        F: {
            id: 'star-4',
            name: 'Dataset F (Star-4)',
            pages: ['Center', 'Leaf1', 'Leaf2', 'Leaf3'],
            links: [['Center', 'Leaf1'], ['Center', 'Leaf2'], ['Center', 'Leaf3']]
        },
        G: {
            id: 'mixed-7',
            name: 'Dataset G (Mixed-7)',
            pages: ['A', 'B', 'C', 'Dang', 'Iso', 'X', 'Y'],
            links: [['A', 'B'], ['B', 'C'], ['C', 'A'], ['C', 'Dang'], ['X', 'Y']]
        }
    };

    let activeDatasetKey = 'A';
    let lastExperimentResultJSON = null;

    const datasetBtns = document.querySelectorAll('.btn-dataset');
    const runSweepBtn = document.getElementById('run-sweep-btn');
    const exportJsonBtn = document.getElementById('export-json-btn');
    const labMetricDataset = document.getElementById('lab-metric-dataset');
    const labMetricIter = document.getElementById('lab-metric-iter');
    const labMetricError = document.getElementById('lab-metric-error');
    const labMetricMass = document.getElementById('lab-metric-mass');
    const labSweepTbody = document.getElementById('lab-sweep-tbody');
    const labJsonOutput = document.getElementById('lab-json-output');

    const loadDatasetOntoCanvas = (datasetKey) => {
        const ds = datasetCatalog[datasetKey];
        if (!ds) return;

        cy.elements().remove();
        closeNodeDrawer();
        ds.pages.forEach(addGraphNode);
        ds.links.forEach(([src, tgt]) => addGraphEdge(src, tgt));
        clearScores();
        applyLayout();
    };

    datasetBtns.forEach((btn) => {
        btn.addEventListener('click', () => {
            datasetBtns.forEach((b) => b.classList.remove('active'));
            btn.classList.add('active');

            activeDatasetKey = btn.getAttribute('data-dataset') || 'A';
            const ds = datasetCatalog[activeDatasetKey];

            if (labMetricDataset) labMetricDataset.textContent = ds.name;
            loadDatasetOntoCanvas(activeDatasetKey);
            showToast(`Loaded ${ds.name} onto canvas. Click "Run Parameter Sweep".`, 'info');
        });
    });

    if (runSweepBtn) {
        runSweepBtn.addEventListener('click', async () => {
            const ds = datasetCatalog[activeDatasetKey] || datasetCatalog.A;
            const dampings = [0.15, 0.30, 0.50, 0.70, 0.85, 0.95];

            runSweepBtn.disabled = true;
            runSweepBtn.textContent = 'Running Sweep...';

            const sweepResults = [];
            let baseline85Result = null;

            try {
                for (const d of dampings) {
                    const response = await fetch(`${API_BASE_URL}/calculate`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            pages: ds.pages,
                            links: ds.links,
                            damping: d,
                            tol: 1e-6,
                            max_iterations: 100,
                            detailed: true
                        })
                    });

                    const data = await response.json();
                    if (!response.ok || data.error) {
                        throw new Error(data.error || `Failed calculation at d=${d}`);
                    }

                    const topNode = Object.entries(data.ranking).sort((a, b) => b[1] - a[1])[0]?.[0] || 'None';
                    const massSum = Object.values(data.ranking).reduce((sum, v) => sum + v, 0);

                    const resObj = {
                        damping: d,
                        iterations: data.iterations,
                        converged: data.converged,
                        final_error: data.final_error,
                        top_authority: topNode,
                        rank_mass_sum: massSum,
                        ranking: data.ranking
                    };

                    sweepResults.push(resObj);
                    if (d === 0.85) baseline85Result = resObj;
                }

                // Update Metric Summary Cards
                if (baseline85Result) {
                    if (labMetricIter) labMetricIter.textContent = baseline85Result.iterations;
                    if (labMetricError) labMetricError.textContent = baseline85Result.final_error.toExponential(4);
                    if (labMetricMass) labMetricMass.textContent = baseline85Result.rank_mass_sum.toFixed(8);
                }

                // Render Parameter Sweep Table
                if (labSweepTbody) {
                    labSweepTbody.innerHTML = '';
                    sweepResults.forEach((res) => {
                        const tr = document.createElement('tr');

                        const tdD = document.createElement('td');
                        tdD.textContent = res.damping.toFixed(2);
                        tdD.style.fontWeight = '600';

                        const tdIter = document.createElement('td');
                        tdIter.textContent = res.iterations;

                        const tdStatus = document.createElement('td');
                        const badge = document.createElement('span');
                        badge.className = res.converged ? 'badge-standard' : 'badge-dangling';
                        badge.textContent = res.converged ? 'Converged' : 'Max Iterations';
                        tdStatus.appendChild(badge);

                        const tdErr = document.createElement('td');
                        tdErr.textContent = res.final_error.toExponential(4);

                        const tdTop = document.createElement('td');
                        tdTop.textContent = labelFromValue(res.top_authority);
                        tdTop.title = res.top_authority;

                        tr.append(tdD, tdIter, tdStatus, tdErr, tdTop);
                        labSweepTbody.appendChild(tr);
                    });
                }

                // Construct Reproducible Experiment JSON Trace
                const expArtifact = {
                    experiment_id: `exp-${ds.id}-${Date.now()}`,
                    dataset_id: ds.id,
                    dataset_name: ds.name,
                    node_count: ds.pages.length,
                    edge_count: ds.links.length,
                    pages: ds.pages,
                    links: ds.links,
                    damping_sweep: sweepResults
                };

                lastExperimentResultJSON = expArtifact;
                if (labJsonOutput) {
                    labJsonOutput.textContent = JSON.stringify(expArtifact, null, 2);
                }

                showToast(`Parameter sweep complete across ${dampings.length} damping values!`, 'success');

            } catch (error) {
                showToast(error.message, 'error');
            } finally {
                runSweepBtn.disabled = false;
                runSweepBtn.textContent = 'Run Parameter Sweep';
            }
        });
    }

    if (exportJsonBtn) {
        exportJsonBtn.addEventListener('click', () => {
            if (!lastExperimentResultJSON) {
                showToast('Run a parameter sweep first to generate JSON results.', 'error');
                return;
            }

            const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(lastExperimentResultJSON, null, 2));
            const dlAnchor = document.createElement('a');
            dlAnchor.setAttribute('href', dataStr);
            dlAnchor.setAttribute('download', `pagerank_${lastExperimentResultJSON.dataset_id}_experiment.json`);
            document.body.appendChild(dlAnchor);
            dlAnchor.click();
            dlAnchor.remove();

            showToast('JSON experiment artifact downloaded successfully.', 'success');
        });
    }

    // Initializations
    updateStats();
    checkBackendHealth();
});



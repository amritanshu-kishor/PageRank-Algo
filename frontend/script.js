document.addEventListener('DOMContentLoaded', () => {
    const cy = cytoscape({
        container: document.getElementById('cy'),
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': '#2454c6',
                    'border-color': '#f6f1e8',
                    'border-width': 2,
                    'color': '#fffaf0',
                    'font-family': 'Inter, sans-serif',
                    'font-size': 11,
                    'font-weight': 800,
                    'height': 48,
                    'label': 'data(label)',
                    'overlay-opacity': 0,
                    'text-background-color': '#171717',
                    'text-background-opacity': 0.72,
                    'text-background-padding': 4,
                    'text-margin-y': 8,
                    'text-max-width': 116,
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
                    'background-color': '#f0a202',
                    'border-color': '#fff2bd',
                    'color': '#ffffff'
                }
            },
            {
                selector: 'edge',
                style: {
                    'arrow-scale': 1.15,
                    'curve-style': 'bezier',
                    'line-color': '#8c7b67',
                    'target-arrow-color': '#8c7b67',
                    'target-arrow-shape': 'triangle',
                    'transition-duration': '0.25s',
                    'transition-property': 'line-color, target-arrow-color, width',
                    'width': 2.2
                }
            },
            {
                selector: 'edge.top-inbound',
                style: {
                    'line-color': '#f0a202',
                    'target-arrow-color': '#f0a202',
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
        const layoutName = cy.nodes().length > 8 ? 'cose' : 'circle';
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
        cy.nodes().removeClass('top-ranked');
        cy.edges().removeClass('top-inbound');
        cy.nodes().forEach((node) => {
            node.style({
                'width': 48,
                'height': 48,
                'font-size': 11,
                'background-color': '#2454c6'
            });
        });
        cy.edges().forEach((edge) => {
            edge.style({
                'line-color': '#8c7b67',
                'target-arrow-color': '#8c7b67',
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
            alert(id ? 'Page already exists.' : 'Enter a page name or URL.');
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
            alert('Enter both source and target pages.');
            return;
        }

        if (addGraphEdge(source, target)) {
            sourceInput.value = '';
            targetInput.value = '';
            clearScores();
            applyLayout();
        } else {
            alert('That directed link already exists.');
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
            alert('Enter a website URL first.');
            return;
        }

        resultsSection.classList.remove('hidden');
        loadingText.textContent = 'Crawling...';
        loadingText.classList.remove('hidden');
        rankingList.innerHTML = '';
        crawlSummary.classList.add('hidden');
        crawlBtn.disabled = true;

        try {
            const response = await fetch('http://127.0.0.1:5000/crawl', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url, max_pages: maxPages })
            });

            const data = await response.json();
            if (!response.ok || data.error) {
                throw new Error(data.error || 'Failed to crawl website.');
            }

            cy.elements().remove();
            data.pages.forEach(addGraphNode);
            data.links.forEach(([source, target]) => addGraphEdge(source, target));
            applyLayout();
            displayResults(data.scores);
            animateGraph(data.scores);

            crawlSummary.textContent = `Found ${data.pages.length} pages and ${data.links.length} links.`;
            crawlSummary.classList.remove('hidden');
        } catch (error) {
            alert(error.message);
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
            alert('Add pages and directed links first.');
            return;
        }

        resultsSection.classList.remove('hidden');
        crawlSummary.classList.add('hidden');
        loadingText.textContent = 'Calculating...';
        loadingText.classList.remove('hidden');
        rankingList.innerHTML = '';
        calculateBtn.disabled = true;

        try {
            const response = await fetch('http://127.0.0.1:5000/calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pages: nodes, links: edges })
            });

            const data = await response.json();
            if (!response.ok || data.error) {
                throw new Error(data.error || `Server returned ${response.status}`);
            }

            displayResults(data);
            animateGraph(data);
        } catch (error) {
            alert(error.message);
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
                'background-color': node.id() === topNodeId ? '#f0a202' : '#2454c6'
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

    updateStats();
});

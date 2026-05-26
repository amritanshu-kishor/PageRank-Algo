document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Cytoscape
    const cy = cytoscape({
        container: document.getElementById('cy'),
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': '#6366f1',
                    'label': 'data(label)',
                    'color': '#ffffff',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'font-size': '14px',
                    'font-family': 'Inter, sans-serif',
                    'font-weight': 'bold',
                    'width': 40,
                    'height': 40,
                    'transition-property': 'width, height, background-color',
                    'transition-duration': '0.5s'
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 3,
                    'line-color': '#64748b',
                    'target-arrow-color': '#64748b',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'arrow-scale': 1.5,
                    'transition-property': 'line-color, target-arrow-color',
                    'transition-duration': '0.5s'
                }
            }
        ],
        layout: {
            name: 'grid'
        },
        userZoomingEnabled: true,
        userPanningEnabled: true,
        boxSelectionEnabled: false
    });

    // Run layout function to nicely organize nodes
    const applyLayout = () => {
        cy.layout({
            name: cy.nodes().length > 12 ? 'cose' : 'circle',
            animate: true,
            animationDuration: 500,
            padding: 50
        }).run();
    };

    const labelFromUrl = (value) => {
        try {
            const url = new URL(value);
            const path = url.pathname === '/' ? '/' : url.pathname.replace(/\/$/, '');
            return `${url.hostname}${path}`.slice(0, 48);
        } catch {
            return value;
        }
    };

    const addGraphNode = (id) => {
        if (cy.getElementById(id).empty()) {
            cy.add({
                group: 'nodes',
                data: { id: id, label: labelFromUrl(id) }
            });
        }
    };

    const addGraphEdge = (source, target) => {
        const edgeId = `${source}->${target}`;
        if (cy.getElementById(edgeId).empty()) {
            cy.add({
                group: 'edges',
                data: { id: edgeId, source: source, target: target }
            });
        }
    };

    // 2. Add Node Logic
    const addNodeBtn = document.getElementById('add-node-btn');
    const nodeInput = document.getElementById('node-name');

    addNodeBtn.addEventListener('click', () => {
        const id = nodeInput.value.trim().toUpperCase();
        if (id && cy.getElementById(id).empty()) {
            addGraphNode(id);
            nodeInput.value = '';
            applyLayout();
        } else {
            alert(id ? "Node already exists!" : "Please enter a valid node name.");
        }
    });

    // 3. Add Link Logic
    const addLinkBtn = document.getElementById('add-link-btn');
    const sourceInput = document.getElementById('link-source');
    const targetInput = document.getElementById('link-target');

    addLinkBtn.addEventListener('click', () => {
        const source = sourceInput.value.trim().toUpperCase();
        const target = targetInput.value.trim().toUpperCase();

        if (source && target) {
            // Check if nodes exist, if not, create them
            addGraphNode(source);
            addGraphNode(target);

            // Check if edge already exists
            const edgeId = `${source}->${target}`;
            if (cy.getElementById(edgeId).empty()) {
                addGraphEdge(source, target);
                sourceInput.value = '';
                targetInput.value = '';
                applyLayout();
            } else {
                alert("Link already exists!");
            }
        } else {
            alert("Please enter both source and target nodes.");
        }
    });

    // 4. Sample Data Logic
    const loadSampleBtn = document.getElementById('load-sample-btn');
    loadSampleBtn.addEventListener('click', () => {
        cy.elements().remove();
        const sampleNodes = [
            { data: { id: 'A', label: 'A' } },
            { data: { id: 'B', label: 'B' } },
            { data: { id: 'C', label: 'C' } },
            { data: { id: 'D', label: 'D' } },
            { data: { id: 'E', label: 'E' } }
        ];
        const sampleEdges = [
            { data: { id: 'A-B', source: 'A', target: 'B' } },
            { data: { id: 'A-C', source: 'A', target: 'C' } },
            { data: { id: 'B-C', source: 'B', target: 'C' } },
            { data: { id: 'C-A', source: 'C', target: 'A' } },
            { data: { id: 'D-C', source: 'D', target: 'C' } },
            { data: { id: 'E-D', source: 'E', target: 'D' } },
            { data: { id: 'B-E', source: 'B', target: 'E' } }
        ];
        cy.add(sampleNodes);
        cy.add(sampleEdges);
        applyLayout();
        document.getElementById('results-section').classList.add('hidden');
    });

    // 5. Clear All Logic
    const clearBtn = document.getElementById('clear-btn');
    clearBtn.addEventListener('click', () => {
        cy.elements().remove();
        document.getElementById('results-section').classList.add('hidden');
    });

    // 6. Calculate PageRank API call
    const calculateBtn = document.getElementById('calculate-btn');
    const resultsSection = document.getElementById('results-section');
    const loadingText = document.getElementById('loading');
    const rankingList = document.getElementById('ranking-list');
    const crawlSummary = document.getElementById('crawl-summary');
    const crawlBtn = document.getElementById('crawl-btn');
    const crawlUrl = document.getElementById('crawl-url');
    const crawlLimit = document.getElementById('crawl-limit');

    crawlBtn.addEventListener('click', async () => {
        const url = crawlUrl.value.trim();
        const maxPages = Number(crawlLimit.value) || 12;

        if (!url) {
            alert("Enter a website URL first.");
            return;
        }

        resultsSection.classList.remove('hidden');
        loadingText.textContent = 'Crawling website...';
        loadingText.classList.remove('hidden');
        rankingList.innerHTML = '';
        crawlSummary.classList.add('hidden');
        crawlBtn.disabled = true;

        try {
            const response = await fetch('http://127.0.0.1:5000/crawl', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
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
            loadingText.textContent = 'Calculating...';
            loadingText.classList.add('hidden');
            crawlBtn.disabled = false;
        }
    });

    calculateBtn.addEventListener('click', async () => {
        const nodes = cy.nodes().map(n => n.id());
        const edges = cy.edges().map(e => [e.data('source'), e.data('target')]);

        if (nodes.length === 0) {
            alert("Graph is empty. Add nodes and links first!");
            return;
        }

        // UI Updates for loading
        resultsSection.classList.remove('hidden');
        crawlSummary.classList.add('hidden');
        loadingText.classList.remove('hidden');
        rankingList.innerHTML = '';

        try {
            const response = await fetch('http://127.0.0.1:5000/calculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ pages: nodes, links: edges })
            });

            if (!response.ok) {
                throw new Error('Failed to compute PageRank. Server returned ' + response.status);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            displayResults(data);
            animateGraph(data);

        } catch (error) {
            alert(error.message);
            resultsSection.classList.add('hidden');
        } finally {
            loadingText.classList.add('hidden');
        }
    });

    // 7. Render Results
    function displayResults(scores) {
        rankingList.innerHTML = '';
        let rank = 1;
        for (const [nodeId, score] of Object.entries(scores)) {
            const li = document.createElement('li');
            li.className = 'ranking-item';
            li.innerHTML = `
                <span class="rank">#${rank}</span>
                <span class="node-name" title="${nodeId}">${labelFromUrl(nodeId)}</span>
                <span class="score">${score.toFixed(4)}</span>
            `;
            // Staggered animation
            li.style.animationDelay = `${rank * 0.1}s`;
            rankingList.appendChild(li);
            rank++;
        }
    }

    // 8. Animate Graph based on scores
    function animateGraph(scores) {
        // Find max score to normalize sizing
        const maxScore = Math.max(...Object.values(scores));
        
        cy.nodes().forEach(node => {
            const score = scores[node.id()] || 0;
            // Base size 40, max extra size 80 based on proportional score
            const size = 40 + (score / maxScore) * 80;
            
            // Highlight color for top node
            const isTop = score === maxScore;
            const bgColor = isTop ? '#10b981' : '#6366f1';

            node.style({
                'width': size,
                'height': size,
                'background-color': bgColor,
                'font-size': 12 + (score / maxScore) * 8
            });
        });

        // Also highlight edges pointing to the top node
        let topNodeId = null;
        for (const [id, score] of Object.entries(scores)) {
            if (score === maxScore) topNodeId = id;
        }

        cy.edges().forEach(edge => {
            if (edge.target().id() === topNodeId) {
                edge.style({
                    'line-color': '#10b981',
                    'target-arrow-color': '#10b981',
                    'width': 4
                });
            } else {
                edge.style({
                    'line-color': '#64748b',
                    'target-arrow-color': '#64748b',
                    'width': 3
                });
            }
        });
    }
});

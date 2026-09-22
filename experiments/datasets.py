"""
Controlled, deterministic experiment datasets for the PageRank research framework.

All datasets are statically defined tuples of (pages, links).
They are independent of any live network resource.

Every dataset is validated against the Step 4 graph contract before use.
Do NOT use live websites as mandatory experiment datasets.

Dataset catalogue
-----------------
DATASET_A  — Simple linear chain           (A→B→C→D)
DATASET_B  — Directed cycle                (A→B→C→A)
DATASET_C  — Dangling graph                (A→B→C, C has no outgoing edges)
DATASET_D  — Disconnected graph            (two components + isolated node)
DATASET_E  — Hub graph                     (one node with many incoming links)
DATASET_F  — Star graph (outward)          (center → all leaves)
DATASET_G  — Mixed graph                   (cycle + dangling + isolated + multi-component)

Scalable dataset generation
---------------------------
generate_chain(n)  — deterministic chain of n nodes
generate_cycle(n)  — deterministic cycle of n nodes
generate_star(n)   — deterministic star: center → n-1 leaf nodes
"""

import sys
from pathlib import Path

# Make backend modules importable when running from the project root.
_backend = Path(__file__).resolve().parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from graph_validator import validate_graph


# ---------------------------------------------------------------------------
# Static Controlled Datasets
# ---------------------------------------------------------------------------

DATASET_A = {
    "dataset_id": "chain-4",
    "description": "Simple linear chain: A→B→C→D",
    "pages": ["A", "B", "C", "D"],
    "links": [["A", "B"], ["B", "C"], ["C", "D"]],
}
"""
A → B → C → D

All nodes in one component. D is a dangling node (no outgoing edges).
A has no incoming edges.
"""

DATASET_B = {
    "dataset_id": "cycle-3",
    "description": "Directed cycle: A→B→C→A",
    "pages": ["A", "B", "C"],
    "links": [["A", "B"], ["B", "C"], ["C", "A"]],
}
"""
A → B → C → A

Perfect cycle: all nodes have in_degree=1 and out_degree=1.
Expected: all PageRank scores equal (by symmetry).
"""

DATASET_C = {
    "dataset_id": "dangling-3",
    "description": "Dangling graph: A→B→C, C has no outgoing edges",
    "pages": ["A", "B", "C"],
    "links": [["A", "B"], ["B", "C"]],
}
"""
A → B → C

C is dangling (no outgoing edges). Tests dangling-node rank redistribution.
A has no incoming edges.
"""

DATASET_D = {
    "dataset_id": "disconnected-5",
    "description": "Disconnected graph: two components (A→B, C→D) plus isolated node E",
    "pages": ["A", "B", "C", "D", "E"],
    "links": [["A", "B"], ["C", "D"]],
}
"""
Component 1: A → B      (B dangling)
Component 2: C → D      (D dangling)
Isolated:    E           (no edges)

Tests disconnected component handling and rank mass conservation.
"""

DATASET_E = {
    "dataset_id": "hub-6",
    "description": "Hub graph: nodes B,C,D,E,F all link to hub node A",
    "pages": ["A", "B", "C", "D", "E", "F"],
    "links": [
        ["B", "A"],
        ["C", "A"],
        ["D", "A"],
        ["E", "A"],
        ["F", "A"],
    ],
}
"""
B → A
C → A
D → A
E → A
F → A

A receives all incoming links; B,C,D,E,F are dangling after pointing to A.
A itself has no outgoing edge — it is also dangling.
Expected: A should accumulate significantly higher PageRank than others.
"""

DATASET_F = {
    "dataset_id": "star-out-5",
    "description": "Outward star: center A links to all leaf nodes B,C,D,E",
    "pages": ["A", "B", "C", "D", "E"],
    "links": [
        ["A", "B"],
        ["A", "C"],
        ["A", "D"],
        ["A", "E"],
    ],
}
"""
A → B
A → C
A → D
A → E

A is the center with out_degree=4. B,C,D,E are all dangling.
A distributes rank equally to all leaves.
"""

DATASET_G = {
    "dataset_id": "mixed-7",
    "description": (
        "Mixed graph: directed cycle (A→B→C→A), dangling node D reachable from C, "
        "isolated node E, second component (F→G)"
    ),
    "pages": ["A", "B", "C", "D", "E", "F", "G"],
    "links": [
        ["A", "B"],
        ["B", "C"],
        ["C", "A"],  # closes cycle A→B→C→A
        ["C", "D"],  # D is dangling
        ["F", "G"],  # second component; G is dangling
        # E is isolated (no edges)
    ],
}
"""
Cycle component:   A → B → C → A   (C also links to D)
Dangling from C:   D
Isolated node:     E
Second component:  F → G  (G dangling)

Tests interplay of cycle, dangling redistribution, isolation, and disconnected components.
"""

# Catalog for programmatic enumeration.
ALL_DATASETS = [
    DATASET_A,
    DATASET_B,
    DATASET_C,
    DATASET_D,
    DATASET_E,
    DATASET_F,
    DATASET_G,
]


# ---------------------------------------------------------------------------
# Dataset Validation
# ---------------------------------------------------------------------------

def load_dataset(dataset):
    """
    Validate and return the pages and links for a dataset definition.

    Applies the Step 4 graph validator. Raises ValueError if the dataset
    is structurally invalid (which would indicate a bug in the dataset
    definition, not in user input).

    :param dataset: dict with 'pages' and 'links' keys (as defined above).
    :return: Tuple (pages: list[str], links: list[list[str]])
    :raises ValueError: If the dataset fails graph validation.
    """
    pages = dataset["pages"]
    links = dataset["links"]
    return validate_graph(pages, links)


# ---------------------------------------------------------------------------
# Deterministic Scalable Dataset Generation
# ---------------------------------------------------------------------------

def generate_chain(n):
    """
    Generate a deterministic linear chain of n nodes.

    Nodes: "N001", "N002", ..., "N{n:03d}"
    Edges: N001→N002, N002→N003, ..., N{n-1}→N{n}

    :param n: Number of nodes (must be >= 1).
    :return: dict with dataset_id, description, pages, links.
    :raises ValueError: If n < 1.
    """
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError(f"n must be a positive integer, got {n!r}")
    pages = [f"N{i:03d}" for i in range(1, n + 1)]
    links = [[pages[i], pages[i + 1]] for i in range(len(pages) - 1)]
    return {
        "dataset_id": f"chain-{n}",
        "description": f"Deterministic linear chain of {n} nodes",
        "pages": pages,
        "links": links,
    }


def generate_cycle(n):
    """
    Generate a deterministic directed cycle of n nodes.

    Nodes: "N001", ..., "N{n:03d}"
    Edges: N001→N002, ..., N{n-1}→N{n}, N{n}→N001

    :param n: Number of nodes (must be >= 2).
    :return: dict with dataset_id, description, pages, links.
    :raises ValueError: If n < 2.
    """
    if not isinstance(n, int) or isinstance(n, bool) or n < 2:
        raise ValueError(f"n must be an integer >= 2 for a cycle, got {n!r}")
    pages = [f"N{i:03d}" for i in range(1, n + 1)]
    links = [[pages[i], pages[(i + 1) % n]] for i in range(n)]
    return {
        "dataset_id": f"cycle-{n}",
        "description": f"Deterministic directed cycle of {n} nodes",
        "pages": pages,
        "links": links,
    }


def generate_star(n):
    """
    Generate a deterministic outward-pointing star with n nodes total.

    Center node: "C001"
    Leaf nodes:  "L001", "L002", ..., "L{n-1:03d}"
    Edges: C001 → each leaf.

    :param n: Total node count including the center (must be >= 2).
    :return: dict with dataset_id, description, pages, links.
    :raises ValueError: If n < 2.
    """
    if not isinstance(n, int) or isinstance(n, bool) or n < 2:
        raise ValueError(f"n must be an integer >= 2 for a star, got {n!r}")
    center = "C001"
    leaves = [f"L{i:03d}" for i in range(1, n)]
    pages = [center] + leaves
    links = [[center, leaf] for leaf in leaves]
    return {
        "dataset_id": f"star-{n}",
        "description": f"Deterministic outward star with 1 center and {n - 1} leaves ({n} nodes total)",
        "pages": pages,
        "links": links,
    }

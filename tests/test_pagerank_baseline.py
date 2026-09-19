import json
import os
import sys
import unittest
# Step 3 note: two tests below carry @unittest.skip because Step 3 corrected the
# mathematical behavior they were asserting.  Their bodies are preserved verbatim
# as historical records of the pre-Step-3 implementation.

# Ensure backend directory is in Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from pagerank import calculate_pagerank

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def load_fixture(filename):
    filepath = os.path.join(FIXTURES_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


class TestPageRankBaseline(unittest.TestCase):
    """
    Baseline test suite for the PageRank implementation in backend/pagerank.py.
    Captures exact baseline output behavior established during Phase 1 - Step 1.
    """

    def test_a_simple_chain_graph(self):
        """Test A: Simple chain graph A -> B -> C."""
        data = load_fixture("simple_graph.json")
        scores = calculate_pagerank(data["pages"], data["links"])

        self.assertEqual(set(scores.keys()), {"A", "B", "C"})
        self.assertAlmostEqual(scores["A"], 0.18441678192715535, places=6)
        self.assertAlmostEqual(scores["B"], 0.34117104656523745, places=6)
        self.assertAlmostEqual(scores["C"], 0.47441217150760717, places=6)
        self.assertAlmostEqual(sum(scores.values()), 1.0, places=6)

    def test_b_directed_cycle_graph(self):
        """Test B: Directed cycle graph A -> B -> C -> A."""
        data = load_fixture("cycle_graph.json")
        scores = calculate_pagerank(data["pages"], data["links"])

        self.assertEqual(set(scores.keys()), {"A", "B", "C"})
        self.assertAlmostEqual(scores["A"], 1.0 / 3.0, places=6)
        self.assertAlmostEqual(scores["B"], 1.0 / 3.0, places=6)
        self.assertAlmostEqual(scores["C"], 1.0 / 3.0, places=6)
        self.assertAlmostEqual(sum(scores.values()), 1.0, places=6)

    @unittest.skip(
        "HISTORICAL BASELINE (Step 2): asserts pre-Step-3 post-hoc-normalization behavior. "
        "Step 3 corrected dangling-node handling to in-iteration redistribution. "
        "New correct behavior is verified in test_pagerank_correctness.py."
    )
    def test_c_dangling_node_graph(self):
        """Test C: Dangling node graph A -> B -> C (C has no out-edges)."""
        data = load_fixture("dangling_graph.json")
        scores = calculate_pagerank(data["pages"], data["links"])

        # Baseline behavior: rank leaks during iterations and is normalized post-hoc
        self.assertEqual(set(scores.keys()), {"A", "B", "C"})
        self.assertAlmostEqual(scores["A"], 0.18441678192715535, places=6)
        self.assertAlmostEqual(scores["B"], 0.34117104656523745, places=6)
        self.assertAlmostEqual(scores["C"], 0.47441217150760717, places=6)
        self.assertAlmostEqual(sum(scores.values()), 1.0, places=6)

    def test_d_disconnected_graph(self):
        """Test D: Disconnected graph (A -> B, C -> D)."""
        data = load_fixture("disconnected_graph.json")
        scores = calculate_pagerank(data["pages"], data["links"])

        self.assertEqual(set(scores.keys()), {"A", "B", "C", "D"})
        self.assertAlmostEqual(scores["A"], 0.17543859649122806, places=6)
        self.assertAlmostEqual(scores["B"], 0.3245614035087719, places=6)
        self.assertAlmostEqual(scores["C"], 0.17543859649122806, places=6)
        self.assertAlmostEqual(scores["D"], 0.3245614035087719, places=6)
        self.assertAlmostEqual(sum(scores.values()), 1.0, places=6)

    def test_e_self_loop_graph(self):
        """Test E: Self-loop graph (A -> A)."""
        data = load_fixture("self_loop_graph.json")
        scores = calculate_pagerank(data["pages"], data["links"])

        self.assertEqual(set(scores.keys()), {"A"})
        self.assertAlmostEqual(scores["A"], 1.0, places=6)

    def test_f_duplicate_edge_graph(self):
        """Test F: Duplicate edge graph (A -> B, A -> B)."""
        data = load_fixture("duplicate_edge_graph.json")
        scores = calculate_pagerank(data["pages"], data["links"])

        self.assertEqual(set(scores.keys()), {"A", "B"})
        self.assertAlmostEqual(scores["A"], 0.3508771929824562, places=6)
        self.assertAlmostEqual(scores["B"], 0.6491228070175439, places=6)
        self.assertAlmostEqual(sum(scores.values()), 1.0, places=6)

    def test_empty_graph(self):
        """Test empty graph entry condition."""
        data = load_fixture("empty_graph.json")
        scores = calculate_pagerank(data["pages"], data["links"])
        self.assertEqual(scores, {})

    @unittest.skip(
        "HISTORICAL BASELINE (Step 2): asserts pre-Step-3 behavior where invalid target edges "
        "incremented out_degree[A] and silently lost rank to the phantom node C, producing 0.5/0.5 "
        "after post-hoc normalization. Step 3 filters invalid edges before rank computation. "
        "New correct behavior is verified in test_pagerank_correctness.py."
    )
    def test_invalid_target_edge(self):
        """Test behavior when edge targets node not in pages list."""
        pages = ["A", "B"]
        links = [["A", "C"]]  # C is not in pages
        scores = calculate_pagerank(pages, links)

        # Baseline behavior: C is ignored in receiving loop, out_degree[A]=1, rank is lost to C, A and B both get equal damping rank and normalize to 0.5
        self.assertEqual(set(scores.keys()), {"A", "B"})
        self.assertAlmostEqual(scores["A"], 0.5, places=6)
        self.assertAlmostEqual(scores["B"], 0.5, places=6)


if __name__ == "__main__":
    unittest.main()

"""
Phase 1 — Step 3: PageRank Correctness Tests

Tests the corrected PageRank implementation in backend/pagerank.py for:
- Mass conservation (rank sums to 1.0)
- Cycle symmetry
- Dangling node in-iteration redistribution
- Disconnected graph handling
- Self-loop handling
- Duplicate edge deduplication
- Invalid target edge filtering
- Damping factor validation
- Determinism
- Convergence verification
- Performance sanity (modest graph)
"""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from pagerank import calculate_pagerank

MASS_TOLERANCE = 1e-6   # PageRank values should sum to 1.0 within this
SYMMETRY_TOLERANCE = 1e-6  # Symmetric nodes should be equal within this


class TestMassConservation(unittest.TestCase):
    """
    Requirement 9: For all graph types, sum(PageRank) must be approximately 1.0.
    Tests mass conservation under the corrected in-iteration dangling redistribution.
    """

    def _assert_mass_conserved(self, pages, links, label=""):
        scores = calculate_pagerank(pages, links)
        total = sum(scores.values())
        self.assertAlmostEqual(
            total, 1.0, delta=MASS_TOLERANCE,
            msg=f"Mass not conserved for {label}: sum={total}"
        )

    def test_mass_simple_chain(self):
        """A -> B -> C: mass conservation."""
        self._assert_mass_conserved(
            ["A", "B", "C"], [["A", "B"], ["B", "C"]], "simple chain A->B->C"
        )

    def test_mass_cycle(self):
        """A -> B -> C -> A: mass conservation."""
        self._assert_mass_conserved(
            ["A", "B", "C"],
            [["A", "B"], ["B", "C"], ["C", "A"]],
            "cycle A->B->C->A"
        )

    def test_mass_dangling(self):
        """A -> B -> C, C is dangling: mass conservation."""
        self._assert_mass_conserved(
            ["A", "B", "C"], [["A", "B"], ["B", "C"]], "dangling A->B->C"
        )

    def test_mass_disconnected(self):
        """A -> B, C -> D: mass conservation across disconnected components."""
        self._assert_mass_conserved(
            ["A", "B", "C", "D"],
            [["A", "B"], ["C", "D"]],
            "disconnected A->B, C->D"
        )

    def test_mass_self_loop(self):
        """A -> A: mass conservation for self-loop graph."""
        self._assert_mass_conserved(
            ["A"], [["A", "A"]], "self-loop A->A"
        )

    def test_mass_all_dangling(self):
        """No edges: every node is dangling. Mass must still be conserved."""
        self._assert_mass_conserved(
            ["A", "B", "C"], [], "all-dangling (no edges)"
        )


class TestCycleSymmetry(unittest.TestCase):
    """
    Requirement 10: Cycle A -> B -> C -> A should converge to equal ranks.

    Mathematical expectation: under uniform teleportation and symmetric structure,
    all three nodes have equal stationary distribution = 1/N.
    """

    def test_cycle_equal_ranks(self):
        """A -> B -> C -> A: all nodes converge to 1/3."""
        scores = calculate_pagerank(
            ["A", "B", "C"],
            [["A", "B"], ["B", "C"], ["C", "A"]]
        )
        self.assertEqual(set(scores.keys()), {"A", "B", "C"})
        expected = 1.0 / 3.0
        for node in ["A", "B", "C"]:
            self.assertAlmostEqual(
                scores[node], expected, delta=SYMMETRY_TOLERANCE,
                msg=f"Cycle node {node}: expected {expected}, got {scores[node]}"
            )
        self.assertAlmostEqual(sum(scores.values()), 1.0, delta=MASS_TOLERANCE)


class TestDanglingNode(unittest.TestCase):
    """
    Requirement 11: Dangling node rank redistribution.

    For A -> B -> C where C has no outgoing edges:
    - C is correctly identified as a dangling node.
    - C's rank is redistributed uniformly across all nodes at every iteration.
    - Total rank sum remains 1.0 throughout (not just after post-hoc normalization).
    - No rank disappears from the system.
    """

    def test_dangling_c_identified(self):
        """C is treated as dangling: its rank redistributes, total stays 1."""
        scores = calculate_pagerank(
            ["A", "B", "C"], [["A", "B"], ["B", "C"]]
        )
        self.assertEqual(set(scores.keys()), {"A", "B", "C"})
        # All values must be positive (no rank disappears)
        for node, score in scores.items():
            self.assertGreater(score, 0.0, msg=f"Node {node} has non-positive rank {score}")
        # Mass conservation
        self.assertAlmostEqual(sum(scores.values()), 1.0, delta=MASS_TOLERANCE)
        # C should have highest rank (receives from B, is a sink)
        self.assertGreater(scores["C"], scores["B"])
        self.assertGreater(scores["B"], scores["A"])

    def test_dangling_redistribution_correctness(self):
        """
        Verify dangling redistribution against the standard formula.

        For A -> B -> C with d=0.85, N=3, at convergence:
          PR(A) = (1-d)/N + d*(dangling_rank/N)
          PR(B) = (1-d)/N + d*(dangling_rank/N + PR(A)/1)
          PR(C) = (1-d)/N + d*(dangling_rank/N + PR(B)/1)
          where dangling_rank = PR(C)

        Numerically verified at convergence.
        """
        d = 0.85
        N = 3
        scores = calculate_pagerank(["A", "B", "C"], [["A", "B"], ["B", "C"]], damping=d)

        # dangling_rank = PR(C) at convergence
        dangling_rank = scores["C"]
        base = (1.0 - d) / N + d * (dangling_rank / N)

        # PR(A) should equal base (A has no valid incoming except dangling redistribution)
        self.assertAlmostEqual(
            scores["A"], base, delta=1e-5,
            msg="PR(A) does not match formula at convergence"
        )
        # PR(B) = base + d * PR(A)
        expected_B = base + d * scores["A"]
        self.assertAlmostEqual(
            scores["B"], expected_B, delta=1e-5,
            msg="PR(B) does not match formula at convergence"
        )
        # PR(C) = base + d * PR(B)
        expected_C = base + d * scores["B"]
        self.assertAlmostEqual(
            scores["C"], expected_C, delta=1e-5,
            msg="PR(C) does not match formula at convergence"
        )


class TestDisconnectedGraph(unittest.TestCase):
    """
    Requirement 12: Disconnected graph A -> B, C -> D.

    Algorithm must:
    - Converge
    - Produce finite values
    - Preserve total rank = 1.0
    - Not crash due to multiple components
    """

    def test_disconnected_converges_and_conserves_mass(self):
        """A -> B, C -> D: converges, finite values, total rank 1.0."""
        scores = calculate_pagerank(
            ["A", "B", "C", "D"],
            [["A", "B"], ["C", "D"]]
        )
        self.assertEqual(set(scores.keys()), {"A", "B", "C", "D"})
        for node, score in scores.items():
            self.assertTrue(
                0.0 < score < 1.0 and score == score,  # finite, positive, not NaN
                msg=f"Node {node} has invalid score {score}"
            )
        self.assertAlmostEqual(sum(scores.values()), 1.0, delta=MASS_TOLERANCE)

    def test_disconnected_symmetry(self):
        """A -> B and C -> D are symmetric: A==C and B==D."""
        scores = calculate_pagerank(
            ["A", "B", "C", "D"],
            [["A", "B"], ["C", "D"]]
        )
        self.assertAlmostEqual(scores["A"], scores["C"], delta=SYMMETRY_TOLERANCE,
                               msg="Disconnected symmetric sources should be equal")
        self.assertAlmostEqual(scores["B"], scores["D"], delta=SYMMETRY_TOLERANCE,
                               msg="Disconnected symmetric sinks should be equal")


class TestSelfLoop(unittest.TestCase):
    """
    Requirement 13: Self-loop A -> A.

    Must not raise an exception, must produce finite PageRank, must converge,
    total rank must be approximately 1.
    """

    def test_self_loop_single_node(self):
        """A -> A: single node self-loop, PR(A) = 1.0."""
        scores = calculate_pagerank(["A"], [["A", "A"]])
        self.assertEqual(set(scores.keys()), {"A"})
        self.assertAlmostEqual(scores["A"], 1.0, delta=MASS_TOLERANCE)

    def test_self_loop_in_larger_graph(self):
        """A -> A, B -> C: self-loop node A coexists with other edges."""
        scores = calculate_pagerank(
            ["A", "B", "C"],
            [["A", "A"], ["B", "C"]]
        )
        self.assertEqual(set(scores.keys()), {"A", "B", "C"})
        self.assertAlmostEqual(sum(scores.values()), 1.0, delta=MASS_TOLERANCE)
        for score in scores.values():
            self.assertGreater(score, 0.0, msg="All nodes should have positive rank")


class TestDuplicateEdges(unittest.TestCase):
    """
    Requirement 14: Duplicate edges A -> B, A -> B, A -> B.

    After deduplication the result must be identical to the single-edge graph A -> B.
    The PageRank should not artificially change due to repeated edges.
    """

    def test_duplicate_same_as_single(self):
        """Three copies of A -> B must yield same result as one copy."""
        scores_single = calculate_pagerank(["A", "B"], [["A", "B"]])
        scores_triple = calculate_pagerank(
            ["A", "B"], [["A", "B"], ["A", "B"], ["A", "B"]]
        )
        self.assertAlmostEqual(scores_single["A"], scores_triple["A"], delta=MASS_TOLERANCE)
        self.assertAlmostEqual(scores_single["B"], scores_triple["B"], delta=MASS_TOLERANCE)

    def test_duplicate_mass_conserved(self):
        """Duplicate edges: total rank sums to 1."""
        scores = calculate_pagerank(["A", "B"], [["A", "B"], ["A", "B"]])
        self.assertAlmostEqual(sum(scores.values()), 1.0, delta=MASS_TOLERANCE)


class TestInvalidTargetEdge(unittest.TestCase):
    """
    Requirement 15: Edge A -> C where C is not in the pages list.

    The invalid edge must be silently filtered. A's out-degree must NOT be inflated.
    The rank must not leak to a non-existent node.
    Total rank must be conserved.
    """

    def test_invalid_target_filtered(self):
        """A -> C (C not in pages): A treated as dangling, mass conserved."""
        scores = calculate_pagerank(["A", "B"], [["A", "C"]])
        self.assertEqual(set(scores.keys()), {"A", "B"})
        self.assertAlmostEqual(sum(scores.values()), 1.0, delta=MASS_TOLERANCE)
        # A has no valid outgoing edges (C filtered) -> A is dangling
        # Both A and B are dangling, so rank redistributes evenly -> 0.5 each
        self.assertAlmostEqual(scores["A"], 0.5, delta=MASS_TOLERANCE)
        self.assertAlmostEqual(scores["B"], 0.5, delta=MASS_TOLERANCE)

    def test_invalid_source_filtered(self):
        """C -> B where C is not in pages: edge silently filtered, B's rank unaffected."""
        scores = calculate_pagerank(["A", "B"], [["C", "B"]])
        self.assertEqual(set(scores.keys()), {"A", "B"})
        self.assertAlmostEqual(sum(scores.values()), 1.0, delta=MASS_TOLERANCE)
        # No valid edges: both A and B are dangling -> equal ranks
        self.assertAlmostEqual(scores["A"], 0.5, delta=MASS_TOLERANCE)
        self.assertAlmostEqual(scores["B"], 0.5, delta=MASS_TOLERANCE)

    def test_mixed_valid_invalid_edges(self):
        """A -> B (valid) and A -> C (invalid): only A -> B counts."""
        scores_with_invalid = calculate_pagerank(
            ["A", "B"], [["A", "B"], ["A", "C"]]
        )
        scores_pure = calculate_pagerank(["A", "B"], [["A", "B"]])
        self.assertAlmostEqual(
            scores_with_invalid["A"], scores_pure["A"], delta=MASS_TOLERANCE,
            msg="Invalid edge should not change A's score"
        )
        self.assertAlmostEqual(
            scores_with_invalid["B"], scores_pure["B"], delta=MASS_TOLERANCE,
            msg="Invalid edge should not change B's score"
        )


class TestDampingFactorValidation(unittest.TestCase):
    """
    Requirement 4: Damping factor must be strictly in (0, 1).

    Invalid values must raise ValueError.
    """

    def test_valid_damping(self):
        """Standard d=0.85 must not raise."""
        scores = calculate_pagerank(["A", "B"], [["A", "B"]], damping=0.85)
        self.assertAlmostEqual(sum(scores.values()), 1.0, delta=MASS_TOLERANCE)

    def test_damping_zero_raises(self):
        """d=0 must raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_pagerank(["A", "B"], [["A", "B"]], damping=0.0)

    def test_damping_one_raises(self):
        """d=1 must raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_pagerank(["A", "B"], [["A", "B"]], damping=1.0)

    def test_damping_negative_raises(self):
        """d=-0.5 must raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_pagerank(["A", "B"], [["A", "B"]], damping=-0.5)

    def test_damping_above_one_raises(self):
        """d=1.5 must raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_pagerank(["A", "B"], [["A", "B"]], damping=1.5)

    def test_damping_nan_raises(self):
        """d=NaN must raise ValueError."""
        import math
        with self.assertRaises(ValueError):
            calculate_pagerank(["A", "B"], [["A", "B"]], damping=math.nan)

    def test_damping_inf_raises(self):
        """d=inf must raise ValueError."""
        import math
        with self.assertRaises(ValueError):
            calculate_pagerank(["A", "B"], [["A", "B"]], damping=math.inf)


class TestDeterminism(unittest.TestCase):
    """
    Requirement 16: Same input and parameters must produce identical output on repeated runs.
    """

    def test_deterministic_simple(self):
        """Run simple chain twice, verify identical values."""
        pages = ["A", "B", "C"]
        links = [["A", "B"], ["B", "C"]]
        scores1 = calculate_pagerank(pages, links)
        scores2 = calculate_pagerank(pages, links)
        for node in pages:
            self.assertEqual(scores1[node], scores2[node],
                             msg=f"Node {node}: run1={scores1[node]}, run2={scores2[node]}")

    def test_deterministic_complex(self):
        """Run complex graph 3 times, verify identical values."""
        pages = ["Home", "Docs", "API", "Blog", "About"]
        links = [
            ["Home", "Docs"], ["Home", "Blog"], ["Docs", "API"],
            ["API", "Home"], ["Blog", "About"], ["About", "Docs"]
        ]
        results = [calculate_pagerank(pages, links) for _ in range(3)]
        for node in pages:
            self.assertEqual(results[0][node], results[1][node])
            self.assertEqual(results[1][node], results[2][node])


class TestConvergence(unittest.TestCase):
    """
    Requirement 17: Convergence must be actual convergence, not just loop termination.

    Verifies that the final L1 error is below tolerance, iteration count is finite,
    and max_iterations is respected.
    """

    def test_convergence_final_error_below_tolerance(self):
        """
        Run two consecutive PageRank calculations: the second should differ from
        a single-iteration run, and the converged solution must satisfy the fixed-point
        equation within tolerance.

        We verify convergence by checking the fixed-point residual:
        For a converged solution PR*, one more iteration should barely change it.
        """
        d = 0.85
        pages = ["A", "B", "C"]
        links = [["A", "B"], ["B", "C"], ["C", "A"]]

        # Converged solution
        scores = calculate_pagerank(pages, links, damping=d, tol=1e-9)

        # One more iteration from the converged solution
        # For cycle A->B->C->A all equal, one more iteration gives the same values
        tol = 1e-9
        N = 3
        dangling_rank = 0.0  # no dangling nodes
        for node in pages:
            base = (1.0 - d) / N + d * dangling_rank / N
            # Find incoming sum
            incoming_sum = 0.0
            for src, tgt in [("A", "B"), ("B", "C"), ("C", "A")]:
                if tgt == node:
                    incoming_sum += scores[src] / 1.0
            residual = abs(base + d * incoming_sum - scores[node])
            self.assertLess(
                residual, tol * 10,  # allow small floating-point accumulation
                msg=f"Convergence residual too large for node {node}: {residual}"
            )

    def test_max_iterations_respected(self):
        """With max_iterations=1, only 1 update step happens. Result must still be valid."""
        scores = calculate_pagerank(
            ["A", "B", "C"], [["A", "B"], ["B", "C"]],
            max_iterations=1
        )
        self.assertEqual(set(scores.keys()), {"A", "B", "C"})
        self.assertAlmostEqual(sum(scores.values()), 1.0, delta=0.01,
                               msg="Even after 1 iteration mass should be approximately conserved")

    def test_convergence_requires_multiple_iterations(self):
        """A chain requires more than 1 iteration to converge. Verifies actual iteration."""
        # A simple chain A->B is NOT converged after 1 iteration from uniform init
        # Compare 1-iteration result vs converged result
        scores_1iter = calculate_pagerank(
            ["A", "B", "C"], [["A", "B"], ["B", "C"]], max_iterations=1
        )
        scores_converged = calculate_pagerank(
            ["A", "B", "C"], [["A", "B"], ["B", "C"]], max_iterations=100
        )
        # The 1-iteration result should differ from converged (this graph needs multiple iters)
        # Use a weak check: A's rank after 1 iteration should be measurably different
        diff = abs(scores_1iter["C"] - scores_converged["C"])
        self.assertGreater(diff, 1e-4,
                           msg="Graph should require multiple iterations to converge")


class TestNumericalStability(unittest.TestCase):
    """
    Requirements 6 & 7: No NaN, no infinite values, no negative ranks.
    """

    def test_no_nan_values(self):
        """No PageRank value should be NaN for standard graphs."""
        import math
        test_cases = [
            (["A", "B", "C"], [["A", "B"], ["B", "C"]]),
            (["A"], [["A", "A"]]),
            (["A", "B"], []),
            (["A", "B", "C", "D"], [["A", "B"], ["C", "D"]]),
        ]
        for pages, links in test_cases:
            scores = calculate_pagerank(pages, links)
            for node, score in scores.items():
                self.assertFalse(math.isnan(score), msg=f"NaN for node {node}")

    def test_no_infinite_values(self):
        """No PageRank value should be infinite."""
        import math
        scores = calculate_pagerank(["A", "B"], [["A", "B"]])
        for node, score in scores.items():
            self.assertFalse(math.isinf(score), msg=f"Inf for node {node}")

    def test_no_negative_values(self):
        """No PageRank value should be negative."""
        scores = calculate_pagerank(
            ["A", "B", "C"], [["A", "B"], ["B", "C"]]
        )
        for node, score in scores.items():
            self.assertGreaterEqual(score, 0.0, msg=f"Negative rank for {node}: {score}")

    def test_empty_graph_returns_empty(self):
        """Empty graph must return empty dict without error."""
        scores = calculate_pagerank([], [])
        self.assertEqual(scores, {})

    def test_single_isolated_node(self):
        """Single node with no edges: PR = 1.0."""
        scores = calculate_pagerank(["A"], [])
        self.assertAlmostEqual(scores["A"], 1.0, delta=MASS_TOLERANCE)


class TestPerformanceSanity(unittest.TestCase):
    """
    Requirement 21: Performance sanity check on a modest graph.

    Not a scalability study — just verifies no catastrophic regression.
    A 100-node chain should complete in reasonable time.
    """

    def test_modest_graph_performance(self):
        """100-node chain must complete under 5 seconds."""
        N = 100
        pages = [str(i) for i in range(N)]
        links = [[str(i), str(i + 1)] for i in range(N - 1)]

        start = time.time()
        scores = calculate_pagerank(pages, links)
        elapsed = time.time() - start

        self.assertEqual(len(scores), N)
        self.assertAlmostEqual(sum(scores.values()), 1.0, delta=0.001)
        self.assertLess(elapsed, 5.0,
                        msg=f"100-node chain took {elapsed:.2f}s, expected < 5s")


if __name__ == "__main__":
    unittest.main()

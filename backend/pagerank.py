def calculate_pagerank(pages, links, d=0.85, max_iterations=100, tol=1.0e-6):
    """
    Computes the PageRank of given pages and links.
    
    :param pages: List of webpage names (nodes)
    :param links: List of directed links [source, target] (edges)
    :param d: Damping factor (default 0.85)
    :param max_iterations: Maximum number of iterations for convergence
    :param tol: Tolerance for convergence
    :return: Dictionary of {page: pagerank_score}
    """
    N = len(pages)
    if N == 0:
        return {}
    
    # 1. Initialize equal ranks for all pages: PR = 1/N
    pr = {page: 1.0 / N for page in pages}
    
    # 2. Calculate outgoing links count C(Ti) for each page
    out_degree = {page: 0 for page in pages}
    for source, target in links:
        if source in out_degree:
            out_degree[source] += 1
            
    # Handle duplicate links by treating them as single if necessary,
    # but based on the UI we should prevent duplicates. We will assume links are unique.

    # 3. Iteratively distribute rank
    for iteration in range(max_iterations):
        new_pr = {}
        diff = 0
        
        # For each node A
        for page in pages:
            rank_sum = 0
            
            # Find all nodes Ti that link to A
            for source, target in links:
                if target == page:
                    # Add PR(Ti) / C(Ti)
                    # C(Ti) is out_degree[source]
                    if out_degree[source] > 0:
                        rank_sum += pr[source] / out_degree[source]
            
            # PR(A) = (1-d)/N + d * sum
            new_pr[page] = ((1.0 - d) / N) + (d * rank_sum)
            
            # Calculate difference for convergence check
            diff += abs(new_pr[page] - pr[page])
            
        pr = new_pr
        
        # 4. Check convergence
        if diff < tol:
            print(f"Converged after {iteration + 1} iterations.")
            break
            
    # 5. Return normalized final scores (Optional step, but ensures sum to 1 if there were no dangling nodes)
    # Due to dangling nodes, the sum might be less than 1. We can normalize it.
    total_pr = sum(pr.values())
    if total_pr > 0:
        pr = {k: v / total_pr for k, v in pr.items()}
        
    return pr

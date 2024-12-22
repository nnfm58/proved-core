from copy import deepcopy
from itertools import combinations
from typing import Set, List, Tuple, Dict, FrozenSet

from pm4py.objects.log.obj import EventLog, Trace
from pm4py.util.xes_constants import DEFAULT_NAME_KEY


def uSupport(x: Set[str], u_log: List[List[Trace]]) -> Tuple[float, float]:
    """Calculates the minimum and maximum support for an itemset x
    in an uncertain event log.
    
    The minimum support value for x in u_log counts how many uncertain traces in u_log contain x in all their realizations. The maximum support value for x in u_log counts how many uncertain traces in u_log contain x in at least one of their realizations.

    Args:
        x (set): An itemset, which is a subset of A.
        u_log (list of list of Traces): A multiset of trace realizations.

    Returns:
        tuple: A tuple containing two values, the minimum and maximum support for the itemset x in the event log.

    """
    # Initialize support counts
    min_support_count = 0
    max_support_count = 0

    for realization_sets in u_log:
        # Get the set of events for each realization
        events = [set(event[DEFAULT_NAME_KEY] for event in realization) for realization in realization_sets]

        # Check if x is in all realizations for this uncertain trace
        if all(x.issubset(realization) for realization in events):
            min_support_count += 1
        
        # Check if x is in at least one realization for this uncertain trace
        if any(x.issubset(realization) for realization in events):
            max_support_count += 1

    # Calculate the minimum and maximum support values
    num_traces = len(u_log)
    min_support = min_support_count / num_traces
    max_support = max_support_count / num_traces
    
    return (min_support, max_support)


def uSupport_prob(x: Set[str], 
                  u_log: EventLog,
                  trace_probability_key: str = "trace_probability"
                  ) -> Tuple[float, float]:
    
    """Calculates the minimum and maximum support for an itemset x
    in an uncertain event log U_log.
    
    Modifies uSupport to calculate support taking probabilities into account.

    Args:
        x (set): An itemset, which is a subset of A.
        u_log (list of list of Traces): A multiset of trace realizations.

    Returns:
        tuple: A tuple containing two values, the minimum and maximum support for the itemset x in the dataset D.

    """

    min_support = 0.0
    max_support = 0.0

    for realization_set in u_log:
        realizations = [([event[DEFAULT_NAME_KEY] for event in r], r.attributes[trace_probability_key]) for r in realization_set]

        all_realizations_have_x = all(x.issubset({label for label in realization}) for realization, _ in realizations)
        
        if all_realizations_have_x:
            min_support += 1

        for event_seq, cum_prob in realizations:
            if x.issubset({label for label in event_seq}):
                    max_support += cum_prob

    # Calculate the support values as a fraction of the total number of traces
    avg_min_support = round(min_support, 5) / len(u_log)
    avg_max_support = round(max_support, 5) / len(u_log)
    return (avg_min_support, avg_max_support)


def generate_new_candidates(
        current_candidates: Set[FrozenSet[str]], 
        previous_frequent_sets: Set[FrozenSet[str]], k: int) -> Set[FrozenSet[str]]:
    """Generate new candidate itemsets of size k+1 from current candidates."""
    new_candidates = set()
    for A, B in combinations(current_candidates, 2):
        if len(A.intersection(B)) == k - 1:
            union_set = A.union(B)
            if len(union_set) == k + 1:
                if all(frozenset(subset) in previous_frequent_sets for subset in combinations(union_set, k)):
                    new_candidates.add(union_set)
    return new_candidates


def UA_Apriori(
        u_log: List[List[Trace]], 
        support_pairs: List[Tuple[float, float]],
        activity_key: str = DEFAULT_NAME_KEY) -> Dict[Tuple[float, float], List[Tuple[FrozenSet[str], float, float]]]:
    
    """
    Implement the Apriori algorithm to find frequent itemsets for multiple support pairs.
    
    Args:
        u_log (list of lists): The realization of the uncertain event log.
        support_pairs (list of tuples): List of tuples where each tuple is a (minsup, maxsup) pair.
    
    Returns:
        dict: Dictionary where keys are support pairs and values are lists of frequent itemsets with their min_ and max_support.
    """
    results = {pair: [] for pair in support_pairs}
    frequent_sets_per_pair = {pair: set() for pair in support_pairs}

    # Generate candidate itemsets
    initial_candidates = {frozenset([event[activity_key]]) for realization_set in u_log for realization in realization_set for event in realization}

    candidates_per_pair = {pair: deepcopy(initial_candidates) for pair in support_pairs}


    k = 1 # Start with itemsets of size 1
    while any(candidates_per_pair.values()):
        # Calculate support for all current candidates
        support_cache = {}
        all_candidates = set().union(*candidates_per_pair.values())
        for item_set in all_candidates:
            support_cache[item_set] = uSupport(item_set, u_log)

        # Filter and update candidates for each support pair
        for pair in support_pairs:
            minsup, maxsup = pair
            new_candidates = set()
            for item_set in candidates_per_pair[pair]:
                u_minsup, u_maxsup = support_cache[item_set]
                if u_minsup >= minsup and u_maxsup <= maxsup:
                    results[pair].append((item_set, u_minsup, u_maxsup))
                    new_candidates.add(item_set)
                    frequent_sets_per_pair[pair].add(item_set)
            # Generate new candidates for the next iteration with pruning
            candidates_per_pair[pair] = generate_new_candidates(new_candidates, frequent_sets_per_pair[pair], k)

        k += 1 # Increment itemset size

    return results


def UA_Apriori_prob(u_log: List[List[Trace]], 
    support_pairs: List[Tuple[float, float]],
    activity_key: str = DEFAULT_NAME_KEY) -> Dict[Tuple[float, float], List[Tuple[FrozenSet[str], float, float]]]:
    """Implement the Apriori algorithm to find frequent itemsets for multiple support pairs.
    
    Args:
        u_log (list of lists): The uncertain event log.
        support_pairs (list of tuples): List of tuples where each tuple is a (minsup, maxsup) pair.
    
    Returns:
        dict: Dictionary where keys are support pairs and values are lists of frequent itemsets with their min_ and max_support.
    """
    results = {pair: [] for pair in support_pairs}
    frequent_sets_per_pair = {pair: set() for pair in support_pairs}

    # Generate candidate itemsets
    initial_candidates = {frozenset([event[activity_key]]) for realization_set in u_log for realization in realization_set for event in realization if event[activity_key] is not None}

    candidates_per_pair = {pair: deepcopy(initial_candidates) for pair in support_pairs}


    k = 1 # Start with itemsets of size 1
    while any(candidates_per_pair.values()):
        # Calculate support for all current candidates
        support_cache = {}
        all_candidates = set().union(*candidates_per_pair.values())
        for item_set in all_candidates:
            support_cache[item_set] = uSupport_prob(item_set, u_log)

        # Filter and update candidates for each support pair
        for pair in support_pairs:
            minsup, maxsup = pair
            new_candidates = set()
            for item_set in candidates_per_pair[pair]:
                u_minsup, u_maxsup = support_cache[item_set]
                if u_minsup >= minsup and u_maxsup <= maxsup:
                    results[pair].append((item_set, u_minsup, u_maxsup))
                    new_candidates.add(item_set)
                    frequent_sets_per_pair[pair].add(item_set)
            # Generate new candidates for the next iteration with pruning
            candidates_per_pair[pair] = generate_new_candidates(new_candidates, frequent_sets_per_pair[pair], k)

        k += 1 # Increment itemset size

    return results


def U_Apriori_mod(u_log: List[List[Trace]], 
    support_pairs: List[Tuple[float, float]],
    activity_key: str = DEFAULT_NAME_KEY) -> Dict[Tuple[float, float], List[Tuple[FrozenSet[str], float, float]]]:
    """Implement the Apriori algorithm to find frequent itemsets for multiple support pairs replicating the algorithm presented in:
    
    Chui, Chun-Kit, Ben Kao, and Edward Hung. “Mining Frequent Itemsets from Uncertain Data.” In Advances in Knowledge Discovery and Data Mining, 2007. https://doi.org/10.1007/978-3-540-71701-0_8.

    Args:
        u_log (list of lists): The uncertain event log.
        support_pairs (list of tuples): List of tuples where each tuple is a (minsup, maxsup) pair.
    
    Returns:
        dict: Dictionary where keys are support pairs and values are lists of frequent itemsets with their min_ and max_support.
    """
    results = {pair: [] for pair in support_pairs}
    frequent_sets_per_pair = {pair: set() for pair in support_pairs}

    # Generate candidate itemsets
    initial_candidates = {frozenset([event[activity_key]]) for realization_set in u_log for realization in realization_set for event in realization if event[activity_key] is not None}

    candidates_per_pair = {pair: deepcopy(initial_candidates) for pair in support_pairs}


    k = 1 # Start with itemsets of size 1
    while any(candidates_per_pair.values()):
        # Calculate support for all current candidates
        support_cache = {}
        all_candidates = set().union(*candidates_per_pair.values())
        for item_set in all_candidates:
            support_cache[item_set] = uSupport_prob(item_set, u_log)

        # Filter and update candidates for each support pair
        for pair in support_pairs:
            minsup, maxsup = pair
            new_candidates = set()
            for item_set in candidates_per_pair[pair]:
                u_minsup, u_maxsup = support_cache[item_set]
                if u_maxsup >= maxsup:
                    results[pair].append((item_set, u_minsup, u_maxsup))
                    new_candidates.add(item_set)
                    frequent_sets_per_pair[pair].add(item_set)
            # Generate new candidates for the next iteration with pruning
            candidates_per_pair[pair] = generate_new_candidates(new_candidates, frequent_sets_per_pair[pair], k)

        k += 1 # Increment itemset size

    return results
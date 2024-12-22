import sys
from collections import defaultdict
from copy import deepcopy
from itertools import combinations, permutations
from typing import List, Tuple, Dict, Any
from abc import ABC, abstractmethod


class BaseWINEPI(ABC):

    def __init__(self, 
            realization: List[List[Tuple]], 
            width: int, 
            step: int = 1, 
            min_supp_threshold: float = 0, 
            max_supp_threshold: float = float('inf')
    ):
        """Initializes the BaseWINEPI object.

        Args:
            realization (list of list of tuple): A list of event sequences,     
                where each event sequence is a list of tuples.Each tuple consists of a timestamp and an event label, e.g., (timestamp, event_label).            
            width (int): The width of the sliding window, representing the  
                range of timestamps to include in each window.
            step (int, optional): The step size for moving the sliding window 
                forward. Default is 1.         
            min_supp_threshold (int): The minimum support threshold for 
                considering an itemset as frequent. Default is 0.
            max_supp_threshold (float): The maximum support threshold for 
                considering an itemset as frequent. Default is infinity.
        """ 
        self.realization = realization
        self.width = width
        self.step = step
        self.min_supp_threshold = min_supp_threshold
        self.max_supp_threshold = max_supp_threshold

    @abstractmethod
    def is_subset(self, candidate: List[Any], window: List[Any]) -> bool:
        """Checks whether the candidate is a subset of the window."""
        pass


    @abstractmethod
    def generate_candidates(self, lk: List[Any], k: int) -> List[List[Any]]:
        """ Generates a list of candidate itemsets."""
        pass

    
    @abstractmethod
    def filter_candidates(self,
            min_max_counts: Dict[Tuple, Tuple[float, float]]
        ) -> List[Tuple]:
        pass


    def apriori_gen(self, Lk: List[Tuple], k: int) -> List[List[Any]]:
        """Generates the next set of candidate itemsets (Ck) using combinations.
        
        Args:
            Lk (list of frozenset): The list of frequent itemsets.
            k (int): The size of the next candidate itemsets.
            
        Returns:
            list: A list of candidate itemsets of size k.
        """
        Ck = []
        candidates = [] 
        lk = sorted(set([item for t in Lk for item in t])) # get and sort elements from frozenset
        candidates = self.generate_candidates(lk, k)
        for candidate in candidates:
            if self.check_subset_freq(candidate, Lk, k-1):
                Ck.append(candidate)
        return Ck
    

    def sliding_window(self) -> List[List[Tuple]]:
        """Generates windows of events using a sliding window approach on each event sequence in the realization set.

        Returns:
            nested_windows (list of list of TUPLES?): A nested list where each 
                sublist is a series of windows generated from a corresponding event sequence in the realization set. Each window is represented as a tuple.
        """
        nested_windows = []
        for i, sequence in enumerate(self.realization):
            t_end = sequence[0][0] + self.step
            t_start = t_end - self.width
            no_windows = int((sequence[-1][0] - sequence[0][0] + self.width) / self.step)
            
            # Initialize windows with the first window already computed
            windows = [list([sequence[0][1]])]
            
            for _ in range(1, no_windows):  # Start from 1 as the first window is already computed
                t_start += self.step
                t_end += self.step
                row = [event[1] for event in sequence if t_start <= event[0] < t_end]
                windows.append(row)
            
            nested_windows.append([tuple(uw) for uw in windows]) 
        return nested_windows


    def create_C1(self) -> List[List[Any]]:
        """Create list of candidates of lenght k=1.

        Returns:
            C1 (list): List that contains the lists of candidates with lenght 1.
        """
        C1_set = set()
        for sequence in self.realization:
            for event in sequence:
                C1_set.add(event[1])
        C1 = [[item] for item in sorted(C1_set)]
        return C1
    

    @staticmethod
    def check_subset_freq(candidate: Tuple, Lk: List[Tuple], k: int) -> bool:
        """Check if all subsets of a candidate epsiodes are frequent.

        Generates all possible k-length subsets of the given candidate episodes and checks if each of these subsets is in the list of frequent episodes Lk.

        Args:
            candidate (tuple): The candidate episodes whose subsets are to be
                checked.
            Lk (list of tuples): A list frequent episodes.
            k (int): The length of the subsets to be checked.

        Returns:
            bool: True if all subsets are frequent. False otherwise.
        """
        if k>1:    
            subsets = list(combinations(candidate, k))
        else:
            return True
        for elem in subsets:
            if not elem in Lk:
                return False
        return True


    def scan_windows(self, 
            nested_windows: List[List[Tuple]], 
            Ck: List[List[Any]]
    ) -> Tuple[List[Tuple], Dict[Tuple, Tuple[int, int]]]:
        """Scan through nested windows to count the occurrence of each candidate sequence (Ck).
        
        Args:
            nested_windows (list of list of tuples): Each sublist represents a
                window containing ordered sequences of items.
            Ck (list of lists): Ordered candidate sequences to be counted.
            
        Returns:
            tuple: Two elements:
                - A dictionary with keys as sequences and values as a tuple (min_count, max_count).
        """
        supp_counters = [{} for _ in range(len(nested_windows))]

        # Loop through the nested list and update counters
        for i, windows in enumerate(nested_windows):
            no_windows = len(windows)
            for candidate in Ck:
                for win in windows:
                    if self.is_subset(candidate, win):
                        supp_counters[i][tuple(candidate)] = supp_counters[i].get(tuple(candidate), 0) + 1
            for key in supp_counters[i]:
                supp_counters[i][key] /= no_windows   
        # Initialize a defaultdict to keep count of how many sublists each candidate is in
        element_count = defaultdict(int)

        # Initialize dictionaries to store the minimum and maximum counts for each element
        min_count = {}
        max_count = {}

        # Count the number of sublists each element is in
        # and also keep track of the min and max counts for each element
        for counter in supp_counters:
            for k, v in counter.items():
                element_count[k] += 1
                min_count[k] = round(min(min_count.get(k, sys.maxsize), v), 1)
                max_count[k] = round(max(max_count.get(k, -sys.maxsize), v), 1)

        min_max_counts = {}
        total_sublists = len(supp_counters)

        # Populate final_counts with the min and max counts and a boolean
        for k, v in element_count.items():
            # Check if a candidate appears in all of the sublists of nested_windows
            is_in_all_sublists = (v == total_sublists)
            # Set min_count to zero if the itemset is not in all sublists
            min_count[k] = 0 if not is_in_all_sublists else min_count[k]
            min_max_counts[k] = (min_count[k], max_count[k])

        return min_max_counts


    def winepi(self) -> Tuple[List[List[Tuple]], Dict[Tuple, Tuple[int, int]]]:
        """Apply the WinEpi algorithm to identify frequent episodes within sliding windows of a sequence.

        Returns:
            tuple: Two elements:
                - A list of lists, where each sublist contains the frequent itemsets of length k.
                - A dictionary with keys as itemsets and values as a tuple (min_count, max_count), which represent the minimum and maximum support count for each itemset.
        """
        C1 = self.create_C1()
        nested_windows = self.sliding_window()
        min_max_count = self.scan_windows(nested_windows, C1)
        L1 = self.filter_candidates(min_max_count)
        
        L = [L1]
        k = 2
        while (len(L[k-2]) > 0):
            Ck = self.apriori_gen(L[k-2], k)
            min_max_count_k = self.scan_windows(nested_windows, Ck) 
            Lk = self.filter_candidates(min_max_count_k) 
            min_max_count.update(min_max_count_k)
            L.append(Lk)
            k += 1
        
        # remove empty last itemset from L
        if not L[-1]:
            L.pop()
        return L, min_max_count
    
    
class SerialWINEPI(BaseWINEPI):

    def generate_candidates(self, lk: List[Any], k: int) -> List[List[Any]]:
        return list(permutations(lk, k))

    def is_subset(self, sub: List[Any], lst: List[Any]) -> bool:
        """Checks whether all elements in 'sub' appear in 'lst' in the same order. Elements in 'sub' can have gaps between them when appearing in 'lst'.

        Args:
            sub (list): The sublist to check.
            lst (list): The list in which to check for the sublist.
        
        Returns:
            bool: True if all elements in 'sub' are in 'lst' in the same order.
        """
        lenght, j = len(sub), 0
        for elem in lst:
            if elem == sub[j]:
                j += 1
            if j == lenght:
                return True
        return False
    
    def filter_candidates(self,
            min_max_counts: Dict[Tuple, Tuple[float, float]]
        ) -> List[Tuple]:
        """
        Filters candidate episodes based on minimum and maximum support thresholds.

        Args:
            min_max_counts (Dict[Tuple, Tuple[float, float]]): A dictionary mapping each candidate episode to its minimum and maximum support values.
        Returns:
            List[Tuple]: A list of candidate episodes that meet both the minimum and maximum support thresholds.
        """

        Lk = [candidate for candidate, (min_count, max_count) in min_max_counts.items() if min_count >= self.min_supp_threshold and max_count <= self.max_supp_threshold]

        return Lk


class ParallelWINEPI(BaseWINEPI):
    def generate_candidates(self, lk: List[Any], k: int) -> List[List[Any]]:
        return list(combinations(lk, k))

    
    def is_subset(self, sub: List[Any], lst: List[Any]) -> bool:
        """Checks whether all elements in 'sub' appear in 'lst'
        
        Args:
            sub (list): The sublist to check.
            lst (list): The list in which to check for the sublist.
        
        Returns:
            bool: True if all elements in 'sub' are in 'lst'.
        """
        return set(sub).issubset(lst)

    def filter_candidates(self,
            min_max_counts: Dict[Tuple, Tuple[float, float]]
        ) -> List[Tuple]:
        """
        Filters candidate episodes based on minimum and maximum support thresholds.

        Args:
            min_max_counts (Dict[Tuple, Tuple[float, float]]): A dictionary mapping each candidate episode to its minimum and maximum support values.
        Returns:
            List[Tuple]: A list of candidate episodes that meet both the minimum and maximum support thresholds.
        """

        Lk = [candidate for candidate, (min_count, max_count) in min_max_counts.items() if min_count >= self.min_supp_threshold and max_count <= self.max_supp_threshold]

        return Lk
    
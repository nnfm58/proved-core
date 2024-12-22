import operator
from typing import List, Tuple

from networkx import DiGraph
from pm4py.objects.log.obj import Event, Trace
from pm4py.util.xes_constants import DEFAULT_NAME_KEY, DEFAULT_TIMESTAMP_KEY

import proved.xes_keys as xes_keys


class BehaviorGraph(DiGraph):
    """
    Class representing a behavior graph, a directed acyclic graph showing the precedence relationship between uncertain events.
    For more information refer to:
        Pegoraro, Marco, and Wil MP van der Aalst. "Mining uncertain event data in process mining." 2019 International Conference on Process Mining (ICPM). IEEE, 2019.

    :param trace: Trace object containing uncertain event data.
    :param activity_key: Key used to identify activity labels in the trace.
    :param timestamp_key: Key used to identify timestamps in the trace.
    :param u_timestamp_min_key: Key used for minimum timestamp in uncertain data.
    :param u_timestamp_max_key: Key used for maximum timestamp in uncertain data.
    :param u_missing_key: Key used for missing probability in uncertain data.
    :param u_activity_key: Key used for uncertain activity names.
    """


    def __init__(self, 
                 trace: Trace, 
                 activity_key: str = DEFAULT_NAME_KEY, 
                 timestamp_key: str = DEFAULT_TIMESTAMP_KEY, 
                 u_timestamp_min_key: str = xes_keys.DEFAULT_U_TIMESTAMP_MIN_KEY, 
                 u_timestamp_max_key: str = xes_keys.DEFAULT_U_TIMESTAMP_MAX_KEY, 
                 u_missing_key: str = xes_keys.DEFAULT_U_MISSING_KEY, 
                 u_activity_key: str = xes_keys.DEFAULT_U_NAME_KEY):
        super().__init__()

        self.trace = trace
        self.activity_key = activity_key
        self.timestamp_key = timestamp_key
        self.u_timestamp_min_key = u_timestamp_min_key
        self.u_timestamp_max_key = u_timestamp_max_key
        self.u_missing_key = u_missing_key
        self.u_activity_key = u_activity_key


        # Generate and add nodes and edges to the graph
        node_tuples = self.create_nodes_tuples()
        self.add_nodes_from_graph(node_tuples)
        self.add_edges_from_nodes(node_tuples)



    def create_nodes_tuples(self) -> List[Tuple[Tuple[int, Tuple[Tuple[str, float], ...]], bool]]:
        """
        Creates nodes tuples for each event in a trace, considering uncertainties in activities and timestamps. 
        Each node is represented as a tuple, containing the event index, a tuple of (label, probability) pairs, 
        and a boolean indicating timestamp type.

        :return: A list of nodes tuples.
        """
        nodes_tuples = []
        for i, event in enumerate(self.trace):
            node = self.process_event(event, i)
            self.add_node_tuples(event, node, nodes_tuples)
        
        nodes_tuples.sort(key=operator.itemgetter(0, 2))

        return tuple((node, timestamp_type) for _, (node), timestamp_type in nodes_tuples)
    

    def process_event(self, 
                      event: Event, 
                      event_index: int) -> Tuple[int, Tuple[Tuple[str, float], ...]]:
        """
        Processes an individual event from the trace, considering uncertainties.
        Returns a tuple with the event index, and a tuple of tuples for each possible event label and its uncertainty details.
        
        :param event: The event to be processed.
        :param event_index: The index of the event in the trace.
        :return: A tuple (event_index, ((event_label, uncertainty_info), ...)).
        """

        event_options = []
        common_uncertainty_info = {}
        # Add timestamp info
        common_uncertainty_info[self.timestamp_key]= event[self.timestamp_key]

        if self.u_missing_key in event:
            common_uncertainty_info[self.u_missing_key] = event[self.u_missing_key]

        if self.u_timestamp_min_key in event and self.u_timestamp_max_key in event:
            common_uncertainty_info[self.u_timestamp_min_key] = event[self.u_timestamp_min_key]
            common_uncertainty_info[self.u_timestamp_max_key] = event[self.u_timestamp_max_key]

        # Handle label uncertainty
        if self.u_activity_key in event:
            for label, prob in event[self.u_activity_key]['children'].items():
                uncertainty_info = common_uncertainty_info.copy()
                uncertainty_info[self.u_activity_key] = prob
                event_options.append((label, uncertainty_info))
        else:
            # Handle events without label uncertainty
            event_options.append((event[self.activity_key], common_uncertainty_info))

        # Handle missing event
        if self.u_missing_key in event and event[self.u_missing_key] <= 1:
            missing_info = common_uncertainty_info.copy()
            missing_info[self.u_missing_key] = 1 - event[self.u_missing_key]
            event_options.append((None, missing_info))

        return event_index, tuple(event_options)

    
    def add_node_tuples(
            self,
            event: Event, 
            new_node: Tuple[int, Tuple[Tuple[str, float], ...]], 
            nodes_tuples: List[Tuple[Tuple[int, Tuple[Tuple[str, float]]], bool]]):
        """
        Adds node tuples with their corresponding label-probability tuples and timestamp types to the nodes list.
        
        :param event: The event being processed.
        :param new_node: The new node tuple.
        :param nodes_tuples: The existing list of node tuples.
        """
        # Check if the event has a minimum uncertain timestamp
        if self.u_timestamp_min_key not in event:
            # Use the actual timestamp
            nodes_tuples.append((event[self.timestamp_key], new_node, False))
            nodes_tuples.append((event[self.timestamp_key], new_node, True)) 
        else:
            # Add nodes for both minimum and maximum timestamps
            nodes_tuples.append((event[self.u_timestamp_min_key], new_node, False))  # False indicates minimum timestamp
            nodes_tuples.append((event[self.u_timestamp_max_key], new_node, True))  # True indicates maximum timestamp
    

    def add_nodes_from_graph(self, node_tuples: List[Tuple]):
        """
        Adds nodes to the behavior graph based on provided node tuples.

        :param node_tuples: A list of tuples representing nodes in the behavior graph.
        """

        for node, timestamp_type in node_tuples:
            node_id, label_u_dict_tuples = node
            labels = frozenset(label for label, _ in label_u_dict_tuples)
            u_dict_combined = {}

            # Combine the uncertainty dictionaries for each label in the node
            for label, u_dict in label_u_dict_tuples:
                # Handle the case when the event is missing (None)
                if label is None:
                    u_dict_combined['None'] = u_dict
                else:
                    u_dict_combined[label] = u_dict

            self.add_node((node_id, labels), u_dict=u_dict_combined)
    

    def add_edges_from_nodes(self, node_tuples: List[Tuple]):
        """
        Adds edges to the behavior graph based on the node tuples.

        :param node_tuples: A list of tuples representing nodes in the behavior graph.
        """
        edges_list = []
        for i, (node1, timestamp_type1) in enumerate(node_tuples):
            edge = None
            node1_id, _ = node1
            if timestamp_type1:  # True for the end of a timestamp range
                for node2, timestamp_type2 in node_tuples[i + 1:]:
                    node2_id, _ = node2
                    if not timestamp_type2:  # False for the start of a timestamp range
                        edge = ((node1_id, frozenset(label for label, _ in node1[1])), 
                                (node2_id, frozenset(label for label, _ in node2[1])))
                        edges_list.append(edge)
                    elif edge in edges_list:
                        break      
        self.add_edges_from(edges_list)
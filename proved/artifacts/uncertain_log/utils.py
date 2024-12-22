from typing import List

from pm4py.objects.log.obj import Trace
from pm4py.util.xes_constants import DEFAULT_NAME_KEY, DEFAULT_TIMESTAMP_KEY

from proved.artifacts.behavior_graph import behavior_graph as behavior_graph_builder 
from proved.artifacts.behavior_net import behavior_net as behavior_net_builder
from proved.artifacts.behavior_net.utils import acyclic_net_variants
from proved.artifacts.uncertain_log.trace_probability_calculator import calculate_realizations_probabilities
from proved.artifacts.uncertain_log.realization_set_aggregator import get_unique_realizations
import proved.xes_keys as xes_keys


def realization_set(trace: Trace, 
                    add_probability: bool = False,
                    activity_key: str = DEFAULT_NAME_KEY, 
                    timestamp_key: str = DEFAULT_TIMESTAMP_KEY, 
                    u_timestamp_min_key: str = xes_keys.DEFAULT_U_TIMESTAMP_MIN_KEY, 
                    u_timestamp_max_key: str = xes_keys.DEFAULT_U_TIMESTAMP_MAX_KEY, 
                    u_missing_key: str = xes_keys.DEFAULT_U_MISSING_KEY, 
                    u_activity_key: str = xes_keys.DEFAULT_U_NAME_KEY
                    )-> List[Trace]:
    """
    Returns the realization set of an uncertain trace.

    :param trace: An uncertain trace.
    :type trace:
    :param add_probability: Flag for the probability calculation of each variant.
    :param activity_key: Key used to identify activity labels in the trace.
    :param timestamp_key: Key used to identify timestamps in the trace.
    :param u_timestamp_min_key: Key used for minimum timestamp in uncertain data.
    :param u_timestamp_max_key: Key used for maximum timestamp in uncertain data.
    :param u_missing_key: Key used for missing probability in uncertain data.
    :param u_activity_key: Key used for uncertain activity names.
    :return: The realization set of the trace in input.
    :rtype:
    """

    behavior_graph = behavior_graph_builder.BehaviorGraph(
        trace, 
        activity_key,       
        timestamp_key, 
        u_timestamp_min_key, 
        u_timestamp_max_key, 
        u_missing_key, 
        u_activity_key
        )

    behavior_net = behavior_net_builder.BehaviorNet(behavior_graph)
    bn_i = behavior_net.initial_marking
    bn_f = behavior_net.final_marking
    
    trace_realizations = acyclic_net_variants(behavior_net, bn_i, bn_f)

    if add_probability:
        # Add attribute with the probability of each trace realization 
        calculate_realizations_probabilities(
            trace_realizations,
            u_missing_key,
            u_timestamp_min_key,
            u_timestamp_max_key,
            u_activity_key) 

    unique_realizations = get_unique_realizations(
        trace_realizations, 
        add_probability,
        activity_key
        )


    return unique_realizations
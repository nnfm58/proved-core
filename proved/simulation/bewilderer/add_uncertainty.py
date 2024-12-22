from pm4py.objects.log.util.xes import DEFAULT_NAME_KEY, DEFAULT_TIMESTAMP_KEY

from proved.xes_keys import DEFAULT_U_NAME_KEY, DEFAULT_U_TIMESTAMP_MIN_KEY, DEFAULT_U_TIMESTAMP_MAX_KEY, DEFAULT_U_MISSING_KEY


from proved.simulation.bewilderer.add_activities import add_uncertain_activities_to_log, add_uncertain_activities_to_trace
from proved.simulation.bewilderer.add_timestamps import add_uncertain_timestamp_to_log, add_uncertain_timestamp_to_trace
from proved.simulation.bewilderer.add_indeterminate_events import add_indeterminate_events_to_log, add_indeterminate_events_to_trace


def add_uncertainty(p_a=0.0, p_t=0.0, p_i=0.0, log=None, log_map=None, max_labels_to_add=1, label_set=None, activity_key=DEFAULT_NAME_KEY, u_activity_key=DEFAULT_U_NAME_KEY, timestamp_key=DEFAULT_TIMESTAMP_KEY, u_timestamp_min_key=DEFAULT_U_TIMESTAMP_MIN_KEY, u_timestamp_max_key=DEFAULT_U_TIMESTAMP_MAX_KEY, u_missing_key=DEFAULT_U_MISSING_KEY):
    add_uncertain_activities_to_log(p_a, log, log_map=log_map, max_labels_to_add=max_labels_to_add, label_set=label_set, activity_key=activity_key, u_activity_key=u_activity_key)
    add_uncertain_timestamp_to_log(p_t, log, log_map=log_map, timestamp_key=timestamp_key, u_timestamp_min_key=u_timestamp_min_key, u_timestamp_max_key=u_timestamp_max_key)
    add_indeterminate_events_to_log(p_i, log, log_map=log_map, u_missing_key=u_missing_key)


def add_uncertainty_to_trace(p_a=0.0, p_t=0.0, p_i=0.0, 
        trace=None, 
        max_labels_to_add=1, 
        label_set=None,
        activity_key=DEFAULT_NAME_KEY, 
        u_activity_key=DEFAULT_U_NAME_KEY, 
        timestamp_key=DEFAULT_TIMESTAMP_KEY, 
        u_timestamp_min_key=DEFAULT_U_TIMESTAMP_MIN_KEY, u_timestamp_max_key=DEFAULT_U_TIMESTAMP_MAX_KEY, 
        u_missing_key=DEFAULT_U_MISSING_KEY):
    """
    Adds uncertainty to events in a trace. It can add:
    - Uncertain activity labels with probability p_a
    - Uncertain timestamps with probability p_t
    - Indeterminate (missing) events with probability p_i

    :param trace: The trace (list of events)
    :param p_a: Probability of adding uncertain activity labels
    :param p_t: Probability of adding uncertain timestamps
    :param p_i: Probability of marking events as indeterminate
    :param max_labels_to_add: Maximum number of uncertain activity labels to add
    :param label_set: Set of possible activity labels to choose from
    :return: None (modifies the trace in place)
    """
    
    add_uncertain_activities_to_trace(p_a, trace,  
        max_labels_to_add = max_labels_to_add,
        label_set=label_set, activity_key=activity_key, 
        u_activity_key=u_activity_key)
    
    
    add_uncertain_timestamp_to_trace(p_t, trace,
        timestamp_key=timestamp_key, 
        u_timestamp_min_key=u_timestamp_min_key, 
        u_timestamp_max_key=u_timestamp_max_key)

    add_indeterminate_events_to_trace(p_i, trace, u_missing_key=u_missing_key)

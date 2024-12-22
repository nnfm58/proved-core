
from random import random, sample, uniform
from warnings import warn

from pm4py.objects.log.obj import Trace
from pm4py.objects.log.util.xes import DEFAULT_NAME_KEY

from proved.xes_keys import DEFAULT_U_NAME_KEY


def add_uncertain_activities_to_log(p, log=None, log_map=None, max_labels_to_add=1, label_set=None, activity_key=DEFAULT_NAME_KEY, u_activity_key=DEFAULT_U_NAME_KEY):
    """
    Adds possible activity labels to events in a trace with a certain probability, up to a maximum.

    :param trace: the trace
    :param p: the probability of indeterminate events
    :param label_set: the list of new possible activity labels
    :param max_labels: the maximum number of uncertain activity labels (unbounded if 0)
    :param activity_key: the xes key for the activity labels
    :param u_activity_key: the xes key for uncertain activity labels
    :return:
    """

    if p > 0.0:

        build_label_set = False
        if label_set is None:
            build_label_set = True

        if log_map is None:
            if log is None:
                raise ValueError('Parameters log and log_map cannot both be None.')
            else:
                log_map = {}
                if build_label_set:
                    label_set = set()
                i = 0
                for trace in log:
                    for j in range(len(trace)):
                        log_map[i] = (trace, j)
                        if build_label_set:
                            label_set.add(trace[j][activity_key])
                        i += 1

        to_alter = max(0, round(len(log_map) * p))
        indices_to_alter = sample(frozenset(log_map), to_alter)
        labels_to_add = min(max_labels_to_add, len(label_set) - 1)
        for i in indices_to_alter:
            trace, j = log_map[i]
            trace[j][u_activity_key] = dict()
            trace[j][u_activity_key]['children'] = {activity_label: 0 for activity_label in [trace[j][activity_key]] + sample(list(label_set - {trace[j][activity_key]}), labels_to_add)}


def add_uncertain_activities_to_log_montecarlo(log, p, max_labels=0, label_set=None, activity_key=DEFAULT_NAME_KEY, u_activity_key=DEFAULT_U_NAME_KEY):
    """
    Adds possible activity labels to events in an event log with a certain probability, up to a maximum.

    :param log: the event log
    :param p: the probability of indeterminate events
    :param label_set: the list of new possible activity labels
    :param max_labels: the maximum number of uncertain activity labels (unbounded if 0)
    :param activity_key: the xes key for the activity labels
    :param u_activity_key: the xes key for uncertain activity labels
    :return:
    """

    if p > 0.0:
        if label_set is None:
            label_set = set()
            for trace in log:
                for event in trace:
                    label_set.add(event[activity_key])
        for trace in log:
            add_uncertain_activities_to_trace_montecarlo(trace, p, label_set, max_labels, activity_key, u_activity_key)


def add_uncertain_activities_to_trace_montecarlo(trace, p, max_labels=0, label_set=None, activity_key=DEFAULT_NAME_KEY, u_activity_key=DEFAULT_U_NAME_KEY):
    """
    Adds possible activity labels to events in a trace with a certain probability, up to a maximum.

    :param trace: the trace
    :param p: the probability of indeterminate events
    :param label_set: the list of new possible activity labels
    :param max_labels: the maximum number of uncertain activity labels (unbounded if 0)
    :param activity_key: the xes key for the activity labels
    :param u_activity_key: the xes key for uncertain activity labels
    :return:
    """

    if p > 0.0:
        if label_set is None:
            label_set = set()
            for event in trace:
                label_set.add(event[activity_key])
        for event in trace:
            to_add = 0
            if max_labels == 0 or max_labels > len(label_set):
                if u_activity_key not in event:
                    max_labels = len(label_set) - 1
                else:
                    max_labels = len(label_set) - len(event[u_activity_key]['children'])
            while random() < p and to_add < max_labels:
                to_add += 1
            if to_add > 0:
                if u_activity_key not in event:
                    event[u_activity_key] = dict()
                    event[u_activity_key]['children'] = {activity_label: 0 for activity_label in [event[activity_key]] + sample(label_set - {event[activity_key]}, to_add)}
                else:
                    event[u_activity_key]['children'].update({activity_label: 0 for activity_label in [event[activity_key]] + sample(label_set - {event[activity_key]}, to_add)})


def add_uncertain_activities_to_trace(p: float, 
        trace: Trace,  
        max_labels_to_add:int =1, label_set=None, 
        activity_key:str= DEFAULT_NAME_KEY,                                       u_activity_key:str=DEFAULT_U_NAME_KEY,
        add_probability_values: bool = True,
        ):
    
    """
    Adds uncertain activity labels to exactly p percent of the events in the trace,
    ensuring that uncertainty is not added more than once to the same event.
   
    :param trace: The trace (list of events)
    :param p: Probability (percentage) of events to modify
    :param max_labels_to_add: Maximum number of uncertain activity labels to add
    :param label_set: Set of possible activity labels to choose from
    :param activity_key: Key for the activity label in the trace events
    :param u_activity_key: Key for the uncertain activity in the trace events
    :param add_probability_values: If True, assigns random probabilities; otherwise, assigns equal probabilities
    :return: None (modifies the trace in place)
    """

    if not 0<= p <=1:
        raise ValueError('Probability p must be between 0 and 1.')

    if p > 0.0:
        if label_set is None:
            label_set = set(event[activity_key] for event in trace)
        
        labels_to_add = min(max_labels_to_add, len(label_set) - 1)

        # Filter out events that already have uncertain activity labels
        available_events = [event for event in trace if u_activity_key not in event]
    
        # Determine the exact number of events to modify based on p
        num_events_to_modify = (round(len(trace) * p))

        # Ensure we only sample from available events that haven't been modified yet
        # If there are fewer available events than the number to be modified
        if len(available_events) < num_events_to_modify:
            # Warn the user if fewer than p% of events can be modified
            warn(f"Cannot modify exactly {p*100}% of the events. Only {len(available_events)} events available for modification.")
            events_to_modify = available_events
        else:
            # Otherwise, sample exactly the number of events needed
            events_to_modify = sample(available_events, num_events_to_modify)  
  
    
        for event in events_to_modify:          
            event[u_activity_key] = dict()
            current_activity_label = event[activity_key]
            additional_labels = sample(list(label_set - {current_activity_label}), labels_to_add)                         
            # Assign probabilities
            if add_probability_values:
                uniform_probs = [uniform(0.0001, 0.9999) for _ in range(labels_to_add + 1)]
                normalized_probs = [prob / sum(uniform_probs) for prob in uniform_probs]
            else:
                normalized_probs = [1 / (labels_to_add + 1)] * (labels_to_add + 1)
            # Assign the uncertain activity labels with probabilities
            children_dict = {label: prob for label, prob in zip([current_activity_label] + additional_labels, normalized_probs)}
            event[u_activity_key]['children'] = children_dict

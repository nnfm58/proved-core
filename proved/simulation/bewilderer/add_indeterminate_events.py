from random import random, sample, uniform
from warnings import warn

from pm4py.objects.log.obj import Trace

from proved.xes_keys import DEFAULT_U_MISSING_KEY



def add_indeterminate_events_to_log(p, log=None, log_map=None, u_missing_key=DEFAULT_U_MISSING_KEY):
    """
    Turns events in an trace into indeterminate events with a certain probability.

    :param trace: the trace
    :param p: the probability of indeterminate events
    :param u_missing_key: the xes key for indeterminate events
    :return:
    """

    if p > 0.0:

        if log_map is None:
            if log is None:
                raise ValueError('Parameters log and log_map cannot both be None.')
            else:
                log_map = {}
                i = 0
                for trace in log:
                    for j in range(len(trace)):
                        log_map[i] = (trace, j)
                        i += 1

        to_add = max(0, round(len(log_map) * p))
        indices_to_add = sample(frozenset(log_map), to_add)
        for i in indices_to_add:
            trace, j = log_map[i]
            trace[j][u_missing_key] = 1


def add_indeterminate_events_to_log_montecarlo(log, p, u_missing_key=DEFAULT_U_MISSING_KEY):
    """
    Turns events in an event log into indeterminate events with a certain probability.

    :param log: the event log
    :param p: the probability of indeterminate events
    :param u_missing_key: the xes key for indeterminate events
    :return:
    """

    if p > 0.0:
        for trace in log:
            add_indeterminate_events_to_trace_montecarlo(trace, p, u_missing_key)


def add_indeterminate_events_to_trace_montecarlo(trace, p, u_missing_key=DEFAULT_U_MISSING_KEY):
    """
    Turns events in an trace into indeterminate events with a certain probability.

    :param trace: the trace
    :param p: the probability of indeterminate events
    :param u_missing_key: the xes key for indeterminate events
    :return:
    """

    if p > 0.0:
        for event in trace:
            if random() < p:
                event[u_missing_key] = 1



def add_indeterminate_events_to_trace(p: float, 
        trace: Trace,  
        add_probability_values: bool = True, 
        u_missing_key: str = DEFAULT_U_MISSING_KEY):
    """
    Adds indeterminate events (represented by a probability) to exactly p percent of the events in the trace. Ensures indeterminate uncertainty is not added to the same event more than once.
    
    :param trace: The trace (list of events)
    :param p: Probability (percentage) of events to modify
    :param add_probability_values: If True, assigns random probability; if False, assigns 0.5
    :param u_missing_key: The key used to represent indeterminate events
    :return: None (modifies the trace in place)
    """
    # Ensure the probability is valid
    if not 0 <= p <= 1:
        raise ValueError('Probability p must be between 0 and 1.')

    if p > 0.0:
        # Filter out events that already have indeterminate uncertainty
        available_events = [event for event in trace if u_missing_key not in event]
        
        # Calculate the number of events to modify based on p (p% of total trace size)
        total_events = len(trace)
        num_events_to_modify = max(1, round(total_events * p))
        
        # Check if there are fewer available events than needed
        if len(available_events) < num_events_to_modify:
            # Warn the user if fewer than p% of events can be modified
            warn(f"Cannot modify exactly {p*100}% of the events. Only {len(available_events)} events available for modification.")
            # Modify all available events
            events_to_modify = available_events
        else:
            # Otherwise, sample exactly the number of events needed
            events_to_modify = sample(available_events, num_events_to_modify)
        
        for event in events_to_modify:
            if add_probability_values:
                # Assign a random probability value drawn from a uniform distribution
                event[u_missing_key] = uniform(0.00001, 0.99999)
            else:
                # Assign equal probability value to both scenarios
                event[u_missing_key] = 0.5

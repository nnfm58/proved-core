from copy import copy
from datetime import timedelta, datetime
from random import random, sample
from warnings import warn

from pm4py.objects.log.obj import Trace
from pm4py.objects.log.util.xes import DEFAULT_TIMESTAMP_KEY

from proved.xes_keys import DEFAULT_U_TIMESTAMP_MIN_KEY, DEFAULT_U_TIMESTAMP_MAX_KEY


def add_uncertain_timestamp_to_log(p, log=None, log_map=None, timestamp_key=DEFAULT_TIMESTAMP_KEY, u_timestamp_min_key=DEFAULT_U_TIMESTAMP_MIN_KEY, u_timestamp_max_key=DEFAULT_U_TIMESTAMP_MAX_KEY):
    """
    Adds possible activity labels to events in a trace with a certain probability, up to a maximum.

    :param trace: the trace
    :param p: the probability of overlapping timestamps with previous events
    :param p_right: the probability of overlapping timestamps with successive events
    :param max_overlap_left: the maximum number of events that a timestamp can overlap
    :param max_overlap_right: the maximum number of events that a timestamp can overlap
    :param timestamp_key: the xes key for the timestamp
    :param u_timestamp_min_key: the xes key for the minimum value of an uncertain timestamp
    :param u_timestamp_max_key: the xes key for the maximum value of an uncertain timestamp
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

        to_alter = max(0, round(len(log_map) * p))
        indices_to_alter = sample(frozenset(log_map), to_alter)
        for i in indices_to_alter:
            trace, j = log_map[i]
            # trace[j][u_timestamp_min_key] = copy(min(trace[j][timestamp_key], trace[max(j - 1, 0)][timestamp_key])) - timedelta(milliseconds=100)
            # trace[j][u_timestamp_max_key] = copy(max(trace[j][timestamp_key], trace[min(j + 1, len(trace) - 1)][timestamp_key])) + timedelta(milliseconds=100)
            # If the event is the first in the trace, we alter the timestamp to overlap the following event. If the event is the last in the trace, we alter the
            # timestamp to overlap the previous. In any other case, we pick either one at random.
            if j == 0 or (j != len(trace) - 1 and random() < .5):
                trace[j][u_timestamp_min_key] = copy(trace[j][timestamp_key]) - timedelta(milliseconds=100)
                trace[j][u_timestamp_max_key] = copy(max(trace[j][timestamp_key], trace[min(j + 1, len(trace) - 1)][timestamp_key])) + timedelta(milliseconds=100)
            else:
                trace[j][u_timestamp_min_key] = copy(min(trace[j][timestamp_key], trace[max(j - 1, 0)][timestamp_key])) - timedelta(milliseconds=100)
                trace[j][u_timestamp_max_key] = copy(trace[j][timestamp_key]) + timedelta(milliseconds=100)


def add_uncertain_timestamp_to_log_montecarlo(log, p_left, p_right, max_overlap_left=0, max_overlap_right=0, timestamp_key=DEFAULT_TIMESTAMP_KEY, u_timestamp_min_key=DEFAULT_U_TIMESTAMP_MIN_KEY, u_timestamp_max_key=DEFAULT_U_TIMESTAMP_MAX_KEY):
    """
    Adds possible activity labels to events in an event log with a certain probability, up to a maximum.

    :param log: the event log
    :param p_left: the probability of overlapping timestamps with previous events
    :param p_right: the probability of overlapping timestamps with successive events
    :param max_overlap_left: the maximum number of events that a timestamp can overlap
    :param max_overlap_right: the maximum number of events that a timestamp can overlap
    :param timestamp_key: the xes key for the timestamp
    :param u_timestamp_min_key: the xes key for the minimum value of an uncertain timestamp
    :param u_timestamp_max_key: the xes key for the maximum value of an uncertain timestamp
    :return:
    """

    if p_left > 0.0 or p_right > 0.0:
        for trace in log:
            add_uncertain_timestamp_to_trace_montecarlo(trace, p_left, p_right, max_overlap_left, max_overlap_right, timestamp_key, u_timestamp_min_key, u_timestamp_max_key)


def add_uncertain_timestamp_to_trace_montecarlo(trace, p_left, p_right, max_overlap_left=0, max_overlap_right=0, timestamp_key=DEFAULT_TIMESTAMP_KEY, u_timestamp_min_key=DEFAULT_U_TIMESTAMP_MIN_KEY, u_timestamp_max_key=DEFAULT_U_TIMESTAMP_MAX_KEY):
    """
    Adds possible activity labels to events in a trace with a certain probability, up to a maximum.

    :param trace: the trace
    :param p_left: the probability of overlapping timestamps with previous events
    :param p_right: the probability of overlapping timestamps with successive events
    :param max_overlap_left: the maximum number of events that a timestamp can overlap
    :param max_overlap_right: the maximum number of events that a timestamp can overlap
    :param timestamp_key: the xes key for the timestamp
    :param u_timestamp_min_key: the xes key for the minimum value of an uncertain timestamp
    :param u_timestamp_max_key: the xes key for the maximum value of an uncertain timestamp
    :return:
    """

    if p_left > 0.0 or p_right > 0.0:
        for i in range(len(trace)):
            steps_left = 0
            steps_right = 0
            while random() < p_left and steps_left < min(max_overlap_left, i):
                steps_left += 1
            while random() < p_right and steps_right < min(max_overlap_right, len(trace) - i - 1):
                steps_right += 1
            # (Partially) supports events that already have uncertainty on timestamps
            # This might cause problems on events for which 'u_timestamp_min_key' <= 'timestamp_key' <= 'u_timestamp_max_key'
            if u_timestamp_max_key in trace[i - steps_left]:
                if u_timestamp_min_key in trace[i]:
                    trace[i][u_timestamp_min_key] = copy(min(trace[i][u_timestamp_min_key], trace[i - steps_left][u_timestamp_max_key]))
                else:
                    trace[i][u_timestamp_min_key] = copy(min(trace[i][timestamp_key], trace[i - steps_left][u_timestamp_max_key]))
            else:
                if u_timestamp_min_key in trace[i]:
                    trace[i][u_timestamp_min_key] = copy(min(trace[i][u_timestamp_min_key], trace[i - steps_left][timestamp_key]))
                else:
                    trace[i][u_timestamp_min_key] = copy(min(trace[i][timestamp_key], trace[i - steps_left][timestamp_key]))
            if u_timestamp_min_key in trace[i + steps_right]:
                if u_timestamp_max_key in trace[i]:
                    trace[i][u_timestamp_max_key] = copy(max(trace[i][u_timestamp_max_key], trace[i + steps_right][u_timestamp_min_key]))
                else:
                    trace[i][u_timestamp_max_key] = copy(max(trace[i][timestamp_key], trace[i + steps_right][u_timestamp_min_key]))
            else:
                if u_timestamp_max_key in trace[i]:
                    trace[i][u_timestamp_max_key] = copy(max(trace[i][u_timestamp_max_key], trace[i + steps_right][timestamp_key]))
                else:
                    trace[i][u_timestamp_max_key] = copy(max(trace[i][timestamp_key], trace[i + steps_right][timestamp_key]))



def str_to_datetime(timestamp):
    """Helper function to convert string to datetime if necessary"""
    if isinstance(timestamp, str):
        return datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    return timestamp

def add_uncertain_timestamp_to_trace(
        p: float,
        trace: Trace, 
        timestamp_key: str = DEFAULT_TIMESTAMP_KEY, 
        u_timestamp_min_key: str = DEFAULT_U_TIMESTAMP_MIN_KEY,
        u_timestamp_max_key: str = DEFAULT_U_TIMESTAMP_MAX_KEY):
    """
    Adds timestamp uncertainty to events in a trace with a certain probability.
    Handles both string and datetime formats for timestamps.
    
    :param trace: The trace (list of events)
    :param p: The probability of modifying timestamps with uncertainty
    :param timestamp_key: The key for the event's timestamp
    :param u_timestamp_min_key: The key for the minimum value of an uncertain timestamp
    :param u_timestamp_max_key: The key for the maximum value of an uncertain timestamp
    :raises ValueError: if p is not in the range [0, 1]
    :return:
    """
    if not 0 <= p <= 1:
        raise ValueError('Probability p must be between 0 and 1.')
    
    if p > 0.0:
        available_indices = [i for i in range(len(trace)) if u_timestamp_min_key not in trace[i] and u_timestamp_max_key not in trace[i]]
        num_events_to_modify = max(1, round(len(available_indices) * p))
        
        # Check if there are fewer available events than needed
        if len(available_indices) < num_events_to_modify:
            warn(f"Cannot modify exactly {p*100}% of the available events. Only {len(available_indices)} events available for modification.")
            indices_to_alter = available_indices  # Modify all available events
        else:
            indices_to_alter = sample(available_indices, num_events_to_modify)

        # Alter selected events by adding uncertainty in timestamp
        for i in indices_to_alter:
            event = trace[i]
            event_timestamp = str_to_datetime(event[timestamp_key])  # Convert if necessary
            
            # If the event is the first in the trace, alter the timestamp to overlap the following event
            # If the event is the last, overlap with the previous event
            # Otherwise, randomly overlap with the previous or next event
            if i == 0 or (i != len(trace) - 1 and random() < 0.5):
                event[u_timestamp_min_key] = copy(event_timestamp) - timedelta(milliseconds=100)
                event[u_timestamp_max_key] = copy(max(event_timestamp, str_to_datetime(trace[min(i + 1, len(trace) - 1)][timestamp_key]))) + timedelta(milliseconds=100)
            else:
                event[u_timestamp_min_key] = copy(min(event_timestamp, str_to_datetime(trace[max(i - 1, 0)][timestamp_key]))) - timedelta(milliseconds=100)
                event[u_timestamp_max_key] = copy(event_timestamp) + timedelta(milliseconds=100)

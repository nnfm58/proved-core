from typing import List


from pm4py.objects import petri_net
from pm4py.objects.log.obj import Trace, Event
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.util.xes_constants import DEFAULT_NAME_KEY


def acyclic_net_variants(net: PetriNet, 
    initial_marking: Marking,                                    
    final_marking: Marking,
    activity_key: str = DEFAULT_NAME_KEY,
    uncertainty_dict_key: str = "uncertainty_dict") -> List[Trace]:
    """
    Given an acyclic accepting Petri net, initial and final marking extracts a set of variants (in form of traces) replayable on the net. If add_probability is True the trace probability will be calculated and added as a trace atrribute.

    Warning: this function is based on a marking exploration. If the accepting Petri net contains loops, the method will not work properly as it stops the search if a specific marking has already been encountered.

    :param net: An acyclic workflow net.
    :param initial_marking: The initial marking of the net.
    :param final_marking: The final marking of the net.
    :param activity_key: The key used to store activity labels in the trace events.
    :param trace_probability_key: The key used to store trace probability.
    :param uncertainty_dict_key: The key used to store uncertainty information.
    :return: variants: :class:`list` Set of variants - in the form of Trace objects - obtainable executing the net.
    """


    def explore_marking(curr_marking: Marking, 
            curr_partial_trace: List[Event]) -> None:
        """
        Recursive function to explore the variants from a given marking.

        :param curr_marking: The current marking in the exploration.
        :param curr_partial_trace: The current partial trace formed up to this point.
        :param curr_prob: The cumulative probability of the current partial trace.
        """
        if hash(curr_marking) == hash_final_marking:
            new_trace = Trace(curr_partial_trace)
            trace_realizations.append(new_trace)
            return

        hash_curr_pair = hash((curr_marking, tuple(curr_partial_trace)))
        if hash_curr_pair in visited:
            return

        visited.add(hash_curr_pair)
        enabled_transitions = petri_net.semantics.enabled_transitions(net, curr_marking)

        for transition in enabled_transitions:
            next_marking = petri_net.semantics.execute(transition, net, curr_marking)
            uncertainty_info = net.uncertainty_dict.get(transition, {})
            if transition.name not in ('t_source', 't_sink'):
                next_event = Event({activity_key: transition.label})
                next_event[uncertainty_dict_key] = uncertainty_info

                explore_marking(next_marking, curr_partial_trace + [next_event])
            else:
                explore_marking(next_marking, curr_partial_trace)

    hash_final_marking = hash(final_marking)
    visited = set() # Tracks visited markings and partial traces
    trace_realizations = []
    # Start the exploration from the initial marking
    explore_marking(initial_marking, []) 

    return trace_realizations




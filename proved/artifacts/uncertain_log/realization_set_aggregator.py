from collections import defaultdict
from typing import List, Dict, Tuple

from pm4py.objects.log.obj import Event, Trace
from pm4py.util.xes_constants import DEFAULT_NAME_KEY


def get_unique_realizations(
        trace_realizations: List[Trace],
        add_probability: bool = False,
        activity_key: str = DEFAULT_NAME_KEY,
        trace_probability_key: str = "trace_probability",
    )-> List['Trace']:
    """
    Returns the list of unique realizations of uncertain traces along with their respective probabilities.
    
    :param trace_realizations: List of trace realizations to process.
    :param add_probability: Flag to indicate if probabilities should be aggregated.
    :param activity_key: Key to access the activity label in each event.
    :param trace_probability_key: Key to access the trace probability in the attributes.
    :return: List of unique trace realizations with their probabilities if applicable.
    """
    # Dictionary to store unique sequences with their aggregated probabilities
    unique_sequences: Dict[Tuple[str, ...], float] = defaultdict(float)

    for realization in trace_realizations:
        # Create a representation of the sequence
        sequence_repr = tuple(event[activity_key] for event in realization if event[activity_key] is not None)
        
        # Aggregate probabilities
        unique_sequences[sequence_repr] += realization.attributes.get(trace_probability_key, 1) if add_probability else 0

    # Reconstruct the unique realization set
    unique_realization_set = []
    for seq, prob in unique_sequences.items():
        unique_variant = Trace()
        for event in seq:
            unique_variant.append(Event({activity_key: event}))
        if add_probability:    
            unique_variant.attributes[trace_probability_key] = prob
        unique_realization_set.append(unique_variant)
    
    return unique_realization_set

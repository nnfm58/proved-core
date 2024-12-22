"""
Module: Trace Probability Calculation

This module provides functions to calculate the probability of a sequence of uncertain events.
It constructs probability distribution functions (PDFs) for each event in the Trace, and integrates these PDFs to compute the probability of the entire sequence.

Functions:
- construct_uniform_pdf: Constructs a uniform PDF.
- construct_normal_pdf: Constructs a normal PDF.
- construct_dirac_pdf: Constructs an approximation of a Dirac delta function (for deterministic events).
- construct_event: Constructs event objects based on the type.
- process_event_seq: Processes an event sequence and normalizes timestamps.
- get_integrand: Gets the integrand function for probability calculation.
- bound_func: Determines the integral bounds for each PDF.
- bounds_proper: Sets bounds for integration.
- probability: Calculates n-dimensional integral for the given PDFs and bounds.
- calculate_probability: Main function to calculate probability of an event sequence.
"""

import sys
import scipy
from scipy.integrate import nquad
from typing import Callable, List, Dict

from pm4py.util.xes_constants import DEFAULT_TIMESTAMP_KEY

import proved.xes_keys as xes_keys
from pm4py.objects.log.obj import Trace


def construct_uniform_pdf(lower: float, upper: float) -> Callable:
    """Constructs a uniform probability distribution function."""
    def p(x: float) -> float:
        return 1 / (upper - lower) if lower <= x <= upper else 0
    return p


def construct_normal_pdf(mean: float, std: float) -> Callable:
    """Constructs a normal probability distribution function."""
    return lambda x: scipy.stats.norm.pdf(x, loc=mean, scale=std)


def construct_dirac_pdf(timestamp, delta=1e-4)-> Callable:
    """ Constructs an approximation of a Dirac delta function for deterministic events."""
    def p(x):
        if timestamp - delta <= x <= timestamp + delta:
            return 1 / (2 * delta)
        return 0
    return p 


def construct_event(
        event_type: str, 
        lower: float, 
        upper: float, 
        mean: float = None, 
        std: float = None, 
        delta: float = 1e-4
    ) -> Dict:

    """
    Constructs event objects based on the type (uniform, normal, or deterministic).

    :param event_type: The type of event ('uniform', 'normal', 'deterministic').
    :param lower: The lower bound of the event time.
    :param upper: The upper bound of the event time.
    :param mean: The mean (mu) for normal distribution.
    :param std: The standard deviation (sigma) for normal distribution.
    :param delta: The range for the Dirac delta function approximation.
    :return: A dictionary representing the constructed event.
    """

    if event_type == 'uniform':
        return {
            "p": construct_uniform_pdf(lower, upper),
            "lower": lower,
            "upper": upper
        }
    elif event_type == 'normal':
        return {
            "p": construct_normal_pdf(mean, std),
            "lower": mean - 4 * std,
            "upper": mean + 4 * std
        }
    elif event_type == 'deterministic':
        return {
            "p": construct_dirac_pdf(lower, delta),
            "lower": lower,
            "upper": upper
        }
    

def process_event_seq(
        sigma: List[Dict], 
        uncertainty_dict_key: str = "uncertainty_dict",
        u_timestamp_min_key: str = xes_keys.DEFAULT_U_TIMESTAMP_MIN_KEY,
        u_timestamp_max_key: str = xes_keys.DEFAULT_U_TIMESTAMP_MAX_KEY,
        timestamp_key: str = DEFAULT_TIMESTAMP_KEY,
        delta: float = 1e-6
    ) -> List[Dict]:

    """Processes an event sequence, normalizes timestamps, and constructs event objects.
    
    :param sigma: The sequence of events.
    :param uncertainty_dict_key: The key in the event dict where uncertainty data is stored.
    :param u_timestamp_min_key: The key for the minimum timestamp in the uncertainty data.
    :param u_timestamp_max_key: The key for the maximum timestamp in the uncertainty data.
    :param timestamp_key: The key for the timestamp in the event dict.
    :param delta: The range for the Dirac delta function approximation.
    :return: A list of normalized event objects.
    """

    event_objects = []  # Store event objects here
    min_timestamp = float('inf')  # Initialize to infinity

    # Iterate through events, construct event objects, and find min timestamp
    for event in sigma:
        event_info = event.get(uncertainty_dict_key, {})

        if u_timestamp_min_key in event_info and u_timestamp_max_key in event_info:
            # Uncertain event with min and max timestamps
            u_timestamp_min = event_info[u_timestamp_min_key].timestamp()
            u_timestamp_max = event_info[u_timestamp_max_key].timestamp()
            min_timestamp = min(min_timestamp, u_timestamp_min)  # Update min timestamp
            event_objects.append({'lower': u_timestamp_min, 'upper': u_timestamp_max, 'type': 'uniform'})
        else:
            # Deterministic event
            timestamp = event_info[timestamp_key].timestamp()
            min_timestamp = min(min_timestamp, timestamp)  # Update min timestamp
            event_objects.append({'lower': timestamp, 'upper': timestamp, 'type': 'deterministic'})

    # Normalize timestamps and create event_uniform or event_deterministic objects
    normalized_events = []
    for event_obj in event_objects:
        lower1 = round(event_obj['lower'] - min_timestamp,3)
        upper1 = round(event_obj['upper'] - min_timestamp,3)

        lower = event_obj['lower']
        upper = event_obj['upper']

        if event_obj['type'] == 'uniform':
            normalized_events.append(construct_event('uniform', lower1, upper1))
        if event_obj['type'] == 'deterministic':
            normalized_events.append(construct_event('deterministic', lower1, upper1, delta=delta))

    return normalized_events


def get_integrand(*pdfs: List[Callable]) -> Callable:
    """
    Gets the integrand for n-dimensional integration based on the provided probability density functions (PDFs).

    :param pdfs: A list of PDFs for the events.
    :return: A function representing the product of PDFs, to be used as an integrand.
    """
    def p_product(*xs: float) -> float:
        result = 1
        if len(xs) != len(pdfs):
            print("not the same amount of variables as pdfs")
        for pdf, xi in zip(pdfs, xs):
            result *= pdf(xi)
            
        return result

    return p_product


def bound_func(i: int, tmins: List[float], tmaxs: List[float]) -> Callable:
    
    """
    Determines the integral bounds of the i-th PDF, given the lists of minimal and maximal timestamps of all events

    :param i: The index of the current integral.
    :param tmins: The list of minimal timestamps for the events.
    :param tmaxs: The list of maximal timestamps for the events.
    :return: A function that provides the integration bounds for the i-th integral.
    """
    def bound_func_inner(*xs):
        upper_bound = min(tmaxs[i:])

        if len(xs) > 0:
            lower_bound = max(tmins[i], xs[0])
        else:
            lower_bound = tmins[i]

        return lower_bound, upper_bound
    return bound_func_inner


def bounds_proper(tmins, tmaxs):
    """
    Returns a sequence of functions that return integration bounds for each dimension.
    The first element gives bounds for the innermost integral, and can depend on all other integration variables.
    The last element gives bounds for the outermost integral.
    The tmins and tmaxs are in the order outermost integral to innermost integral.

    :param tmins: The list of minimal timestamps for the events.
    :param tmaxs: The list of maximal timestamps for the events.
    :return: A list of functions, each returning the integration bounds for the corresponding integral.
    """

    num_integrals = len(tmins)
    # count the integrals from outermost (0) to innermost (num_integrals - 1)
    bounds = []
    for i in range(num_integrals):
        bounds.insert(0, bound_func(i, tmins, tmaxs))

    return bounds


def probability(pdfs: List[Callable], tmins: List[float], tmaxs: List[float]
    ) -> float:
    """
    Calculates the n-dimensional integral over the given probability density functions (PDFs) within the specified bounds.
    
    :param pdfs: A list of PDFs for the events where the i-th function gives the pdf of the i-th interval.
    :param tmins, tmaxs: A List of floats where the i-th float is the lower / upper bound of the i-th interval
    :return: The calculated area under the curve, representing the probability.
    """
    integrand = get_integrand(*pdfs)
    bounds = bounds_proper(tmins, tmaxs) # bounds_for_scipy(tmins, tmaxs)

    # Define options for nquad
    options = {
    'limit': 5,  # The iteration limit
    'epsabs': 1e-3,  # Absolute error tolerance
    'epsrel': 1e-3,  # Relative error tolerance
    }
    area = nquad(integrand, bounds, opts=options)
    return area


def calculate_integral(sigma: List[Dict]) -> float:
    """
    Main function to calculate the probability of the given sequence of events (sigma).

    :param sigma: The sequence of events.
    :return: The calculated probability of the sequence.
    """
    events = process_event_seq(sigma)
    probs = [event["p"] for event in events]
    tmins = [event["lower"] for event in events]
    tmaxs = [event["upper"] for event in events]

    probs.reverse()  # reverse due to how nquad works
    return probability(probs, tmins, tmaxs)


def calculate_realizations_probabilities(
        trace_realizations: List[Trace], 
        u_missing_key: str = xes_keys.DEFAULT_U_MISSING_KEY,
        u_timestamp_min_key: str = xes_keys.DEFAULT_U_TIMESTAMP_MIN_KEY,
        u_timestamp_max_key: str = xes_keys.DEFAULT_U_TIMESTAMP_MAX_KEY,
        u_activity_key: str = xes_keys.DEFAULT_U_NAME_KEY,
        trace_probability_key: str = "trace_probability",
        uncertainty_dict_key: str = "uncertainty_dict") -> float :
    """
    Calculate P(sigma | tau) for a given realization and trace.
    """
    def calculate_PO(sigma):
        """
        Calculate P_O(rho | tau) for a given realization.
        """
        P_missing = calculate_P_missing(sigma)
        if any(u_timestamp_min_key in event[uncertainty_dict_key] for event in sigma):
            I_rho, error = calculate_integral(sigma)
            return I_rho * P_missing

        else: return P_missing


    def calculate_PA(sigma):
        """
        Calculate P_A(sigma | rho) for a given realization.
        """
        PA_sigma_rho = 1
        for event in sigma:
            uncertainty_info = event.get(uncertainty_dict_key, {})
            # Multiply probabilities of each event's activity label
            if u_activity_key in uncertainty_info:
                activity_probability = uncertainty_info[u_activity_key]
                PA_sigma_rho *= activity_probability
        return PA_sigma_rho


    def calculate_P_missing(sigma):
        """
        Calculate the probability for missing events on a given realization.
        """
        P_missing = 1
        for event in sigma:
            uncertainty_info = event.get(uncertainty_dict_key, {})
            if u_missing_key in uncertainty_info:
            # If there are missing values, we need to account for that when calculating PO  
                missing_probability = uncertainty_info[u_missing_key]
                P_missing *= missing_probability
        return P_missing
    

    for trace in trace_realizations:
        PO = calculate_PO(trace)
        PA = calculate_PA(trace)
        trace.attributes[trace_probability_key] = PO * PA

    return
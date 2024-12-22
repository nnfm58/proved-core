from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils


class BehaviorNet(PetriNet):
    """
    Class that represents a behavior net, a sound workflow Petri net that can replay all realizations of an uncertain trace.
    For more information refer to:
        Pegoraro, Marco, and Wil MP van der Aalst. "Mining uncertain event data in process mining." 2019 International Conference on Process Mining (ICPM). IEEE, 2019.
    """

    def __init__(self, behavior_graph):
        PetriNet.__init__(self)

        # Creating sink and source place, and invisible transitions connecting them to the rest of the net
        source_place = PetriNet.Place('source')
        self.places.add(source_place)
        source_trans = PetriNet.Transition('t_source', None)
        self.transitions.add(source_trans)
        petri_utils.add_arc_from_to(source_place, source_trans, self)

        sink_place = PetriNet.Place('sink')
        self.places.add(sink_place)
        sink_trans = PetriNet.Transition('t_sink', None)
        self.transitions.add(sink_trans)
        petri_utils.add_arc_from_to(sink_trans, sink_place, self)

        # Creating transitions for each node in the graph
        node_trans = {}  
        self.uncertainty_dict = {}
        for node, attrs in behavior_graph.nodes(data=True):
            node_id, labels = node
            #TODO add a xsd default key
            node_dict = attrs.get('u_dict', {})
            transition_set = set()

            for label in labels:
                transition_label = f"t{node_id}_{label if label is not None else 'None'}"
                transition = PetriNet.Transition(transition_label, label)
                self.transitions.add(transition)
                transition_set.add(transition)
                # Add uncertainty info to events
                if label is None:
                    # Special handling for missing events
                    self.uncertainty_dict[transition] = node_dict.get('None', {})
                else:
                    self.uncertainty_dict[transition] = node_dict.get(label, {})

            node_trans[node_id] = transition_set

        for node_from_id, node_from_labels in behavior_graph.nodes:
            transitions_from = node_trans[node_from_id]
           
           # Each activity that can start the trace have to be connected through an AND-split to the starting invisible transition
            if not list(behavior_graph.predecessors((node_from_id, node_from_labels))):
                place_from_source = PetriNet.Place(f'source_to_{node_from_id}')
                self.places.add(place_from_source)
                petri_utils.add_arc_from_to(source_trans, place_from_source, self)
                for transition in transitions_from:
                    petri_utils.add_arc_from_to(place_from_source, transition, self)

            # Every arc in the behavior graph is translated to a place in the behavior net, describing the precedence relationship between nodes
            # For each successor of the current node, all the transitions of the current node are connected to all the transitions in the successor through a place
            for node_to_id, node_to_labels in behavior_graph.successors((node_from_id, node_from_labels)):
                transitions_to = node_trans[node_to_id]
                place_between = PetriNet.Place(f'{node_from_id}_to_{node_to_id}')
                self.places.add(place_between)

                for transition_from in transitions_from:
                    petri_utils.add_arc_from_to(transition_from, place_between, self)
                for transition_to in transitions_to:
                    petri_utils.add_arc_from_to(place_between, transition_to, self)
            # Each activity that can end the trace have to be connected through an AND-join to the ending invisible transition
            if not list(behavior_graph.successors((node_from_id, node_from_labels))):
                place_to_sink = PetriNet.Place(f'{node_from_id}_to_sink')
                self.places.add(place_to_sink)
                petri_utils.add_arc_from_to(place_to_sink, sink_trans, self)
                for transition in transitions_from:
                    petri_utils.add_arc_from_to(transition, place_to_sink, self)
        # Initial and final markings are just one token in the source place and one token in the sink place, respectively
        self.initial_marking = Marking({source_place: 1})
        self.final_marking = Marking({sink_place: 1})


    def __set_initial_marking(self, initial_marking):
        self.__initial_marking = initial_marking

    def __get_initial_marking(self):
        return self.__initial_marking

    def __set_final_marking(self, final_marking):
        self.__final_marking = final_marking

    def __get_final_marking(self):
        return self.__final_marking

    initial_marking = property(__get_initial_marking, __set_initial_marking)
    final_marking = property(__get_final_marking, __set_final_marking)



import copy
import numpy as np

from functools import wraps
from chatbotQuery import ChatbotMessage
from chatbotQuery.io import chooser_io, parse_parameter_functions


def formatting_store_detection(func):
    @wraps(func)
    def function_wrapped(*args, **kwargs):
        ## Getting the message from inputs
        if len(args) >= 2:
            answer = args[1]
        else:
            answer = kwargs['message']
        ##
        assert(isinstance(answer, ChatbotMessage))
        ## Detection process
        selector_types = func(*args, **kwargs)
        ## Store results in message
        answer = answer.add_selector_types(selector_types)
        return answer
    return function_wrapped


def formatting_base_response(func):
    @wraps(func)
    def function_wrapped(*args, **kwargs):
        ## Getting the message from inputs
        if len(args) >= 2:
            message = args[1]
        else:
            message = kwargs['message']
        ## Selection process from database of possible messages
        selected_message = func(*args, **kwargs)
        ## Build output message
        output_message = message.collapse_message(selected_message)
        output_message.check_message()
        output_message = output_message.reflect_metadata(message)

#        if 'query' in message:
#            output_message['query'] = message['query']
        return output_message

    return function_wrapped


################################## Detection ##################################
###############################################################################
class BaseDetector(object):

    def __init__(self, pos_types=None, detector=None):
        if pos_types is None:
            assert(detector is None)
            self.pos_types = []
            self.detector = lambda x: ()
        else:
            assert(callable(detector))
            self.pos_types = pos_types
            self.detector = detector

    @classmethod
    def from_detector_info(cls, detector_info):
        if detector_info is None:
            return cls()
        elif type(detector_info) in [list, tuple]:
            return cls(*detector_info)
        elif type(detector_info) == dict:
            pos_types = detector_info['pos_types']
            detector_f =\
                parse_parameter_functions(detector_info['detector_function'])
            return cls(pos_types=pos_types, detector=detector_f)
        else:
            assert(isinstance(detector_info, BaseDetector))
            return cls(pos_types=detector_info.pos_types,
                       detector=detector_info.detector)

    @formatting_store_detection
    def detect(self, answer):
        probabilities = self.detector(answer)
        assert(len(probabilities) == len(self.pos_types))
        selector_types = dict(zip(self.pos_types, probabilities))
        return selector_types


################################### Querier ###################################
###############################################################################
class BaseQuerier(object):

    def __init__(self, querier):
        assert(callable(querier))
        self.querier = querier

    @classmethod
    def from_querier_info(cls, querier_info):
        if querier_info is None:
            return NullQuerier()
        elif callable(querier_info):
            return cls(querier_info)
        elif type(querier_info) == dict:
            querier_f =\
                parse_parameter_functions(querier_info['querier_function'])
            return cls(querier=querier_f)
        else:
            assert(isinstance(querier_info, BaseQuerier))
            return querier_info

    def make_query(self, handler_db, message):
        query_message = self.querier(handler_db, message)
        if isinstance(query_message, dict):
            if 'query' in query_message:
                message.update(query_message)
        else:
            if query_message is not None:
                message['query'] = query_message
        return message


class NullQuerier(BaseQuerier):

    def __init__(self):
        def null_querier(handler_db, message):
            return None
        super().__init__(null_querier)


################################### Chooser ###################################
###############################################################################
class BaseChooser(object):

    @formatting_base_response
    def choose(self, message=None):
        message = self.candidates[(self.times_used % len(self.candidates))]
        self.times_used += 1
        return message

    @classmethod
    def from_chooser_info(cls, chooser_info):
        if chooser_info is None:
            return NullChooser()
        elif type(chooser_info) in [list, tuple]:
            return RandomChooser(chooser_info)
        elif type(chooser_info) == dict:
            if 'chooser_object' in chooser_info:
                obj = eval(chooser_info['chooser_object'])
            else:
                obj = cls
            pars = obj._preparation_parameters(chooser_info)
            return obj(**pars)
        else:
            assert(isinstance(chooser_info, BaseChooser))
            obj = copy.copy(chooser_info)
            obj.times_used = 0
            return obj

    def _parse_candidate_messages(self, candidate_messages):
        if type(candidate_messages) != list:
            candidate_messages = chooser_io(candidate_messages)
        self.candidates = [ChatbotMessage.from_candidates_messages(r)
                           for r in candidate_messages]


class NullChooser(BaseChooser):
    """Avoid to take a decision and pass a message as it arrives to it."""

    def __init__(self):
        self.candidates = []
        self.times_used = 0

    @classmethod
    def _preparation_parameters(cls, parameters):
        return {}

    def choose(self, message):
        return message


class RandomChooser(BaseChooser):

    def __init__(self, candidate_messages):
        self._parse_candidate_messages(candidate_messages)
        self.times_used = 0

    @classmethod
    def _preparation_parameters(cls, parameters):
        candidate_messages = chooser_io(parameters['filepath'])
        return {'candidate_messages': candidate_messages}

    @formatting_base_response
    def choose(self, message=None):
        self.times_used += 1
        return self.candidates[np.random.randint(len(self.candidates))]


class SequentialChooser(BaseChooser):

    def __init__(self, candidate_messages, startsentence=-1):
        self._parse_candidate_messages(candidate_messages)
        if startsentence == -1:
            startsentence = np.random.randint(len(self.candidates))
        self.times_used = startsentence

    @classmethod
    def _preparation_parameters(cls, parameters):
        return_pars = {}
        return_pars['candidate_messages'] = chooser_io(parameters['filepath'])
        if 'startsentence' in parameters:
            return_pars['startsentence'] = parameters['startsentence']
        return return_pars


class QuerierSizeDrivenChooser(BaseChooser):
    # TODEPRECATE: QuerierSplitterChooser

    def __init__(self, candidate_messages, type_var, cond,
                 query_var='query_idxs'):
        self._parse_candidate_messages(candidate_messages)
        self.type_var = type_var
        self.cond = cond
        self.query_var = query_var
        for i, r in enumerate(self.candidates):
            self.candidates[i][self.type_var] = int(r[self.type_var])

    @classmethod
    def _preparation_parameters(cls, parameters):
        return_pars = {}
        return_pars['candidate_messages'] = chooser_io(parameters['filepath'])
        return_pars['type_var'] = parameters['type_var']
        return_pars['cond'] =\
            parse_parameter_functions(parameters['chooser_function'])
        return_pars['query_var'] = parameters['query_var']
        return return_pars

    @formatting_base_response
    def choose(self, message):
        if self.query_var in message:
            i = self.cond(len(message[self.query_var]))
        else:
            i = self.cond(len(message['query'][self.query_var]))
        filtered_candidates = [q for q in self.candidates
                               if q[self.type_var] == i]
        return filtered_candidates[np.random.randint(len(filtered_candidates))]


class QuerierSplitterChooser(BaseChooser):

    def __init__(self, candidate_messages, type_var, cond,
                 query_var='query_idxs'):
        self._parse_candidate_messages(candidate_messages)
        self.type_var = type_var
        self.cond = cond
        self.query_var = query_var
        for i, r in enumerate(self.candidates):
            self.candidates[i][self.type_var] = int(r[self.type_var])

    @classmethod
    def _preparation_parameters(cls, parameters):
        return_pars = {}
        return_pars['candidate_messages'] = chooser_io(parameters['filepath'])
        return_pars['type_var'] = parameters['type_var']
        return_pars['cond'] =\
            parse_parameter_functions(parameters['chooser_function'])
        return_pars['query_var'] = parameters['query_var']
        return return_pars

    @formatting_base_response
    def choose(self, message):
        i = self.choose_tag(message)
        filtered_candidates = [q for q in self.candidates
                               if int(q[self.type_var]) == i]
        return filtered_candidates[np.random.randint(len(filtered_candidates))]

    def choose_tag(self, message):
        # TODO: Extend
        if isinstance(message['query'], dict):
            i = self.cond(message['query'][self.query_var])
        else:
            i = self.cond(message['query'])
        return i


################################# Transition ##################################
###############################################################################
class TransitionConversationStates(object):

    def __init__(self, name_trans_states, condition):
        self._format_condition(condition)
        self._format_transitions(name_trans_states)
        self.currentstate = None

    @classmethod
    def from_transition_info(cls, transition_info):
        if transition_info is None:
            return NullTransitionConversation()
        elif type(transition_info) in [tuple, list]:
            assert(len(transition_info) == 2)
            return cls(*transition_info)
        elif type(transition_info) == dict:
            if 'transition_object' in transition_info:
                obj = eval(transition_info['transition_object'])
            else:
                obj = cls
            if 'transition_states' not in transition_info:
                return NullTransitionConversation()
            name_trans_states = transition_info['transition_states']
            tr_function_info = transition_info['transition_function']
            if not callable(tr_function_info):
                tr_function_info = parse_parameter_functions(tr_function_info)
            return obj(name_trans_states, tr_function_info)
        else:
            assert(isinstance(transition_info, TransitionConversationStates))
            if transition_info.condition is None:
                return NullTransitionConversation()
            return cls(transition_info.transitions, transition_info.condition)

    @classmethod
    def test_from_transition_info(cls, transition_info):
        if transition_info is None:
            return NullTransitionConversation()
        elif isinstance(transition_info, list):
            if len(transition_info):
                if isinstance(transition_info[0], list):
                    return TransitionTesting(transition_info[0])
            return TransitionTesting(transition_info)
        elif isinstance(transition_info, dict):
            if 'transition_states' not in transition_info:
                return NullTransitionConversation()
            if 'transition_object' in transition_info:
                tr_obj_name = transition_info['transition_object']
                if tr_obj_name == 'NullTransitionConversation':
                    return NullTransitionConversation()
            return TransitionTesting(transition_info.transitions)
        elif isinstance(transition_info, tuple):
            assert(isinstance(transition_info[0], list))
            return TransitionTesting(transition_info[0])
        else:
            assert(isinstance(transition_info, TransitionConversationStates))
            return TransitionTesting(transition_info.transitions)

    def _format_condition(self, condition):
        assert(callable(condition))
        self.condition = condition

    def _format_transitions(self, name_trans_states):
        if type(name_trans_states) in [list, tuple]:
            self.transitions = name_trans_states
        elif type(name_trans_states) == str:
            self.transitions = [name_trans_states]
        else:
            raise TypeError("Not correct transition states input.")

    def set_current_state(self, conversationstate):
        self.currentstate = conversationstate.name

    def next_state(self, response):
        i_states = self.condition(response)
        name_next_state = self.transitions[i_states]
        return name_next_state


class NullTransitionConversation(TransitionConversationStates):

    def __init__(self, name_trans_states=None, condition=None):
        self.condition = None
        self.transitions = []
        self.currentstate = None

    def next_state(self, response):
        return self.currentstate


class TransitionTesting(TransitionConversationStates):
    """Testing mode transitions for the ones next to user interaction."""

    def __init__(self, name_trans_states=None):
        self._format_transitions(name_trans_states)
        self.currentstate = None

    def next_state(self, response):
        last_response = response.last_message_text
        name_next_state = self.transitions[int(last_response)]
        return name_next_state


############################### Utils functions ###############################
###############################################################################
def flatten_1lvl(lista):
    new_list = []
    for l in lista:
        if isinstance(l, list):
            new_list.extend(l)
        else:
            new_list.append(l)
    return new_list

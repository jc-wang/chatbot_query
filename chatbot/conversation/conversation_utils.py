

import copy
import numpy as np

from functools import wraps
from chatbot import ChatbotMessage


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
        ## WARNING: Probably into class message
        for key in message:
            if key not in output_message:
                if key not in ['message', 'from', 'time', 'answer_status',
                               'sending_status', 'collection']:
                    output_message[key] = message[key]
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
        else:
            assert(isinstance(querier_info, BaseQuerier))
            return querier_info

    def make_query(self, handler_db, message):
        query_message = self.querier(handler_db, message)
        if isinstance(query_message, dict):
            if 'query' in query_message:
                message.update(query_message)
        else:
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
        else:
            assert(isinstance(chooser_info, BaseChooser))
            obj = copy.copy(chooser_info)
            obj.times_used = 0
            return obj


class NullChooser(BaseChooser):
    """Avoid to take a decision and pass a message as it arrives to it."""

    def __init__(self):
        self.candidates = []
        self.times_used = 0

    def choose(self, message):
        return message


class RandomChooser(BaseChooser):

    def __init__(self, candidate_messages):
        self.candidates = [ChatbotMessage.from_candidates_messages(r)
                           for r in candidate_messages]
        self.times_used = 0

    @formatting_base_response
    def choose(self, message=None):
        self.times_used += 1
        return self.candidates[np.random.randint(len(self.candidates))]


class SequentialChooser(BaseChooser):

    def __init__(self, candidate_messages, startsentence=-1):
        self.candidates = [ChatbotMessage.from_candidates_messages(r)
                           for r in candidate_messages]
        if startsentence == -1:
            startsentence = np.random.randint(len(self.candidates))
        self.times_used = startsentence


class QuerierSizeDrivenChooser(BaseChooser):
    # TODEPRECATE: QuerierSplitterChooser

    def __init__(self, candidate_messages, type_var, cond,
                 query_var='query_idxs'):
        self.candidates = [ChatbotMessage.from_candidates_messages(r)
                           for r in candidate_messages]
        self.type_var = type_var
        self.cond = cond
        self.query_var = query_var

    @formatting_base_response
    def choose(self, message):
        i = self.cond(len(message[self.query_var]))
        filtered_candidates = [q for q in self.candidates
                               if q[self.type_var] == i]
        return filtered_candidates[np.random.randint(len(filtered_candidates))]


class QuerierSplitterChooser(BaseChooser):

    def __init__(self, candidate_messages, type_var, cond,
                 query_var='query_idxs'):
        self.candidates = [ChatbotMessage.from_candidates_messages(r)
                           for r in candidate_messages]
        self.type_var = type_var
        self.cond = cond
        self.query_var = query_var

    @formatting_base_response
    def choose(self, message):
        i = self.choose_tag(message)
        filtered_candidates = [q for q in self.candidates
                               if q[self.type_var] == i]
        return filtered_candidates[np.random.randint(len(filtered_candidates))]

    def choose_tag(self, message):
        # TODO: Extend
        i = self.cond(message['query'][self.query_var])
        return i


################################# Transition ##################################
###############################################################################
class TransitionConversationStates(object):

    def __init__(self, name_trans_states, condition):
        assert(callable(condition))
        self.condition = condition
        self.transitions = name_trans_states
        self.currentstate = None

    @classmethod
    def from_transition_info(cls, transition_info):
        if transition_info is None:
            return NullTransitionConversation()
        elif type(transition_info) in [tuple, list]:
            assert(len(transition_info) == 2)
            return cls(*transition_info)
        else:
            assert(isinstance(transition_info, TransitionConversationStates))
            if transition_info.condition is None:
                return NullTransitionConversation()
            return cls(transition_info.transitions, transition_info.condition)

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

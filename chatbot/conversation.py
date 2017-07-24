
"""
Conversation
------------
Main code for the State Machine and tools to engineer the possible
conversation.

"""
import numpy as np
import copy


############################# ConversationMachine #############################
###############################################################################
class BaseConversationState(object):

    def __init__(self, name, transition):
        self.name = name
        if transition is None:
            self.transition = NullTransitionConversation()
        else:
            self.transition = transition
        self.transition_states = self.transition.transitions
        self.next_state = self.name
        self.tags = None
        self.next_tags = None

    def next(self, message):
        next_state_name = self.transition.next_state(message)
        return next_state_name

    def _compute_next(self, message):
        self.next_state = self.next(message)

    def get_tags(self):
        return self.tags

    @property
    def get_currentChildernState(self):
        return self.name


class ConversationStateMachine(BaseConversationState):

    def __init__(self, name, states, startState, endStates, transition=None):
        super().__init__(name, transition)
        state_names = [state.name for state in states]
        assert(startState in state_names)
        assert(all([s in state_names for s in endStates]))
        self.startState = startState
        self.historyStates = [startState]
        self.currentState = startState
        self.endStates = endStates
        self.states = dict(zip(state_names, states))

    def run(self, handler_io):
        current_state = self.states[self.startState]
        while True:
            message = current_state.run(handler_io)
            if current_state.name in self.endStates:
                # Probable returning next state
                return {}
            next_state_name = current_state.next(message)
            current_state = self.states[next_state_name]

    def get_message(self, handler_db, message):
        answer = None
        current_state = self.states[self.currentState]
        self.currentState = current_state.name
        while answer is None:
            answer = current_state.get_message(handler_db, message)
            if current_state.name in self.endStates:
                self._compute_next(answer)
                return answer
            current_state = self.get_next_state(current_state)
        self.currentState = current_state.name
        self.update_tags()
#        self._compute_next(answer)
        return answer

    def get_next_state(self, current_state):
        next_state = current_state.next_state
        self.historyStates.append(next_state)
        current_state = self.states[next_state]
        self.currentState = current_state.name
        return current_state

    def get_tags(self):
        return self.states[self.currentState].self.tags

    def update_tags(self):
        self.next_tags = self.states[self.historyStates[-2]].next_tags

    @property
    def get_currentChildernState(self):
        return self.states[self.currentState].name


############################# ConversationStates ##############################
###############################################################################
class TalkingState(BaseConversationState):
    """State that manage the interaction with the user.
    """

    def __init__(self, name, chooser, detector=None, tags=None,
                 transition=None):
        super().__init__(name, transition)
        ## Conversation states
        self.questions = chooser.candidates
        self.chooser = chooser
        if detector is None:
            self.detector = BaseDetector()
        else:
            assert(isinstance(detector, BaseDetector))
            self.detector = detector
        self.tags = tags
        self.next_tags = tags
        # Flag to know if the it has to get message or make and answer
        self.flag_question_answer = 0

    def run(self, handler_io):
        """
        """
        ## 0. Choose Question
        message = self.chooser.choose()
        message['message'] =\
            message['message'].format(**handler_io.profile_user.profile)

        ## 1. Get answer
        answer = handler_io.interact(message, self.tags)

        ## 2. Process answer
        answer = self.detector.detect(answer)

        return answer

    def get_message(self, handler_db, message):
        if self.flag_question_answer == 0:
            answer = self._choose_question(handler_db)
            self.flag_question_answer = 1
        else:
            answer = self._process_message(message)
            self.flag_question_answer = 0
        return answer

    def _choose_question(self, handler_db):
        ## 0. Choose Question
        message = copy.copy(self.chooser.choose())
        message['message'] =\
            message['message'].format(**handler_db.profile_user.profile)
        return message

    def _process_message(self, answer):
        ## 1. Process answer
        answer = self.detector.detect(answer)
        ## 2. Compute next
        self._compute_next(answer)
        return None


class StoringState(BaseConversationState):
    """Interacts with the storage without interacting with the user.
    """

    def __init__(self, name, storer, transition=None):
        super().__init__(name, transition)
        assert(callable(storer))
        self.storer = storer

    def run(self, handler_io):
        self.storer(handler_io)
        return {}

    def get_message(self, handler_db, message):
        answer = self.run(handler_db)
        self._compute_next(answer)
        return None


class QuerierState(BaseConversationState):
    """Interface with the database to get the query you want to obtain.
    """

    def __init__(self, name, querier, chooser, detector=None, transition=None,
                 tags=None):
        super().__init__(name, transition)
        self.tags = tags
        self.next_tags = tags
        self.chooser = chooser
        assert(callable(querier))
        self.querier = querier
        if detector is None:
            self.detector = BaseDetector()
        else:
            assert(isinstance(detector, BaseDetector))
            self.detector = detector
        # Flag to know if the it has to get message or make and answer
        self.flag_question_answer = 0

    def get_message(self, handler_db, message):
        if self.flag_question_answer == 0:
            answer = self._choose_question(handler_db)
            self.flag_question_answer = 1
        else:
            answer = self._process_message(message)
            self.flag_question_answer = 0
        return answer

    def _process_message(self, answer):
        ## 1. Process answer
        answer = self.detector.detect(answer)
        ## 2. Compute next
        self._compute_next(answer)
        return None

    def _choose_question(self, handler_db):
        ## 0. Query
        answer = self.querier(handler_db)
        ## 1. Choose Question
        message = copy.copy(self.chooser.choose(answer))
        ## 2. Format message
        # WARNING: Hardcoded
        queries_names = ', '.join(answer['query_names'])
        message['message'] =\
            message['message'].format(query_names=queries_names)
        return message


class CheckerState(BaseConversationState):
    """Acts as a control flow in the ConversationStateMachine without
    interacting with the user.
    """

    def __init__(self, name, checker, transition=None):
        super().__init__(name, transition)
        assert(callable(checker))
        self.checker = checker

    def run(self, handler_io):
        check_message = self.checker(handler_io)
        return check_message

    def get_message(self, handler_db, message):
        answer = self.run(handler_db)
        self._compute_next(answer)
        return None


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

    def detect(self, answer):
        probabilities = self.detector(answer)
        assert(len(probabilities) == len(self.pos_types))
        answer['type'] = dict(zip(self.pos_types, probabilities))
        return answer


################################### Chooser ###################################
###############################################################################
class BaseChooser(object):

    def choose(self, message=None):
        message = self.candidates[(self.times_used % len(self.candidates))]
        self.times_used += 1
        return message


class RandomChooser(BaseChooser):

    def __init__(self, candidate_messages):
        self.candidates = candidate_messages
        self.times_used = 0

    def choose(self, message=None):
        self.times_used += 1
        return self.candidates[np.random.randint(len(self.candidates))]


class SequencialChooser(BaseChooser):

    def __init__(self, candidate_messages):
        self.candidates = candidate_messages
        self.times_used = np.random.randint(len(self.candidates))


class QuerierSizeDrivenChooser(BaseChooser):

    def __init__(self, candidate_messages, type_var, cond, query_var='query'):
        self.candidates = candidate_messages
        self.type_var = type_var
        self.cond = cond
        self.query_var = query_var

    def choose(self, message):
        i = self.cond(len(message[self.query_var]))
        filtered_candidates = [q for q in self.candidates
                               if q[self.type_var] == i]
        return filtered_candidates[np.random.randint(len(filtered_candidates))]


################################# Transition ##################################
###############################################################################
class TransitionConversationStates(object):

    def __init__(self, name_trans_states, condition):
        assert(callable(condition))
        self.condition = condition
        self.transitions = name_trans_states

    def next_state(self, response):
        i_states = self.condition(response)
        name_next_state = self.transitions[i_states]
        return name_next_state


class NullTransitionConversation(TransitionConversationStates):

    def __init__(self, name_trans_states=None, condition=None):
        self.condition = lambda x: x
        self.transitions = []

    def next_state(self, response):
        return None

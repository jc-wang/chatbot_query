
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
        self.last = True

    def next(self, message):
        next_state_name = self.transition.next_state(message)
        return next_state_name

    def _compute_next(self, message):
        self.next_state = self.next(message)

    def _islast(self, message):
        islast = False
        if 'last' in message:
            islast = message['last']
        return islast

    def get_tags(self):
        return self.tags

    @property
    def get_currentChildernState(self):
        return self.name

    def restart(self):
        pass


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
        self.ended = False

    def restart(self):
        self.currentState = self.startState
        [self.states[s].restart() for s in self.states]

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
        while self.keep_loop(answer):
            answer = current_state.get_message(handler_db, message)
            if current_state.name in self.endStates:
                self._compute_next(message)
                self.ended = True
#                self.restart()
                return answer
            current_state = self.get_next_state(current_state)
        self.currentState = current_state.name
        self.update_tags()
#        self._compute_next(answer)
        return answer

    def keep_loop(self, answer):
        if answer is None:
            return True
        else:
            assert(type(answer) == dict)
            logi = ('message' not in answer)
            if 'from' in answer:
                logi = logi and (answer['from'] != 'user')
            return logi

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
        self.restart()

    def restart(self):
        # Flag to know if the it has to get message or make and answer
        self.flag_question_answer = 0
        # Last message of the before
        self.last = True
        self.last_query = {}

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
        assert(type(answer) == dict)
        return answer

    def _choose_question(self, handler_db):
        ## 00. Reset some properties
        self.next_state = self.name
        ## 0. Choose Question
        message = copy.copy(self.chooser.choose())
        message['message'] =\
            message['message'].format(**handler_db.profile_user.profile)
        message['last'] = self.last
        ## 1. Store query information if it is available
        if 'query' in message:
            self.last_query = message['query']
        return message

    def _process_message(self, answer):
        ## 1. Process answer
        answer = self.detector.detect(answer)
        ## 2. Compute next
        self._compute_next(answer)
        ## 3. Query managment
        if self.last_query != {}:
            answer['query'] = self.last_query
            self.last_query = {}
        ## WARNING: Undesired
        answer = clean_message(answer)
        return answer


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
        answer = self.storer(handler_db, message)
        self._compute_next(answer)
        return answer


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
        self.restart()

    def restart(self):
        # Flag to know if the it has to get message or make and answer
        self.flag_question_answer = 0
        # Track queries
        self.queriesDB = []
        # Last query memory
        self.last_query = {}
        self.q_data = {}

    def get_message(self, handler_db, message):
        if self.flag_question_answer == 0:
            answer = self._choose_question(handler_db, message)
            self.flag_question_answer = 1
        else:
            answer = self._process_message(message)
            assert('message' not in answer)
            self.flag_question_answer = 0
        return answer

    def _process_message(self, answer):
        ## 0. Reload information of question
        answer.update(self.q_data)
        answer.update(self.last_query)
        ## 1. Process answer
        answer = self.detector.detect(answer)
        ## 2. Compute next
        self._compute_next(answer)
        ## 3. Privatize answer (remove message, only metadata inmportant)
#        answer = clean_message(answer)
        ## 4. Clean storage
        self.q_data = {}
        self.last_query = {}
        answer = clean_message(answer)
        return answer

    def _choose_question(self, handler_db, message):
        ## 00. Reset some properties
        self.next_state = self.name
        ## 0. Query
        query_message = self.querier(handler_db, message)
        ## 1. Choose Question
        message = copy.copy(self.chooser.choose(query_message['query']))
        ## 2. Store in logqueries db
        self.queriesDB.append(query_message)
        self.last_query = query_message
        ## 3. Format message
        message['message'] =\
            message['message'].format(**query_message['answer_names'])
        ## 4. Give a tag to the answer type
        message['answer_type'] =\
            self.chooser.choose_tag(query_message['query'])
        ## 5. Store question information
        self.q_data = self._store_question_data(message)
        return message

    def _store_question_data(self, question):
        q_data = {}
        for v in question:
            if v != 'message':
                q_data[v] = question[v]
        return q_data


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
        answer = self.checker(handler_db, message)
        self._compute_next(answer)
        answer = clean_message(answer)
        return answer


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
    # TODEPRECATE: QuerierSplitterChooser

    def __init__(self, candidate_messages, type_var, cond,
                 query_var='query_idxs'):
        self.candidates = candidate_messages
        self.type_var = type_var
        self.cond = cond
        self.query_var = query_var

    def choose(self, message):
        i = self.cond(len(message[self.query_var]))
        filtered_candidates = [q for q in self.candidates
                               if q[self.type_var] == i]
        return filtered_candidates[np.random.randint(len(filtered_candidates))]


class QuerierSplitterChooser(BaseChooser):

    def __init__(self, candidate_messages, type_var, cond,
                 query_var='query_idxs'):
        self.candidates = candidate_messages
        self.type_var = type_var
        self.cond = cond
        self.query_var = query_var

    def choose(self, message):
        i = self.choose_tag(message)
        filtered_candidates = [q for q in self.candidates
                               if q[self.type_var] == i]
        return filtered_candidates[np.random.randint(len(filtered_candidates))]

    def choose_tag(self, message):
        # TODO: Extend
        i = self.cond(message[self.query_var])
        return i


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


def clean_message(message):
    new_message = {}
    for key in message:
        if key not in ['message', 'from', 'time']:
            new_message[key] = message[key]
    return new_message

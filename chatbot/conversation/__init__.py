
"""
Conversation
------------
Main code for the State Machine and tools to engineer the possible
conversation.

"""

import copy
import numpy as np

from chatbot.conversation.conversation_utils import BaseDetector
from chatbot.conversation.conversation_utils import BaseQuerier, NullQuerier
from chatbot.conversation.conversation_utils import RandomChooser,\
    QuerierSizeDrivenChooser, QuerierSplitterChooser, SequentialChooser,\
    NullChooser, BaseChooser
from chatbot.conversation.conversation_utils import\
    NullTransitionConversation, TransitionConversationStates


def clean_message(message):
    new_message = {}
    for key in message:
        if key not in ['message', 'from', 'time']:
            new_message[key] = message[key]
    return new_message


class BaseConversationState(object):

    def __init__(self, name, transition):
        self.name = name
        self.transition =\
            TransitionConversationStates.from_transition_info(transition)
        self.transition.set_current_state(self)
#        self.transition_states = self.transition.transitions
        self.next_state = self.name
        self.tags = None
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

    def _format_tags(self, tags):
        if type(tags) == str:
            tags = [tags]
        self.tags = tags

    def get_tags(self):
        return self.tags

    @property
    def get_currentChildernState(self):
        return self.name

    @property
    def ended(self):
        return (self.flag_question_answer == 2)

    @property
    def sending_status(self):
        return (not self.shadow)

    def restart(self):
        pass


class GeneralConversationState(BaseConversationState):

    def __init__(self, name, detector=None, chooser=None, querier=None,
                 transition=None, asker=True, tags=None, shadow=False):
        super().__init__(name, transition)
        ## Initialize core elements
        self.detector = BaseDetector.from_detector_info(detector)
        self.chooser = BaseChooser.from_chooser_info(chooser)
        self.querier = BaseQuerier.from_querier_info(querier)
        # Enrichment information
        self.tags = self._format_tags(tags)
        ## Asker or answerer
        self.asker = asker
        if asker:
            self.flag_question_answer = 0
        else:
            self.flag_question_answer = 1
        ## External control information
        self.shadow = shadow

    def get_message(self, handler_db, message):
        if self.flag_question_answer == 0:
            answer = self._answer_message(handler_db, message)
            self.flag_question_answer = 1
        elif self.flag_question_answer == 1:
            answer = self._process_message(message)
            self.flag_question_answer = 0  # WARNING
        else:
            # It should be added as an end state
            raise Exception("End of conversation!")
        assert(type(answer) == dict)
        return answer

    def _answer_message(self, handler_db, message):
        ## 0. Make query
        message = self.querier.make_query(handler_db, message)
        ## 1. Choose Answer
        message = copy.copy(self.chooser.choose(message))
        ## 2. Format Answer
        message['message'] =\
            message['message'].format(**handler_db.profile_user.profile)
        ## 3. Add tags
        message = self._add_tags(message)
        return message

    def _process_message(self, message):
        ## 1. Process answer
        message = self.detector.detect(message)
        ## 2. Add tags
        message = self._add_tags(message)
        return message

    def _add_tags(self, message):
        if self.tags is not None:
            if 'tags' in message:
                message['tags'] += self.tags
                message['tags'] = list(set(message['tags']))
            else:
                message['tags'] = self.tags
        return message

    def next(self, message):
        "TODO: history"
        next_state_name = self.transition.next_state(message)
        return next_state_name

    def _compute_next(self, message):
        self.next_state = self.next(message)

    @property
    def questions(self):
        return self.chooser.candidates

    @property
    def next_states(self):
        return self.transitions.transitions


############################# ConversationMachine #############################
###############################################################################
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
        ## DEPRECATED??
        self.next_tags = self.states[self.historyStates[-2]].next_tags

    @property
    def get_currentChildernState(self):
        return self.states[self.currentState].name


############################# ConversationStates ##############################
###############################################################################
class TalkingState(GeneralConversationState):
    """State that manage the interaction with the user.
    """

    def __init__(self, name, chooser, detector=None, transition=None,
                 asker=True, tags=None, shadow=False):
        super().__init__(name, detector, chooser, transition=transition,
                         asker=asker, tags=tags, shadow=shadow)
#        ## Conversation states
#        self.questions = chooser.candidates
        self.next_tags = tags
        self.restart()

    def restart(self):
#        # Flag to know if the it has to get message or make and answer
#        self.flag_question_answer = 0
#        # Last message of the before
#        self.last = True
#        self.last_query = {}
        pass

#    def run(self, handler_io):
#        """
#        """
#        ## 0. Choose Question
#        message = self.chooser.choose()
#        message['message'] =\
#            message['message'].format(**handler_io.profile_user.profile)
#
#        ## 1. Get answer
#        answer = handler_io.interact(message, self.tags)
#
#        ## 2. Process answer
#        answer = self.detector.detect(answer)
#
#        return answer
#
#    def get_message(self, handler_db, message):
#        if self.flag_question_answer == 0:
#            answer = self._choose_question(handler_db)
#            self.flag_question_answer = 1
#        else:
#            answer = self._process_message(message)
#            self.flag_question_answer = 0
#        assert(type(answer) == dict)
#        return answer
#
#    def _choose_question(self, handler_db):
#        ## 00. Reset some properties
#        self.next_state = self.name
#        ## 0. Choose Question
#        message = copy.copy(self.chooser.choose())
#        message['message'] =\
#            message['message'].format(**handler_db.profile_user.profile)
#        message['last'] = self.last
#        ## 1. Store query information if it is available
#        if 'query' in message:
#            self.last_query = message['query']
#        return message
#
#    def _process_message(self, answer):
#        ## 1. Process answer
#        answer = self.detector.detect(answer)
#        ## 2. Compute next
#        self._compute_next(answer)
#        ## 3. Query managment
#        if self.last_query != {}:
#            answer['query'] = self.last_query
#            self.last_query = {}
#        ## WARNING: Undesired
#        answer = clean_message(answer)
#        return answer


class StoringState(GeneralConversationState):
    """Interacts with the storage without interacting with the user.
    """

    def __init__(self, name, storer, transition=None):
        super().__init__(name, querier=storer, transition=transition,
                         asker=True, shadow=True)

#    def get_message(self, handler_db, message):
#        answer = self.storer(handler_db, message)
#        self._compute_next(answer)
#        return answer

#    def run(self, handler_io):
#        self.storer(handler_io)
#        return {}


class QuerierState(GeneralConversationState):
    """Interface with the database to get the query you want to obtain.
    """

    def __init__(self, name, querier, chooser, detector=None, transition=None,
                 tags=None):
        super().__init__(name, detector=detector, chooser=chooser,
                         querier=querier, transition=transition, asker=True,
                         tags=tags, shadow=False)
#        self.restart()

#    def restart(self):
#        # Flag to know if the it has to get message or make and answer
#        self.flag_question_answer = 0
#        # Track queries
#        self.queriesDB = []
#        # Last query memory
#        self.last_query = {}
#        self.q_data = {}
#
#    def get_message(self, handler_db, message):
#        if self.flag_question_answer == 0:
#            answer = self._choose_question(handler_db, message)
#            self.flag_question_answer = 1
#        else:
#            answer = self._process_message(message)
#            assert('message' not in answer)
#            self.flag_question_answer = 0
#        return answer
#
#    def _process_message(self, answer):
#        ## 0. Reload information of question
#        answer.update(self.q_data)
#        answer.update(self.last_query)
#        ## 1. Process answer
#        answer = self.detector.detect(answer)
#        ## 2. Compute next
#        self._compute_next(answer)
#        ## 3. Privatize answer (remove message, only metadata inmportant)
##        answer = clean_message(answer)
#        ## 4. Clean storage
#        self.q_data = {}
#        self.last_query = {}
#        answer = clean_message(answer)
#        return answer
#
#    def _choose_question(self, handler_db, message):
#        ## 00. Reset some properties
#        self.next_state = self.name
#        ## 0. Query
#        query_message = self.querier(handler_db, message)
#        ## 1. Choose Question
#        message = copy.copy(self.chooser.choose(query_message['query']))
#        ## 2. Store in logqueries db
#        self.queriesDB.append(query_message)
#        self.last_query = query_message
#        ## 3. Format message
#        message['message'] =\
#            message['message'].format(**query_message['answer_names'])
#        ## 4. Give a tag to the answer type
#        message['answer_type'] =\
#            self.chooser.choose_tag(query_message['query'])
#        ## 5. Store question information
#        self.q_data = self._store_question_data(message)
#        return message
#
#    def _store_question_data(self, question):
#        q_data = {}
#        for v in question:
#            if v != 'message':
#                q_data[v] = question[v]
#        return q_data


class CheckerState(GeneralConversationState):
    """Acts as a control flow in the ConversationStateMachine without
    interacting with the user.
    """

    def __init__(self, name, checker, transition=None):
        super().__init__(name, querier=checker, transition=transition,
                         asker=True, shadow=True)
#
#    def run(self, handler_io):
#        check_message = self.checker(handler_io)
#        return check_message
#
#    def get_message(self, handler_db, message):
#        answer = self.checker(handler_db, message)
#        self._compute_next(answer)
#        answer = clean_message(answer)
#        return answer

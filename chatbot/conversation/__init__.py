
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
from chatbot import ChatbotMessage


class BaseConversationState(object):

    def __init__(self, name, transition):
        self.name = name
        self.transition =\
            TransitionConversationStates.from_transition_info(transition)
        self.transition.set_current_state(self)
#        self.transition_states = self.transition.transitions
        self.next_state = self.name
        self.tags = None

    @property
    def next_states(self):
        return self.transition.transitions

    @property
    def parentState(self):
        return '.'.join(self.abspathname.split('.')[:-1])

    def next(self, message):
        "TODO: history"
        if self.runned:
            return None
        next_state_name = self.transition.next_state(message)
        return next_state_name

    def _compute_next(self, message):
        self.next_state = self.next(message)

    def _if_sent(self, message):
        ifsent = False
        if 'sending_status' in message:
            ifsent = message['sending_status']
        return ifsent

    def _format_tags(self, tags):
        if type(tags) == str:
            tags = [tags]
        self.tags = tags

    def get_tags(self):
        return self.tags

    def restart(self):
        pass

    def create_abspathname(self, abspathname=''):
        abspathname = self._pathname_formatter(abspathname)
        if 'states' in dir(self):
            for s in self.states:
                child_abspathname =\
                    self._pathname_formatter('.'.join([abspathname,
                                                       self.states[s].name]))
                self.states[s].abspathname = child_abspathname
                self.states[s].create_abspathname(child_abspathname)
        else:
            self.abspathname = self._pathname_formatter(abspathname)
#            self.abspathname =\
#                '.'.join([abspathname, self.name]).replace(' ', '_')

#    def create_all_states_list(self, state=[]):
#        return self.accumulate_states

    def create_buttom_states_list(self, state=[]):
        def flatten(container):
            for i in container:
                if isinstance(i, (list, tuple)):
                    for j in flatten(i):
                        yield j
                else:
                    yield i
        if type(state) == list:
            if not state:
                return self.create_buttom_states_list(self)
            return list(flatten([self.create_buttom_states_list(s)
                                 for s in state]))
        elif isinstance(state, ConversationStateMachine):
            state = [self.create_buttom_states_list(state.states[s])
                     for s in state.states]
            state = list(flatten(state))
            return state
        elif isinstance(state, GeneralConversationState):
            return state
        else:
            Exception("Error")

    def _pathname_formatter(self, name):
        return name.replace(' ', '_')


class GeneralConversationState(BaseConversationState):

    def __init__(self, name, detector=None, chooser=None, querier=None,
                 transition=None, asker=True, tags=None, shadow=False,
                 running_times=np.inf):
        super().__init__(name, transition)
        ## Initialize core elements
        self.detector = BaseDetector.from_detector_info(detector)
        self.chooser = BaseChooser.from_chooser_info(chooser)
        self.querier = BaseQuerier.from_querier_info(querier)
        # Store initial configuration
        self.initializers = {'transition': self.transition,
                             'detector': self.detector,
                             'chooser': self.chooser,
                             'querier': self.querier}
        # Enrichment information
        self.tags = self._format_tags(tags)
        ## Asker or answerer
        self.asker = asker
        if asker:
            self.flag_question_answer = 0
        else:
            self.flag_question_answer = 1
        self.runned = False
        ## External control information
        self.shadow = shadow
        self.posting = False
        ## Next state
        self.next_state = self.name
        ## TODO: shadow and asker?
        self.running_times = running_times
        self.counts = 0
        self.accumulate_states = [self]

    def get_message(self, handler_db, message):
        message = ChatbotMessage.from_message(message)
        if self.flag_question_answer == 0:
            answer = self._answer_message(handler_db, message)
            self._manage_next_state(answer)
        elif self.flag_question_answer == 1:
            answer = self._process_message(message)
            self._manage_next_state(answer)
        else:
            # It should be added as an end state
            raise Exception("End of conversation!")
        assert(isinstance(answer, dict))
        return answer

    def _manage_next_state(self, message):
        self.counts += 1
        if self.flag_question_answer == 0:
            self._manage_limited_runs(self.flag_question_answer)
            if not self.asker:
                self._compute_next(message)
                self.runned = True
            else:
                self.runned = False
                self.next_state = self.name
        elif self.flag_question_answer == 1:
            self._manage_limited_runs(self.flag_question_answer)
            if self.asker:
                self._compute_next(message)
                self.runned = True
            else:
                self.runned = False
                self.next_state = self.name
        # If shadow only runs 1 time!!!
#        if self.shadow:
#            self.runned = True

    def _manage_limited_runs(self, actual_flag):
        if self.running_times <= self.counts:
            self.flag_question_answer = 2
        else:
            self.flag_question_answer = int(abs(actual_flag-1))

    def _answer_message(self, handler_db, message):
        ## 0. Make query
        message = self.querier.make_query(handler_db, message)
        ## 0b. Preformat message
        ## 1. Choose Answer
        message = copy.copy(self.chooser.choose(message))
        ## 2. Format Answer
        message = self._message_formatting(handler_db, message)
        ## 3. Add tags
        message = self._add_tags(message)
        ## 4. Sending status
        message = message.add_entry_to_last_message('sending_status',
                                                    self.sending_status)
        ## 5. Answering status
        answer_status = self.sending_status and self.asker
        message = message.add_entry_to_last_message('answer_status',
                                                    answer_status)
        ## 6. Posting status
#        posting_status = self.shadow and self.posting
        message = message.add_entry_to_last_message('posting_status',
                                                    self.posting)
        ## 7. Structure messages
        message = message.structure_answer()
        return message

    def _message_formatting(self, handler_db, message):
        formatting_tags = handler_db.profile_user.profile
        formatting_tags.update(handler_db.get_last_query())
        ## TEMPORAL
        if 'query' in message:
            if message['query'] is not None:
                if 'answer_names' in message['query']:
                    if message['answer_names'] is not None:
                        formatting_tags.update(message['answer_names'])
        if 'answer_names' in message:
            if message['answer_names'] is not None:
                formatting_tags.update(message['answer_names'])
        message = message.format_message(formatting_tags)
        return message

    def _process_message(self, message):
        ## 1. Process answer
        message = self.detector.detect(message)
        ## 2. Add tags
        message = self._add_tags(message)
        return message

    def _detect_message_sending_status(self, message):
        if 'sending_status' in message:
            return message['sending_status']
        return True

    def _preformat_messages(self, message):
        if not self._detect_message_sending_status(message):
            if not message['collection']:
                message['message'] = [copy.copy(message)]
                message['collection'] = True
                return message
        return message

    def _add_tags(self, message):
        if self.tags is not None:
            if 'tags' in message:
                message['tags'] += self.tags
                message['tags'] = list(set(message['tags']))
            else:
                message['tags'] = self.tags
        return message

    @property
    def questions(self):
        return self.chooser.candidates

    @property
    def NotEnter(self):
        return (self.flag_question_answer == 2)

    @property
    def sending_status(self):
        return (not self.shadow)

    @property
    def currentChildernState(self):
        return None

    def restart(self):
        """Reset the properties of the state to go back to the initial
        moment.
        """
        # Initial core components
        self.transition = TransitionConversationStates.\
            from_transition_info(self.initializers['transition'])
        self.transition.set_current_state(self)
        self.detector =\
            BaseDetector.from_detector_info(self.initializers['detector'])
        self.chooser =\
            BaseChooser.from_chooser_info(self.initializers['chooser'])
        self.querier =\
            BaseQuerier.from_querier_info(self.initializers['querier'])
        # Asking state class
        if self.asker:
            self.flag_question_answer = 0
        else:
            self.flag_question_answer = 1


############################# ConversationMachine #############################
###############################################################################
class ConversationStateMachine(BaseConversationState):

    def __init__(self, name, states, startState, endStates, transition=None):
        super().__init__(name, transition)
        ## Managing states
        state_names = [state.name for state in states]
        endStates = endStates if type(endStates) == list else [endStates]
        assert(startState in state_names)
        assert(all([s in state_names for s in endStates]))
        # Initial configuration
        self.startState = startState
        self.initial_endStates = copy.copy(endStates)
        # States tracked
        self.currentState = startState
        self.endStates = endStates
        self.historyStates = [startState]
        # States storing
        self.states = dict(zip(state_names, states))
        self._set_nulltransition_endstates()
        # Tracking transition
        self.next_state = self.name
        self.flag_question_answer = 0
        self._force_post_in_ending_states()
        # Create abspathname
        self.create_abspathname(self.name)
        self.abspathname = copy.copy(self._pathname_formatter(self.name))
        self.accumulate_states = self.accumulate_states_f()
        self.setted = False
        self.runned = False

#    @property
#    def runned(self):
#        return self.in_ending_state and self.is_current_state_runned

    @property
    def in_ending_state(self):
        return (self.currentState in self.endStates)

    @property
    def is_current_state_runned(self):
        return self.states[self.currentState].runned

    def _force_post_in_ending_states(self):
        for endstatename in self.endStates:
            endState = self.states[endstatename]
            if isinstance(endState, GeneralConversationState):
                endState.posting = True

    def _set_nulltransition_endstates(self):
        for endit in self.initial_endStates:
            self.states[endit].transition = NullTransitionConversation()

    def set_machine(self):
        self.create_abspathname(self.name)
        self.flat_states = self.create_buttom_states_list()
#        states_d = dict(zip([s.abspathname for s in self.flat_states],
#                            self.flat_states))
#        self.all_states = self.create_all_states_list()
        self.all_states_d = dict(zip([s.abspathname for s in
                                      self.accumulate_states],
                                     self.accumulate_states))
        self.all_init = dict([(s.abspathname,
                               self._pathname_formatter(s.startState))
                              for s in self.accumulate_states
                              if isinstance(s, ConversationStateMachine)])
        all_endit = []
        for s in self.accumulate_states:
            if isinstance(s, ConversationStateMachine):
                for ini in s.initial_endStates:
                    all_endit.append((self._pathname_formatter(ini),
                                     s.abspathname))
        self.all_endit = dict(all_endit)
        self.all_endit.update({self.abspathname: self.abspathname})

        self.currentState = self.get_initial_state()
        self.historyStates = [self.currentState]
        self.setted = True
#        x_states = {}
#        for s in all_states:
#            if isinstance(s, ConversationStateMachine):
#                x_states[s.abspathname] = (s.startState, s.initial_endStates)

    def get_initial_state(self, name=''):
#        name = self._pathname_formatter(name)
        if not name:
            name = self._pathname_formatter(self.name)
        while True:
            new_name = self.all_init[name]
            name = '.'.join([name, new_name])
            if isinstance(self.all_states_d[name], GeneralConversationState):
                break
        return name

    def get_message(self, handler_db, message):
        assert(self.setted)
        current_state = self.all_states_d[self.currentState]
        while not self.message_prepared(message):
            message = current_state.get_message(handler_db, message)
            current_state = self.manage_next_state(current_state, message)
            self.track_evolution(current_state)
            if current_state is None:
                self.runned = True
                self.NotEnter = True
                break
        return message

    def manage_next_state(self, currentstate, message):
        next_state = currentstate.next_state
        if next_state is None:
            ## Transition between 1 ended bottom and 1 initial bottom states
            parentstate =\
                self._get_parentState_transitioner(currentstate.abspathname)
            # Global ending state Case
            if parentstate is None:
                return None
            # Get the next top parent state
            self.all_states_d[parentstate]._compute_next(message)
            self.all_states_d[parentstate].runned = True
            next_parent = self.all_states_d[parentstate].next_state
            # Global ending state Case
            if next_parent is None:
                return None
            # Get buttom initial state
            if next_parent != self.abspathname:
                next_parent =\
                    '.'.join([self.all_states_d[parentstate].parentState,
                              self._pathname_formatter(next_parent)])
            next_state = self.get_initial_state(next_parent)
            currentstate = self.all_states_d[next_state]
        else:
            ## Normal transition between two bottom states
            next_state = '.'.join([currentstate.parentState,
                                   self._pathname_formatter(next_state)])
            currentstate = self.all_states_d[next_state]
        ## Manage not enter states
        if currentstate.NotEnter:
            currentstate = None
        return currentstate

    def _get_parentState_transitioner(self, statename):
        ## TODO: track functions for each parent state
        if statename == self._pathname_formatter(self.name):
            return None
        parentname = '.'.join(statename.split('.')[:-1])
        if parentname not in self.all_endit:
            return parentname
        return self._get_parentState_transitioner(parentname)

    def track_evolution(self, currentstate):
        if currentstate is None:
            self.currentState = None
        else:
            self.currentState = currentstate.abspathname
        self.historyStates.append(self.currentState)

    def accumulate_states_f(self):
        def flatten(container):
            for i in container:
                if isinstance(i, (list, tuple)):
                    for j in flatten(i):
                        yield j
                else:
                    yield i
        l = [self.states[e].accumulate_states for e in self.states]
        l.append(self)
        return list(flatten(l))

    def restart(self):
        self.currentState = self.get_initial_state()
        self.endStates = self.initial_endStates
        self.historyStates = [self.startState]
        [self.states[s].restart() for s in self.states]

    def _ensure_correct_message(self, message):
        logi = True
        logi = logi and (isinstance(message, dict))
        if not logi:
            raise ValueError("Not proper formatting for message.")
        logi = logi and ('message' in message)
        logi = logi and ('collection' in message)
        if not logi:
            raise ValueError("Not proper formatting for message.")

    def message_prepared(self, message):
        if not isinstance(message, dict):
            return False
        if message == {}:
            return False
        if message.is_prepared():
            return True
        return False

    def _manage_next_state(self, message):
        if self.states[self.currentState].runned:
            self._compute_next(message)

    def _force_next_state(self, message):
        while True:
            currentstate = self.currentState
            self._compute_next(message)
            if currentstate != self.currentState:
                break
        return self.currentState

    @property
    def currentChildernState(self):
        return self.all_states_d[self.currentState].name


############################# ConversationStates ##############################
###############################################################################
class AnsweringState(GeneralConversationState):
    """
    """

    def __init__(self, name, chooser, detector=None, transition=None,
                 tags=None, shadow=False):
        super().__init__(name, detector, chooser, transition=transition,
                         asker=False, tags=tags, shadow=shadow)
#        ## Conversation states
#        self.questions = chooser.candidates
        self.next_tags = tags
        self.restart()


class QuestioningState(GeneralConversationState):
    """
    """

    def __init__(self, name, chooser, detector=None, transition=None,
                 tags=None, shadow=False):
        super().__init__(name, detector, chooser, transition=transition,
                         asker=True, tags=tags, shadow=shadow)
#        ## Conversation states
#        self.questions = chooser.candidates
        self.next_tags = tags
        self.restart()


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


class StoringState(GeneralConversationState):
    """Interacts with the storage without interacting with the user.
    """

    def __init__(self, name, storer, transition=None):
        super().__init__(name, querier=storer, transition=transition,
                         asker=False, shadow=True)


class QuerierState(GeneralConversationState):
    """Interface with the database to get the query you want to obtain.
    """

    def __init__(self, name, querier, chooser, detector=None, transition=None,
                 tags=None, shadow=False):
        super().__init__(name, detector=detector, chooser=chooser,
                         querier=querier, transition=transition, asker=True,
                         tags=tags, shadow=shadow)
#        self.restart()


class CheckerState(GeneralConversationState):
    """Acts as a control flow in the ConversationStateMachine without
    interacting with the user.
    """

    def __init__(self, name, checker, transition=None):
        super().__init__(name, querier=checker, transition=transition,
                         asker=False, shadow=True)

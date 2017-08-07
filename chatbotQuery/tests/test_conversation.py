
import unittest
import copy
#import mock
from unittest import mock
import numpy as np
from itertools import product

from chatbotQuery.conversation import GeneralConversationState, CheckerState,\
    QuerierState, StoringState, TalkingState, ConversationStateMachine
from chatbotQuery.conversation import SequentialChooser,\
    TransitionConversationStates
from chatbotQuery import ChatbotMessage

#from chatbotQuery.conversation import RandomChooser, SequentialChooser,\
#    QuerierSizeDrivenChooser, QuerierSplitterChooser
#from chatbotQuery.conversation import BaseQuerier, NullQuerier
#from chatbotQuery.conversation import BaseDetector


class Test_GeneralConversationState(unittest.TestCase):
    """Testing and standarization of the interface of DBAPI.
    """

    def setUp(self):
        ## Definition of possible inputs
        self.variables = ['name', 'detector', 'chooser', 'querier',
                          'transition', 'asker', 'tags', 'shadow']

        self.pos_values = [('test_conversation'),
                           (None, [[0], lambda x: [0]]),
                           (None, [{'message': 'No', 'collection': True}]),
                           (None, lambda x, y: {'query': {}}),
                           (None, [['yes', 'no'], lambda x: 0]),
                           (True, False),
                           (None, 'tag_value', ['tag_value']),
                           (True, False)]
#        # Create a candidate responses
#        self.responses = [{'message': 'Hello! How are you?'},
#                          {'message': 'These are test messages'}]
        ## Create a mock DBAPI
        # Profile user mock
        profile_user = mock.Mock()
        profile_user.configure_mock(profile={})

        # DBAPI
        def get_query_info(ids):
            return {'query': {'query_idxs': None, 'query_names': None},
                    'answer_names': None}
        dbapi = mock.Mock()
        dbapi.get_query_info = get_query_info

        # Db_handlers
        db_handlers = mock.Mock()
        db_handlers.configure_mock(databases={'db': dbapi})
        db_handlers.configure_mock(profile_user=profile_user)
        self.db_handlers = db_handlers

        ## Messages
        self.message = {'message': 'NO!', 'collection': False}

    def assert_state(self, state):
        i = 0
        message = self.message
        while not ((not state.runned) or (i == 10)):
            message = state.get_message(self.db_handlers, message)
            ## Check message
            self.assertIn('message', message)
            self.assertIn('collection', message)
            ## Check properties
            state.sending_status
            ## Check methods get
            state.get_tags()
#            state.get_currentChildernState()
            state.next_states
            state.questions

            ## Flow control
            i += 1
        state.restart()
        ## Check formatters
        state._format_tags(None)
        state._format_tags("None")
        state.flag_question_answer = 2
        with self.assertRaises(Exception):
            state.get_message(self.db_handlers, message)

    def test_general_trastions(self):
        # Testing transtion
        for p in product(*self.pos_values):
            pars = dict(zip(self.variables, p))
            state = GeneralConversationState(**pars)
            self.assert_state(state)


class Test_TalkingState(unittest.TestCase):

    def setUp(self):
        ## Definition of possible inputs
        self.variables = ['name', 'detector', 'chooser', 'transition', 'asker',
                          'tags', 'shadow']

        self.pos_values = [('test_conversation'),
                           (None, [[0], lambda x: [0]]),
                           (None, [{'message': 'No', 'collection': True}]),
                           (None, [['yes', 'no'], lambda x: 0]),
                           (True, False),
                           (None, 'tag_value', ['tag_value']),
                           (True, False)]

        ## Messages
        self.message =\
            ChatbotMessage.from_candidates_messages({'message': 'NO!',
                                                     'collection': False})

    def assert_state(self, state):
        i = 0
        message = self.message
        while not ((not state.runned) or (i == 10)):
            message = state.get_message(self.db_handlers, message)
            ## Check message
            self.assertIn('message', message)
            self.assertIn('collection', message)
            ## Check properties
            state.sending_status
            ## Check formatters
#            state._format_tags(None)
#            state._format_tags("None")
            ## Check methods get
            state.get_tags()
            state.get_currentChildernState()

            ## Flow control
            i += 1

    def test_talking(self):
        # Testing transtion
        for p in product(*self.pos_values):
            pars = dict(zip(self.variables, p))
            state = TalkingState(**pars)
            self.assert_state(state)


class Test_StoringState(unittest.TestCase):

    def setUp(self):
        ## Definition of possible inputs
        self.variables = ['name', 'storer', 'transition']

        self.pos_values = [('test_conversation'),
                           (None, lambda x, y: {'query': {}}),
                           (None, [['yes', 'no'], lambda x: 0])]

        ## Messages
        self.message =\
            ChatbotMessage.from_candidates_messages({'message': 'NO!',
                                                     'collection': False})

    def assert_state(self, state):
        i = 0
        message = self.message
        while not ((not state.runned) or (i == 10)):
            message = state.get_message(self.db_handlers, message)
            ## Check message
            self.assertIn('message', message)
            self.assertIn('collection', message)
            ## Check properties
            state.sending_status
            ## Check formatters
#            state._format_tags(None)
#            state._format_tags("None")
            ## Check methods get
            state.get_tags()
            state.get_currentChildernState()

            ## Flow control
            i += 1

    def test_storing(self):
        # Testing transtion
        for p in product(*self.pos_values):
            pars = dict(zip(self.variables, p))
            state = StoringState(**pars)
            self.assert_state(state)


class Test_QuerierState(unittest.TestCase):

    def setUp(self):
        ## Definition of possible inputs
        self.variables = ['name', 'detector', 'chooser', 'transition', 'tags',
                          'querier']

        self.pos_values = [('test_conversation'),
                           (None, [[0], lambda x: [0]]),
                           (None, [{'message': 'No', 'collection': True}]),
                           (None, [['yes', 'no'], lambda x: 0]),
                           (None, 'tag_value', ['tag_value']),
                           (None, lambda x, y: {'query': {}})]

        ## Messages
        self.message =\
            ChatbotMessage.from_candidates_messages({'message': 'NO!',
                                                     'collection': False})

    def assert_state(self, state):
        i = 0
        message = self.message
        while not ((not state.runned) or (i == 10)):
            message = state.get_message(self.db_handlers, message)
            ## Check message
            self.assertIn('message', message)
            self.assertIn('collection', message)
            ## Check properties
            state.sending_status
            ## Check formatters
#            state._format_tags(None)
#            state._format_tags("None")
            ## Check methods get
            state.get_tags()
            state.get_currentChildernState()

            ## Flow control
            i += 1

    def test_querying(self):
        # Testing transtion
        for p in product(*self.pos_values):
            pars = dict(zip(self.variables, p))
            state = QuerierState(**pars)
            self.assert_state(state)


class Test_CheckerState(unittest.TestCase):

    def setUp(self):
        ## Definition of possible inputs
        self.variables = ['name', 'checker', 'transition']

        self.pos_values = [('test_conversation'),
                           (None, lambda x, y: {'query': {}}),
                           (None, [['yes', 'no'], lambda x: 0])]

        ## Messages
        self.message =\
            ChatbotMessage.from_candidates_messages({'message': 'NO!',
                                                     'collection': False})

    def assert_state(self, state):
        i = 0
        message = self.message
        while not ((not state.runned) or (i == 10)):
            message = state.get_message(self.db_handlers, message)
            ## Check message
            self.assertIn('message', message)
            self.assertIn('collection', message)
            ## Check properties
            state.sending_status
            ## Check formatters
#            state._format_tags(None)
#            state._format_tags("None")
            ## Check methods get
            state.get_tags()
            self.assertIsNone(state.currentChildernState())

            ## Flow control
            i += 1

    def test_checking(self):
        # Testing transtion
        for p in product(*self.pos_values):
            pars = dict(zip(self.variables, p))
            state = CheckerState(**pars)
            self.assert_state(state)


class Test_ConversationStateMachine(unittest.TestCase):
    """Testing and standarization of the conversation machine.
    """

    def setUp(self):

        ## Create a mock DBAPI
        # Profile user mock
        profile_user = mock.Mock()
        profile_user.configure_mock(profile={})

        # DBAPI
        def get_query_info(ids):
            return {'query': {'query_idxs': None, 'query_names': None},
                    'answer_names': None}
        dbapi = mock.Mock()
        dbapi.get_query_info = get_query_info

        # Db_handlers
        db_handlers = mock.Mock()
        db_handlers.configure_mock(databases={'db': dbapi})
        db_handlers.configure_mock(profile_user=profile_user)
        db_handlers.get_last_query = lambda: {}
        self.db_handlers = db_handlers

        ## Definition of possible inputs
        self.variables = ['name', 'startState', 'endStates', 'states',
                          'transition']
        self.pos_values = [('test_conversation'),
                           (None, lambda x, y: {'query': {}}),
                           (None, [['yes', 'no'], lambda x: 0])]

        ## Chooser
        ask_chooser = SequentialChooser([{'message': 'question?'}])
        res_chooser = SequentialChooser([{'message': 'response'}])
        ## Messages
        self.message =\
            ChatbotMessage.from_candidates_messages({'message': 'NO!',
                                                     'collection': False})

        self.asking_state = {'name': 'questioning_state',
                             'asker': True,
                             'shadow': False,
                             'tags': 'questioning',
                             'chooser': ask_chooser}
        self.answering_state_pars = {'name': 'answering_state',
                                     'asker': False,
                                     'shadow': False,
                                     'tags': 'answering',
                                     'chooser': res_chooser}
        self.shadow_state_pars = {'name': 'shadow_state',
                                  'shadow': True}

    def assert_statemachine(self, statenachine):
        ## Check class
        statenachine.set_machine()
        self.assertIsNotNone(statenachine.currentChildernState)
        statenachine.restart()

        oth = ChatbotMessage.from_candidates_messages({'message': '0'})
        blank = ChatbotMessage.from_candidates_messages({'message': ''})
        notsending = ChatbotMessage.\
            from_candidates_messages({'message': ',',
                                      'sending_status': False})
        yessending = ChatbotMessage.\
            from_candidates_messages({'message': ',',
                                      'sending_status': True})
        self.assertFalse(statenachine.message_prepared(None))
        self.assertFalse(statenachine.message_prepared({}))
        self.assertFalse(statenachine.message_prepared(oth))
        self.assertFalse(statenachine.message_prepared(blank))
        self.assertFalse(statenachine.
                         message_prepared(notsending))
        self.assertTrue(statenachine.
                        message_prepared(yessending))
        ## Check answer
        answer = statenachine.get_message(self.db_handlers, self.message)
        self.assertTrue(answer['sending_status'])
        # Difficult tests to predict
#        endstatename = statenachine.endStates[0]
#        expected_answer =\
#            statenachine.states[endstatename].chooser.candidates[0]
#        self.assertEquals(answer['message'], expected_answer['message'])

        ## Flatten structure computation
        statenachine.create_abspathname()
        statenachine.create_buttom_states_list()

    def test_onestatemachine(self):
        # Testing one state machine
        pars = copy.copy(self.answering_state_pars)
        state = GeneralConversationState(**pars)
        statenachine = ConversationStateMachine(name='statenachine1',
                                                states=[state],
                                                startState=state.name,
                                                endStates=state.name)
        self.assert_statemachine(statenachine)

#    def test_chainstatemachine(self):
#        # Testing two state machine
#        pars = copy.copy(self.answering_state_pars)
#        pars['transition'] = ('questioning_state', lambda m: 0)
#        endstate = GeneralConversationState(**pars)
#        pars = copy.copy(self.asking_state)
#        initstate = GeneralConversationState(**pars)
#        statenachine = ConversationStateMachine(name='statenachine2',
#                                                states=[initstate, endstate],
#                                                startState=initstate.name,
#                                                endStates=endstate.name)
#        self.assert_statemachine(statenachine)
#
#        # Testing longer chain
#        pars = copy.copy(self.answering_state_pars)
#        endstate = GeneralConversationState(**pars)
#
#        pars = copy.copy(self.shadow_state_pars)
#        pars['transition'] = ('questioning_state', lambda m: 0)
#        innnerstate = GeneralConversationState(**pars)
#
#        pars = copy.copy(self.asking_state)
#        pars['transition'] = ('shadow_state', lambda m: 0)
#        initstate = GeneralConversationState(**pars)
#
#        states = [initstate, innnerstate, endstate]
#
#        statenachine = ConversationStateMachine(name='statenachine3',
#                                                states=states,
#                                                startState=initstate.name,
#                                                endStates=endstate.name)
#        self.assert_statemachine(statenachine)
#
#    def test_onebasicnesting_statemachine(self):
#        # Testing complex chain
#        pars = copy.copy(self.answering_state_pars)
#        endstate = GeneralConversationState(**pars)
#
#        pars = copy.copy(self.shadow_state_pars)
#        pars['transition'] = ('questioning_state', lambda m: 0)
#        innnerstate = GeneralConversationState(**pars)
#
#        pars = copy.copy(self.asking_state)
#        pars['transition'] = ('shadow_state', lambda m: 0)
#        initstate = GeneralConversationState(**pars)
#
#        states = [initstate, innnerstate, endstate]
#
#        statenachine = ConversationStateMachine(name='statenachine3',
#                                                states=states,
#                                                startState=initstate.name,
#                                                endStates=endstate.name)
#        ## Nested machine
#        statenachine = ConversationStateMachine(name='1nested_statemachine',
#                                                states=[statenachine],
#                                                startState='statenachine3',
#                                                endStates='statenachine3')
#        self.assert_statemachine(statenachine)

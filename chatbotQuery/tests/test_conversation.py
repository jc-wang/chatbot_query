
import unittest
import copy
#import mock
from unittest import mock
import numpy as np
from itertools import product

from chatbotQuery.conversation import GeneralConversationState, CheckerState,\
    QuerierState, StoringState, TalkingState, QuestioningState,\
    AnsweringState, BaseConversationState, ConversationStateMachine
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

        def get_variables_pos_values(vars):
            pos_values = []
            for v in vars:
                pos_values.append(self.pos_values[self.variables.index(v)])
            return pos_values
        self.get_variables_pos_values = get_variables_pos_values

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
        db_handlers.get_last_query = lambda: {}
        self.db_handlers = db_handlers

        ## Messages
        self.messages =\
            [{'message': 'NO!', 'collection': False, 'from': 'user',
              'collection': False}]
        self.messages = [ChatbotMessage(m) for m in self.messages]

    def assert_base_state(self, state):
        for m in self.messages:
            state.get_message(self.db_handlers, m)
            ## Check message
            state.next_states
        state.restart()
        ## Check formatters
        state._format_tags(None)
        state._format_tags("None")

    def assert_general_state(self, state):
        for m in self.messages:
            message = state.get_message(self.db_handlers, m)
            self.assertIn('message', message)
            self.assertIn('collection', message)
            ## Check properties
            state.sending_status
            state.currentChildrenState
            state.questions
        state.restart()
        ## Check formatters
        state._format_tags(None)
        state._format_tags("None")
        state._add_tags(m)
        state.flag_question_answer = 2
        with self.assertRaises(Exception):
            state.get_message(self.db_handlers, message)
        state.running_times = 2
        state.counts = 3
        state._manage_limited_runs()
        with self.assertRaises(Exception):
            state.create_buttom_states_list(None)

    def test_base_states(self):
        class EchoStateMachine(BaseConversationState):
            def get_message(self, db_handlers, message):
                message['from'] = 'bot'
                return message
#        pos_values = [('baseState'), (None, [['yes', 'no'], lambda x: 0])]
        variables = ['name', 'transition']
        pos_values = self.get_variables_pos_values(variables)
        ## Looping over possibilities
        for p in product(*pos_values):
            pars = dict(zip(variables, p))
            state = EchoStateMachine(**pars)
            self.assert_base_state(state)

    def test_general_trasitions(self):
        # Testing state methods
        for p in product(*self.pos_values):
            pars = dict(zip(self.variables, p))
            state = GeneralConversationState(**pars)
            self.assert_base_state(state)
            self.assert_general_state(state)

    def test_talking(self):
        ## Definition of possible inputs
        variables = ['name', 'detector', 'chooser', 'transition',
                     'tags', 'shadow']
        pos_values = self.get_variables_pos_values(variables)
        # Testing transtion
        for p in product(*pos_values):
            pars = dict(zip(variables, p))
            # Case 0
            pars['asker'] = True
            state = TalkingState(**pars)
            self.assert_base_state(state)
            self.assert_general_state(state)
            # Case 1
            pars['asker'] = False
            state = TalkingState(**pars)
            self.assert_base_state(state)
            self.assert_general_state(state)

    def test_questioning(self):
        ## Definition of possible inputs
        variables = ['name', 'detector', 'chooser', 'transition',
                     'tags', 'shadow']
        pos_values = self.get_variables_pos_values(variables)
        # Testing transtion
        for p in product(*pos_values):
            pars = dict(zip(variables, p))
            state = QuestioningState(**pars)
            self.assert_base_state(state)
            self.assert_general_state(state)

    def test_answering(self):
        ## Definition of possible inputs
        variables = ['name', 'detector', 'chooser', 'transition',
                     'tags', 'shadow']
        pos_values = self.get_variables_pos_values(variables)
        # Testing transtion
        for p in product(*pos_values):
            pars = dict(zip(variables, p))
            state = AnsweringState(**pars)
            self.assert_base_state(state)
            self.assert_general_state(state)

    def test_storing(self):
        ## Definition of possible inputs
        variables = ['name', 'querier', 'transition']
        pos_values = self.get_variables_pos_values(variables)
        variables = ['name', 'storer', 'transition']
        # Testing transtion
        for p in product(*pos_values):
            pars = dict(zip(variables, p))
            state = StoringState(**pars)
            self.assert_base_state(state)
            self.assert_general_state(state)

    def test_querying(self):
        ## Definition of possible inputs
        variables = ['name', 'detector', 'chooser', 'transition', 'tags',
                     'querier']
        pos_values = self.get_variables_pos_values(variables)
        # Testing transtion
        for p in product(*pos_values):
            pars = dict(zip(variables, p))
            state = QuerierState(**pars)
            self.assert_base_state(state)
            self.assert_general_state(state)

    def test_checking(self):
        ## Definition of possible inputs
        variables = ['name', 'querier', 'transition']
        pos_values = self.get_variables_pos_values(variables)
        variables = ['name', 'checker', 'transition']
        # Testing transtion
        for p in product(*pos_values):
            pars = dict(zip(variables, p))
            state = CheckerState(**pars)
            self.assert_base_state(state)
            self.assert_general_state(state)


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

    def assert_statemachine(self, statemachine):
        ## Check class
        statemachine.set_machine()
        self.assertIsNotNone(statemachine.currentChildernState)
#        statemachine.restart()

        oth = ChatbotMessage.from_candidates_messages({'message': '0'})
        blank = ChatbotMessage.from_candidates_messages({'message': ''})
        notsending = ChatbotMessage.\
            from_candidates_messages({'message': ',',
                                      'sending_status': False})
        yessending = ChatbotMessage.\
            from_candidates_messages({'message': ',',
                                      'sending_status': True})
        self.assertFalse(statemachine.message_prepared(None))
        self.assertFalse(statemachine.message_prepared({}))
        self.assertFalse(statemachine.message_prepared(oth))
        self.assertFalse(statemachine.message_prepared(blank))
        self.assertFalse(statemachine.
                         message_prepared(notsending))
        self.assertTrue(statemachine.
                        message_prepared(yessending))
        ## Check answer
        answer = statemachine.get_message(self.db_handlers, self.message)
        self.assertTrue(answer['sending_status'])
        # Difficult tests to predict
#        endstatename = statemachine.endStates[0]
#        expected_answer =\
#            statemachine.states[endstatename].chooser.candidates[0]
#        self.assertEquals(answer['message'], expected_answer['message'])
        if not statemachine.runned:
            statemachine.get_message(self.db_handlers, notsending)
            self.assertTrue(answer['sending_status'])
        if not statemachine.runned:
            statemachine.get_message(self.db_handlers, yessending)
            self.assertTrue(answer['sending_status'])

        ## Flatten structure computation
        statemachine.create_abspathname()
        statemachine.create_buttom_states_list()

    def test_onestatemachine(self):
        # Testing one state machine
        pars = copy.copy(self.answering_state_pars)
        state = GeneralConversationState(**pars)
        statemachine = ConversationStateMachine(name='statemachine1',
                                                states=[state],
                                                startState=state.name,
                                                endStates=state.name)
        self.assert_statemachine(statemachine)

    def test_shortchainstatemachine(self):
        # Testing two state machine
        pars = copy.copy(self.answering_state_pars)
        pars['transition'] = ('questioning_state', lambda m: 0)
        endstate = GeneralConversationState(**pars)
        pars = copy.copy(self.asking_state)
        initstate = GeneralConversationState(**pars)
        statemachine = ConversationStateMachine(name='statemachine2',
                                                states=[initstate, endstate],
                                                startState=initstate.name,
                                                endStates=endstate.name)
        self.assert_statemachine(statemachine)

    def test_longchainstatemachine(self):
        # Testing longer chain
        pars = copy.copy(self.answering_state_pars)
        endstate = GeneralConversationState(**pars)

        pars = copy.copy(self.shadow_state_pars)
        pars['transition'] = ('answering_state', lambda m: 0)
        innnerstate = GeneralConversationState(**pars)

        pars = copy.copy(self.asking_state)
        pars['transition'] = ('shadow_state', lambda m: 0)
        initstate = GeneralConversationState(**pars)

        states = [initstate, innnerstate, endstate]

        statemachine = ConversationStateMachine(name='statemachine3',
                                                states=states,
                                                startState=initstate.name,
                                                endStates=endstate.name)
        self.assert_statemachine(statemachine)

    def test_onenestedchainstatemachine(self):
        # Testing longer chain
        pars = copy.copy(self.answering_state_pars)
        endstate = GeneralConversationState(**pars)

        pars = copy.copy(self.shadow_state_pars)
        pars['transition'] = ('answering_state', lambda m: 0)
        innnerstate = GeneralConversationState(**pars)

        pars = copy.copy(self.asking_state)
        pars['transition'] = ('shadow_state', lambda m: 0)
        initstate = GeneralConversationState(**pars)

        statemachine_init = ConversationStateMachine(name='statemachine_init',
                                                     states=[initstate],
                                                     startState=initstate.name,
                                                     endStates=initstate.name)
        statemachine_me = ConversationStateMachine(name='statemachine_med',
                                                   states=[innnerstate],
                                                   startState=innnerstate.name,
                                                   endStates=innnerstate.name)
        statemachine_end = ConversationStateMachine(name='statemachine_endit',
                                                    states=[endstate],
                                                    startState=endstate.name,
                                                    endStates=endstate.name)
        states = [statemachine_init, statemachine_me, statemachine_end]
        statemachine = ConversationStateMachine(name='statemachine_endit',
                                                states=states,
                                                startState='statemachine_init',
                                                endStates='statemachine_endit')
        self.assert_statemachine(statemachine)

    def test_onebasicnesting_statemachine(self):
        # Testing complex chain
        pars = copy.copy(self.answering_state_pars)
        endstate = GeneralConversationState(**pars)

        pars = copy.copy(self.shadow_state_pars)
        pars['transition'] = ('questioning_state', lambda m: 0)
        innnerstate = GeneralConversationState(**pars)

        pars = copy.copy(self.asking_state)
        pars['transition'] = ('shadow_state', lambda m: 0)
        initstate = GeneralConversationState(**pars)

        states = [initstate, innnerstate, endstate]

        statemachine_son = ConversationStateMachine(name='statemachine3',
                                                    states=states,
                                                    startState=initstate.name,
                                                    endStates=endstate.name)
        ## Nested machine
        statemachine = ConversationStateMachine(name='1nested_statemachine',
                                                states=[statemachine_son],
                                                startState='statemachine3',
                                                endStates='statemachine3')
        self.assert_statemachine(statemachine)

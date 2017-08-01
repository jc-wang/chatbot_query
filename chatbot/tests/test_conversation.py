
import unittest
#import mock
from unittest import mock
import numpy as np
from itertools import product

from chatbot.conversation import GeneralConversationState, CheckerState,\
    QuerierState, StoringState, TalkingState
#from chatbot.conversation import RandomChooser, SequentialChooser,\
#    QuerierSizeDrivenChooser, QuerierSplitterChooser
#from chatbot.conversation import BaseQuerier, NullQuerier
#from chatbot.conversation import BaseDetector


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
        while not ((not state.ended) or (i == 10)):
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
        self.message = {'message': 'NO!', 'collection': False}

    def assert_state(self, state):
        i = 0
        message = self.message
        while not ((not state.ended) or (i == 10)):
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
        self.message = {'message': 'NO!', 'collection': False}

    def assert_state(self, state):
        i = 0
        message = self.message
        while not ((not state.ended) or (i == 10)):
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
        self.message = {'message': 'NO!', 'collection': False}

    def assert_state(self, state):
        i = 0
        message = self.message
        while not ((not state.ended) or (i == 10)):
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
        self.message = {'message': 'NO!', 'collection': False}

    def assert_state(self, state):
        i = 0
        message = self.message
        while not ((not state.ended) or (i == 10)):
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
            state = CheckerState(**pars)
            self.assert_state(state)

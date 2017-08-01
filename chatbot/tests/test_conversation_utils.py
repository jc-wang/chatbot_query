
"""
# Standarization:

* Each message has:
  - 'message'
  - 'collection'

* It sould be:
  - 'query' outside 'message' in collection messages.
  - 'selector_types' in each individual messages.

"""

import unittest
#import mock
from unittest import mock
import numpy as np

from chatbot.conversation import TransitionConversationStates,\
    NullTransitionConversation
from chatbot.conversation import RandomChooser, SequentialChooser,\
    QuerierSizeDrivenChooser, QuerierSplitterChooser
from chatbot.conversation import BaseQuerier, NullQuerier
from chatbot.conversation import BaseDetector


class Test_Transitions(unittest.TestCase):
    """Testing and standarization transitions between states.
    """

    def setUp(self):
        # Create a candidate responses
        self.responses = [{'message': 'Hello! How are you?'},
                          {'message': 'These are test messages'}]
        for e in self.responses:
            e.update({'collection': False})
        # Create transition condition and states
        self.function = lambda x: int('w' in x['message'].lower())
        self.transitions = ['yes', 'no']
        # Create a mock
        conversationstate = mock.Mock()
        conversationstate.configure_mock(name="example")
        self.conversationstate = conversationstate

    def assert_transition(self, transtion):
        for message in self.responses:
            statename = transtion.next_state(message)
            self.assertIsInstance(statename, str)

    def test_general_trastions(self):
        # Testing transtion
        general_transition = TransitionConversationStates(self.transitions,
                                                          self.function)
        general_transition.set_current_state(self.conversationstate)
        self.assert_transition(general_transition)

    def test_null_transition(self):
        # Null testing transtion
        null_transition = NullTransitionConversation()
        null_transition.set_current_state(self.conversationstate)
        self.assert_transition(null_transition)

    def test_base_transitions(self):
        ## WARNING: from_transition_info CANNOT be initilize from a
        ## NullTransitionConversation instance
        pars = [self.transitions, self.function]
        transition = TransitionConversationStates.from_transition_info(pars)
        transition.set_current_state(self.conversationstate)
        self.assert_transition(transition)

        transition =\
            TransitionConversationStates.from_transition_info(transition)
        transition.set_current_state(self.conversationstate)
        self.assert_transition(transition)

        transition = TransitionConversationStates.from_transition_info(None)
        transition.set_current_state(self.conversationstate)
        self.assert_transition(transition)


class Test_Choosers(unittest.TestCase):
    """Testing and standarization over chooser administrator.

    Standarization
    --------------
    ### Input requires:
    * keys:
      - 'message'
      - 'collection'
      - 'selector_types'
      - 'query'

    ### Tasks:
    * Choose a response considering the last message bunch and their properties
    * Put `selector_types` into these new message.

    ### Output requires:
    * keys:
      - 'message'
      - 'collection'
      - 'selector_types'
      - 'query'

    """

    def setUp(self):
        self.candidate_messages = [{'message': 'Nein?', 'tag': 5},
                                   {'message': 'It could be valid', 'tag': 0}]
        for e in self.candidate_messages:
            e.update({'query_idxs': np.random.random(10), 'collection': False,
                      'selector_types': np.random.random(2), 'query': 0})

    def check_general_chooser(self, chooser, collection=True):
        ## Checking individual messages
        for m in self.candidate_messages:
            response = chooser.choose(m)
            self.assertIsInstance(response, dict)
            self.assertIn('message', response)
            self.assertIn('collection', response)
            self.assertIn('selector_types', response)

        ## Checking collection of messages
        if collection:
            m2 = {'message': self.candidate_messages, 'collection': True,
                  'selector_types': m['selector_types']}
            response = chooser.choose(m2)
            self.assertIsInstance(response, dict)
            self.assertIn('message', response)
            self.assertIn('collection', response)
            self.assertIn('selector_types', response)

    def test_random_chooser(self):
        chooser = RandomChooser(self.candidate_messages)
        self.check_general_chooser(chooser)

    def test_sequential_chooser(self):
        chooser = SequentialChooser(self.candidate_messages)
        self.check_general_chooser(chooser)

    def test_sizedriven_chooser(self):
        chooser =\
            QuerierSizeDrivenChooser(self.candidate_messages, type_var='tag',
                                     cond=lambda x: x-x,
                                     query_var='query_idxs')
        self.check_general_chooser(chooser, False)

    def test_splitter_chooser(self):
        chooser =\
            QuerierSplitterChooser(self.candidate_messages, type_var='tag',
                                   cond=lambda x: len(x)-len(x),
                                   query_var='query_idxs')
        self.check_general_chooser(chooser, False)


class Test_Querier(unittest.TestCase):
    """Test interaction with databases administrator.

    ### Input requires:
    * keys:
      - 'message'
      - 'collection'
      - 'selector_types'

    ### Tasks:
    * Query database using the message.
    * Put `query` into these new message.

    ### Output requires:
    * keys:
      - 'message'
      - 'collection'
      - 'selector_types'
      - 'query'

    """

    def setUp(self):
        self.messages =\
            [{'message': '', 'selector_types': 0, 'collection': False},
             {'message': '', 'selector_types': 0, 'collection': False}]

        self.query_info =\
            {'query': {'query_idxs': np.random.randint(0, 10000, 10),
                       'query_names': [],
                       'answer_names': []}}
        self.querier = lambda x, y: self.query_info

    def check_querier(self, querier):
        ## Individual messages
        for m in self.messages:
            message = querier.make_query(None, m)
            self.assertIn('query', message)
        ## Collection messages (Not supported: Always the last message)
#        message = querier.make_query(None, self.messages)
#        self.check_output_message(message)

    def test_base_querier(self):
        querier = BaseQuerier(self.querier)
        self.check_querier(querier)
        ## Class method initialization
        querier = BaseQuerier.from_querier_info(None)
        self.check_querier(querier)
        querier = BaseQuerier.from_querier_info(self.querier)
        self.check_querier(querier)
        querier = BaseQuerier.from_querier_info(querier)
        self.check_querier(querier)

    def test_null_querier(self):
        querier = NullQuerier()
        self.check_querier(querier)


class Test_Detection(unittest.TestCase):
    """

    Standarization
    --------------
    ### Input requires:
    * keys:
      - 'message'
      - 'collection'

    ### Tasks:
    * Detection detects the possible descriptors given a detector
    * Write the possible detection in the message.

    ### Output requires:
    * keys:
      - 'message'
      - 'collection'
      - 'selector_types'

    """

    def setUp(self):
        self.answers = [{'message': 'Nein?', 'tag': 5},
                        {'message': 'It could be valid', 'tag': 4}]
        for e in self.answers:
            e.update({'query_idxs': np.random.random(10), 'collection': False})
        self.postypes = ['a', 'b']
        self.detector = lambda x: np.random.random(2)

    def assert_correct_response(self, response):
        self.assertIn('message', response)
        self.assertIn('collection', response)
        self.assertIn('selector_types', response)

    def check_detector(self, detector):
        # Detect from individual input messages
        for answer in self.answers:
            response = detector.detect(answer)
            ## Check structure
            self.assert_correct_response(response)

        # Detect from a input bunch of messages
        collected_answers = {'selector_types': [], 'message': self.answers,
                             'collection': True}
        response = detector.detect(collected_answers)
        ## Check structure
        self.assert_correct_response(response)

    def test_basedetector(self):
        detector0 = BaseDetector()
        self.check_detector(detector0)
        detector1 = BaseDetector(self.postypes, self.detector)
        self.check_detector(detector1)
        detector2 = BaseDetector.from_detector_info(None)
        self.check_detector(detector2)
        detector3 = BaseDetector.from_detector_info(detector2)
        self.check_detector(detector3)
        detector4 = BaseDetector.from_detector_info([[0], lambda x: [0]])
        self.check_detector(detector4)


import unittest
import copy
#import mock
import numpy as np
from unittest import mock

from chatbotQuery import ChatbotMessage


class Test_Transitions(unittest.TestCase):
    """Testing and standarization transitions between states.
    """

    def setUp(self):
        # Create a candidate responses
        responses = [{'message': 'Hello! How are you?'},
                     {'message': 'These are test messages'}]
        responses = [ChatbotMessage.from_candidates_messages(r)
                     for r in responses]
        for e in responses:
            e.update({'collection': False, 'from': 'user', 'tags': ['0']})
        responses.append({'message': copy.copy(responses), 'collection': True,
                          'from': 'bot', 'tags': ['9'],
                          'query': {'query_idxs': [np.array([], np.int64)],
                                    'query_names': [np.array([], np.int64)],
                                    'query_result': [np.array([], np.int64)]}})
        responses.append({'message': copy.copy(responses[:-1]),
                          'from': 'bot', 'collection': True,
                          'query': {'query_idxs': [np.array([], np.int64)],
                                    'query_names': [np.array([], np.int64)],
                                    'query_result': [np.array([], np.int64)]}})
        self.responses = [ChatbotMessage(r) for r in responses]
        self. responses += [ChatbotMessage.fake_user_message()
                            for i in range(3)]
        r_mes = ChatbotMessage.from_candidates_messages({'query': None,
                                                         'message': ''})
        self.responses += [r_mes]

        # Create transition condition and states
        self.function = lambda x: int('w' in x['message'].lower())
        self.transitions = ['yes', 'no']
        # Create a mock
        conversationstate = mock.Mock()
        conversationstate.configure_mock(name="example")
        self.conversationstate = conversationstate

    def test_chatbotmessage(self):
        for r in self.responses:
            r.last_message_text
            if r['collection']:
                r.format_message({'a': 'b'})
            r.from_message(r)
            r.from_message(dict(r))
            r.keep_query(r)
            for r_aux in self.responses:
                r.keep_query(r_aux)
                r.collapse_message(r_aux)
                r.reflect_message(r_aux)

            r._preformat_collection_messages()

            r.add_tags('tag')
            r.add_tags(['tag'])

            r.is_prepared()

        r = ChatbotMessage.from_candidates_messages({'message': '',
                                                     'sending_status': False})
        r._preformat_collection_messages()
        r = ChatbotMessage.\
            from_candidates_messages({'message': [{'message': ''}],
                                      'sending_status': False})
        r.last_message_text

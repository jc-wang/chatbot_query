
import unittest
#import mock
from unittest import mock

from chatbot import ChatbotMessage


class Test_Transitions(unittest.TestCase):
    """Testing and standarization transitions between states.
    """

    def setUp(self):
        # Create a candidate responses
        self.responses = [{'message': 'Hello! How are you?'},
                          {'message': 'These are test messages'}]

        for e in self.responses:
            e.update({'collection': False, 'from': 'user'})
        # Create transition condition and states
        self.function = lambda x: int('w' in x['message'].lower())
        self.transitions = ['yes', 'no']
        # Create a mock
        conversationstate = mock.Mock()
        conversationstate.configure_mock(name="example")
        self.conversationstate = conversationstate

    def test_chatbotmessage(self):
        responses = [ChatbotMessage.from_candidates_messages(r)
                     for r in self.responses]

        for r in responses:
            r.last_message_text
            r.format_message({'a': 'b'})
            r.from_message(r)
            r.from_message(dict(r))

            r._preformat_collection_messages()

            r.add_tags('tag')
            r.add_tags(['tag'])

        r = ChatbotMessage.from_candidates_messages({'message': '',
                                                     'sending_status': False})
        r._preformat_collection_messages()
        r = ChatbotMessage.\
            from_candidates_messages({'message': [{'message': ''}],
                                      'sending_status': False})
        r.last_message_text


import os
import unittest
import copy
#import mock
from unittest import mock
from itertools import product

from chatbotQuery import ChatbotMessage
from chatbotQuery.ui import ProfileUser, HandlerConvesationDB


class Test_ProfileUser(unittest.TestCase):
    """Testing and standarization Profile user DB.
    """

    def setUp(self):
        self.variables = ['profile_user']
        self.pos_profile_user = [(None, {})]

    def test_profileuser(self):
        for p in product(*self.pos_profile_user):
            pars = dict(zip(self.variables, p))
            prof = ProfileUser(**pars)
            prof = ProfileUser(prof)


class Test_HandlerConvesationDB(unittest.TestCase):

    def setUp(self):
        ## Create a mock db_handler
        # Create a mock DBAPI
        def get_reflection_query(message):
            return {'query': {'query_idxs': None, 'query_names': None},
                    'answer_names': None}
        dbapi = mock.Mock()
        dbapi.get_reflection_query = get_reflection_query

        # Db_handlers possibility
        self.variables = ['profile_user', 'databases']
        self.db_handlers = [(None, {}),
                            (None, dbapi, {'db': dbapi})]

        self.variables_query_messages = ['number', 'sender', 'tag']
        self.pos_query_messages = [(2, 10), (None, 'prueba'), (None, 'sender')]

        ## Messages setting
        m0 = {'message': 'a', 'sending_status': True, 'from': 'bot'}
        m00 = {'message': 'a', 'sending_status': False, 'from': 'bot'}
        m1 = {'message':
              [{'message': 'a', 'sending_status': False, 'from': 'user'},
               {'message': 'b', 'sending_status': True, 'from': 'bot'}],
              'collection': True, 'sending_status': True, 'from': 'bot'}
        m2 = {'message': 'a', 'from': 'user', 'sending_status': False}
        m3 = {'sending_status': True, 'from': 'user',
              'message': [ChatbotMessage.from_candidates_messages(m00),
                          ChatbotMessage.from_candidates_messages(m0),
                          ChatbotMessage(m2)]}
        m4 = ChatbotMessage(copy.copy(m3))
        m5 = ChatbotMessage(copy.copy(m3))
        m4['posting_status'] = True
        m5['posting_status'] = False
        m4['answer_status'] = True
        m5['answer_status'] = True

        self.messages =\
            [ChatbotMessage.from_candidates_messages(m0),
             ChatbotMessage(m1),
             ChatbotMessage(m2), ChatbotMessage(m3), m4, m5]
        self.message = {'message': 'No', 'collection': True, 'query': {}}

        package_path =\
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.example_db_hand_yaml =\
            os.path.join(os.path.dirname(package_path),
                         'examples/example_dbparser/db_handler_parameters.yml')

    def assert_handlerdb(self, handlerdb):
        for m in self.messages:
            for p in product(*self.pos_query_messages):
                pars = dict(zip(self.variables_query_messages, p))
                handlerdb.query_past_messages(**pars)
            handlerdb.message_in(m, 'db')
            handlerdb.message_out(m, 'db')
            handlerdb.message_in(m)
            handlerdb.message_out(m)
            if 'db' in handlerdb.databases:
                handlerdb.store_query(m, 'db')
        handlerdb.query_past_queries(2)
        handlerdb.query_last_queries(2)

    def test_handling_db(self):
        for p in product(*self.db_handlers):
            pars = dict(zip(self.variables, p))
            handler_db = HandlerConvesationDB(**pars)
            self.assert_handlerdb(handler_db)

    def test_handling_db_from_file(self):
        handler_db = HandlerConvesationDB.from_file(self.example_db_hand_yaml)
        self.assert_handlerdb(handler_db)

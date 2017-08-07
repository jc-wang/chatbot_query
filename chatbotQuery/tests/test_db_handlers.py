
import unittest
#import mock
from unittest import mock
from itertools import product

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
        self.message = {'message': 'No', 'collection': True, 'query': {}}

    def assert_handlerdb(self, handlerdb):
        for i in range(10):
            for p in product(*self.pos_query_messages):
                pars = dict(zip(self.variables_query_messages, p))
                handlerdb.query_past_messages(**pars)
            handlerdb.message_in(self.message, 'db')
            handlerdb.message_out(self.message, 'db')
            handlerdb.message_in(self.message)
            handlerdb.message_out(self.message)
            if 'db' in handlerdb.databases:
                handlerdb.store_query(self.message, 'db')
        handlerdb.query_past_queries(2)

    def test_handling_db(self):
        for p in product(*self.db_handlers):
            pars = dict(zip(self.variables, p))
            handler_db = HandlerConvesationDB(**pars)
            self.assert_handlerdb(handler_db)


import unittest
import sys
import io
import os
import copy
#from io import StringIO
from unittest import mock
from itertools import product

from chatbotQuery import ChatbotMessage
from chatbotQuery.ui import HandlerConvesationUI, TerminalUIHandler


class StringIO(io.StringIO):
    """
    A "safely" wrapped version
    """

    def __init__(self, value=''):
        value = value.encode('utf8', 'backslashreplace').decode('utf8')
        io.StringIO.__init__(self, value)

    def write(self, msg):
        io.StringIO.write(self, msg.encode(
            'utf8', 'backslashreplace').decode('utf8'))


class Test_HandlerConvesationDB(unittest.TestCase):

    def setUp(self):
        ## HandlerDB
        handler_db = mock.Mock()
        handler_db.message_in = lambda m: None
        handler_db.message_out = lambda m: None
        handler_db.store_query = lambda m: None
        self.handler_db = handler_db

        ## Conversation machines
        def factory_conversations(out_m, runned):
            conversation_machine = mock.Mock()
            conversation_machine.setted = False
            conversation_machine.set_machine = lambda: None
            conversation_machine.get_message = lambda h, m: out_m
            conversation_machine.runned = runned
            return conversation_machine
        self.factory_conversations = factory_conversations

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

        self.pos_inputs =\
            [[None]+self.messages, [True]]

        package_path =\
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.example_yaml =\
            os.path.join(os.path.dirname(package_path),
                         'examples/example_dbparser/dbparser_parameter.yml')
        self.example_db_hand_yaml =\
            os.path.join(os.path.dirname(package_path),
                         'examples/example_dbparser/db_handler_parameters.yml')

    def stub_stdin(self, inputs):
        stdin = sys.stdin

        def cleanup():
            sys.stdin = stdin

        self.addCleanup(cleanup)
        sys.stdin = StringIO(inputs)

    def stub_stdouts(self):
        stderr = sys.stderr
        stdout = sys.stdout

        def cleanup():
            sys.stderr = stderr
            sys.stdout = stdout

        self.addCleanup(cleanup)
        sys.stderr = StringIO()
        sys.stdout = StringIO()

    def assert_UI(self, handler_ui_class):
        for p in product(*self.pos_inputs):
            conversation = self.factory_conversations(*p)
            handler_ui = handler_ui_class(self.handler_db, conversation)
            handler_ui.run()

    def test_generalmockUI(self):
        class_patch_ui = 'chatbotQuery.ui.HandlerConvesationUI'
        with mock.patch(class_patch_ui, autospec=True) as MockUI:
            ## Definition of the class
            instance = MockUI.return_value
            instance.ask = lambda m: {}
            instance.post = lambda m: None
            self.assert_UI(MockUI)

    def test_generalUI(self):

        class GeneralUI4test(HandlerConvesationUI):
            def post(self, message):
                return None

            def ask(self, message):
                return {}

            def breaker(self, message):
                if message is None:
                    return True
                return False

            def keep_loop(self, message):
                return False

        self.assert_UI(GeneralUI4test)

    def test_CLI(self):
        for m_i in self.messages:
            for m in self.messages:
                self.stub_stdin('input')
                self.stub_stdouts()
                conversation =\
                    self.factory_conversations(m_i, self.pos_inputs[1][0])
                cli_handler = TerminalUIHandler(self.handler_db, conversation)
                cli_handler.interact(m, False)
                cli_handler.interact(m, True)
                cli_handler._reflection_information(m_i, m)

                self.doCleanups()

    def test_instantiation_from_configurationfiles(self):
        HandlerConvesationUI.\
            from_configuration_files(self.example_db_hand_yaml,
                                     self.example_yaml)

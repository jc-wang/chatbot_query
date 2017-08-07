
import unittest
import sys
import io
#from io import StringIO
from unittest import mock
from itertools import product

from chatbot import ChatbotMessage
from chatbot.ui import HandlerConvesationUI, TerminalUIHandler


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
        def factory_conversations(out_m, runned, ended):
            conversation_machine = mock.Mock()
            conversation_machine.setted = False
            conversation_machine.set_machine = lambda: None
            conversation_machine.get_message = lambda h, m: out_m
            conversation_machine.runned = runned
            conversation_machine.ended = ended
            return conversation_machine
        self.factory_conversations = factory_conversations

        m0 = {'message': 'a', 'sending_status': True, 'from': 'bot'}
        m1 = {'message':
              [{'message': 'a', 'sending_status': False, 'from': 'user'},
               {'message': 'b', 'sending_status': True, 'from': 'bot'}],
              'collection': True, 'sending_status': True, 'from': 'bot'}
        m2 = {'message': 'a', 'from': 'user', 'sending_status': False}
        m3 = {'sending_status': True, 'from': 'user',
              'message': [ChatbotMessage.from_candidates_messages(m0),
                          ChatbotMessage(m2)]}

        self.messages =\
            [ChatbotMessage.from_candidates_messages(m0),
             ChatbotMessage(m1),
             ChatbotMessage(m2), ChatbotMessage(m3)]

        self.pos_inputs =\
            [[None]+self.messages, [True], [True]]

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
        class_patch_ui = 'chatbot.ui.HandlerConvesationUI'
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

        self.assert_UI(GeneralUI4test)

    def test_CLI(self):
        for m in self.messages:
            self.stub_stdin('input')
            self.stub_stdouts()
            conversation = self.factory_conversations(self.pos_inputs[0][0],
                                                      self.pos_inputs[1][0],
                                                      self.pos_inputs[2][0])
            cli_handler = TerminalUIHandler(self.handler_db, conversation)
            cli_handler.interact(m, False)
            cli_handler.interact(m, True)

            self.doCleanups()

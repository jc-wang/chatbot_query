
"""

"""

import time
from chatbot import ChatbotMessage
from chatbot.ui.flask_utils import run_flask_app_conversation


class HandlerConvesationUI(object):
    """Object which manage the whole converation interaction.

    It should be able to:
    * Interact with the IO sources
    * Tracking and managing the interaction
    * Store messages

    """

    def __init__(self, handler_db, conversation_machine):
        self.handler_db = handler_db
        if not conversation_machine.setted:
            conversation_machine.set_machine()
        self.conversation_machine = conversation_machine

#    def _reflection_information(self, message, pre_message):
#        for key in pre_message:
#            if key not in ['message', 'from', 'time']:
#                message[key] = pre_message[key]
#        return message

    def run(self, message={}):
        answer = {}
        message = self._format_message(message)
        while self.keep_loop(message):
#            self._reflection_information(message, answer)
            self.handler_db.message_in(message)
            answer = self.conversation_machine.get_message(self.handler_db,
                                                           message)
            if self.breaker(answer):
                for post in answer.get_all_messages():
                    self.post(post)
                break
            self.handler_db.message_out(answer)
            message = self.ask(answer)
            message = self._format_message(message)

    def _format_message(self, message):
        if message == {}:
            message = {'message': ''}
        if 'collection' not in message:
            message['collection'] = False
        message['from'] = 'user'
        message = ChatbotMessage(message)
        return message

    def breaker(self, answer):
        if self.conversation_machine.runned:
            return True
        if answer is None:
            return True
        else:
            if 'message' not in answer:
                return True
            return False

    def keep_loop(self, message):
        if message is not None:
            return True
        if self.conversation_machine.ended:
            return True
        return False


class TerminalUIHandler(HandlerConvesationUI):

    def ask(self, message):
#        if message['message'] == list:
#            for i in range(len(message['message'])-1):
#                self.post(message['message'][i])
#            if message['message']['answer_status']:
#                return self.ask(message['message'][-1])
#            else:
#                self.post(message['message'][-1])
#                return None
        for m in message.get_post():
            self.get_post(m)
        for m in message.get_last_post():
            wait_time = min([len(m['message'])*1/15., 3])
            time.sleep(wait_time)
            response = input(m['message']+"\n")
            if response is not None:
                response = {'message': response}
        return response

    def post(self, message):
        if type(message['message']) == list:
            for m in message['message']:
                self.post(m)
        else:
            wait_time = min([len(message['message'])*1/15., 1])
            time.sleep(wait_time)
            print(message['message'])


class FlaskUIHandler(HandlerConvesationUI):

    def __init__(self, handler_db, conversation_machine):
        super().__init__(handler_db, conversation_machine)

    def ask(self, message={}):
        while message is not None:
            self.handler_db.message_in(message,
                                       self.conversation_machine.next_tags)
            answer = self.conversation_machine.get_message(self.handler_db,
                                                           message)
            if answer is None:
                break
            self.handler_db.message_out(answer,
                                        self.conversation_machine.next_tags)
            wait_time = min([len(answer['message'])*1/15., 3])
            time.sleep(wait_time)
            return answer

    def run(self, message={}):
        run_flask_app_conversation(self.ask)

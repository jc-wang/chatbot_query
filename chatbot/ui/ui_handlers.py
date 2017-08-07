
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

    def run(self, message={}):
        answer = {}
        message = self._format_message(message)
        while self.keep_loop(message):
            self._reflection_information(message, answer)
            self.handler_db.message_in(message)
            answer = self.conversation_machine.get_message(self.handler_db,
                                                           message)
            self.handler_db.store_query(answer)
            if self.breaker(answer):
                try:
                    for post in answer.get_all_messages():
                        self.interact(post, False)
                except:
                    pass
                break
            self.handler_db.message_out(answer)
            message = self.interact(answer)
            message = self._format_message(message)

    def interact(self, message, response=True):
        if not response:
            ## Force posting
            if type(message['message']) == list:
                for m in message['message']:
                    self.post(m)
            else:
                self.post(message)
        else:
            ## Asking
            for m in message.get_post():
                self.post(m)
            for m in message.get_last_post():
                if not m['sending_status']:
                    self.post(m)
                else:
                    response = self.ask(m)
                    return response

    def _reflection_information(self, message, pre_message):
        message = ChatbotMessage(message)
        if 'answer_status' in pre_message:
            if pre_message['answer_status']:
                message = message.reflect_message(pre_message)
        if 'posting_status' in pre_message:
            if not pre_message['posting_status']:
                message = message.keep_query(pre_message)
        else:
            message = message.keep_query(pre_message)
        return message

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
#        if message is not None:
#            return True
        if self.conversation_machine.ended:
            return True
        return False


class TerminalUIHandler(HandlerConvesationUI):

    def ask(self, message):
        self._create_time_delay(message['message'])
        response = input(self._format_messageText(message, False))
        if response is not None:
            response = {'message': response}
        return response

    def post(self, message):
        self._create_time_delay(message['message'])
        print(self._format_messageText(message, True))

    def _format_messageText(self, message, post):
        if message['from'] == 'user':
            return message['message']
        else:
            if post:
                return 'Bot:  '+message['message']
            else:
                return 'Bot:  '+message['message']+'\n'+'User: '

    def _create_time_delay(self, messageText):
        wait_time = min([len(messageText)*1/15., 1.5])
        time.sleep(wait_time)


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

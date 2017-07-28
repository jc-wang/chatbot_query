
"""

"""

import time


class HandlerConvesationUI(object):
    """Object which manage the whole converation interaction.

    It should be able to:
    * Interact with the IO sources
    * Tracking and managing the interaction
    * Store messages

    """

    def __init__(self, handler_db, conversation_machine):
        self.handler_db = handler_db
        self.conversation_machine = conversation_machine

#    def _reflection_information(self, message, pre_message):
#        for key in pre_message:
#            if key not in ['message', 'from', 'time']:
#                message[key] = pre_message[key]
#        return message

    def run(self, message={}):
        answer = {}
        while self.keep_loop(message):
#            self._reflection_information(message, answer)
            self.handler_db.message_in(message,
                                       self.conversation_machine.next_tags)
            answer = self.conversation_machine.get_message(self.handler_db,
                                                           message)
            if self.breaker(answer):
                break
            self.handler_db.message_out(answer,
                                        self.conversation_machine.next_tags)
            message = self.ask(answer)

    def breaker(self, answer):
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
        wait_time = min([len(message['message'])*1/15., 3])
        time.sleep(wait_time)
        response = input(message['message']+"\n")
        if response is not None:
            response = {'message': response}
        return response


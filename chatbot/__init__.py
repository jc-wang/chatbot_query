
"""

TODO
----
Decorator for message collections

"""
import copy


class ChatbotMessage(dict):
    """
    Compulsary elements
    -------------------
    - message
    - collection
    - from [user, bot]

    """

    def __init__(self, message):
        self.update({'message': '', 'collection': False})
        self.update(message)
        assert('from' in self)
        assert('message' in self)
        assert('collection' in self)

    @classmethod
    def from_message(cls, message):
        if isinstance(message, ChatbotMessage):
            return message
        return cls(message)

    @classmethod
    def from_candidates_messages(cls, message):
        message.update({'from': 'bot'})
        if type(message['message']) == str:
            message['collection'] = False
        elif type(message['message']) == list:
            message['collection'] = True
        return cls(message)

    @classmethod
    def fake_user_message(self):
        return ChatbotMessage({'from': 'user'})

    @property
    def last_message_text(self):
        if self['collection']:
            return self['message'][-1]['message']
        else:
            return self['message']

    def get_last_post(self):
        _, last_post = self._filter_message_2_post()
        for p in last_post:
            yield p

    def get_post(self):
        posts, _ = self._filter_message_2_post()
        for p in posts:
            yield p

    def get_all_messages(self):
        for p in self.get_post():
            yield p
        for p in self.get_last_post():
            yield p

    def format_message(self, format_information):
        if self['collection']:
            self['message'][-1]['message'] =\
                self['message'][-1]['message'].format(**format_information)
        else:
            self['message'] = self['message'].format(**format_information)
        return self

    def reflect_message(self, pre_message):
        for key in pre_message:
            if key not in ['message', 'from', 'time', 'answer_status',
                           'sending_status', 'collection', 'posting_status']:
                self[key] = pre_message[key]
        return self

    def reflect_metadata(self, pre_message):
        for key in pre_message:
            if key not in self:
                if key not in ['message', 'from', 'time', 'answer_status',
                               'sending_status', 'collection']:
                    self[key] = pre_message[key]
        return self

    def keep_query(self, pre_message):
        if 'query' in pre_message:
            if 'query' in self:
                if self['query'] is None:
                    self['query'] = pre_message['query']
            else:
                self['query'] = pre_message['query']
        return self

    def _if_possible_send(self, message):
        logi = True
        logi = logi and (message['from'] == 'bot')
        logi = logi and (message['message'] != '')
        return logi

    def _filter_message_2_post(self):
        posts, last_post = [], []
        if self['collection']:
            messages = [m for m in self['message']
                        if self._if_possible_send(m)]
            if len(messages):
                last_post = [messages[-1]]
                posts = messages[:-1]
        else:
            if self._if_possible_send(self):
                last_post = [copy.copy(self)]
        return posts, last_post

    def _detect_message_sending_status(self):
        if 'sending_status' in self:
            return self['sending_status']
        return True

    def _preformat_collection_messages(self):
        if not self._detect_message_sending_status():
            if not self['collection']:
                self['message'] = [copy.copy(self)]
                self['collection'] = True
                return self
        return self

    def _is_prepared(self, message):
        if message['message'] == '':
            return False
        if 'sending_status' in self:
            return self['sending_status']
        if 'posting_status' in self:
            return self['posting_status']

    def is_prepared(self):
        if self['collection']:
            return any([self._is_prepared(e) for e in self['message']])
        else:
            return self._is_prepared(self)
        return False

    def add_tags(self, tags):
        if tags is not None and (type(tags) in [list, str]):
            tags = tags if type(tags) == list else [tags]
            if 'tags' in self:
                old_tags = self['tags']
                old_tags += tags
                old_tags = list(set(old_tags))
                self['tags'] = old_tags
            else:
                self['tags'] = tags
            if self['collection']:
                if 'tags' in self['message'][-1]:
                    old_tags = self['message'][-1]['tags']
                    old_tags += tags
                    old_tags = list(set(old_tags))
                    self['tags'][-1]['tags'] = old_tags
                else:
                    self['message'][-1]['tags'] = tags

        return self

    def collapse_message(self, message):
        self._preformat_collection_messages()
        if self['collection']:
            messagestext = copy.copy(self['message'])
            if message['collection']:
                messagestext += message['message']
            else:
                messagestext.append(message)
            self.update(message)
            self['message'] = messagestext
            self['collection'] = True
            self.check_message()
            return self
        else:
            output_message = copy.copy(message)
            output_message['collection'] = False
            if 'query' in message:
                output_message['query'] = message['query']
            output_message =\
                ChatbotMessage.from_candidates_messages(output_message)
            output_message.check_message()
            return output_message

    def add_selector_types(self, selector_types):
        ## Store results in message
        self['selector_types'] = selector_types
        return self

    def add_entry_to_last_message(self, entry_var, var):
        self[entry_var] = var
        if self['collection']:
            self['message'][-1][entry_var] = var
        return self

    def structure_answer(self):
        ## Input selector types
        if self['collection']:
            self['message'][-1]['selector_types'] = self['selector_types']
        self.check_message()
        return self

    def check_message(self):
        if self['collection']:
            assert(all([isinstance(m, dict) for m in self['message']]))
            assert(all([isinstance(m['message'], str)
                        for m in self['message']]))
        else:
            assert(isinstance(self['message'], str))

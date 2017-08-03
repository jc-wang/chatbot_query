

import time

datetime_format = '%Y-%m-%d %H:%m:%S %z'


class ProfileUser(object):
    """Profile user of the chatbot.
    """

    def __init__(self, profile_user):
        if profile_user is None:
            self.profile = {}
        elif isinstance(profile_user, ProfileUser):
            self.profile = profile_user.profile
        else:
            assert(type(profile_user) == dict)
            self.profile = profile_user


class HandlerConvesationDB(object):
    """Object which tracks the whole converation interaction.

    It should be able to:
    * Interact with the DBs
    * Tracking the interaction
    * Store messages

    """

    def __init__(self, profile_user=None, logging_file=None, databases=None):
        self.profile_user = ProfileUser(profile_user)
        self.messagesDB = []
        self.queriesDB = []
        self.databases = {}
        if databases is None:
            pass
        elif type(databases) == dict:
            self.databases.update(databases)
        else:
            ## It should be DataBaseAPI object
            self.databases = {'db': databases}

    def store_query(self, message, database='db'):
        if 'query' in message:
            if message['query'] is not None:
                query_info = self.databases['db'].get_reflection_query(message)
                query_info['time'] = time.strftime(datetime_format)
                self.queriesDB.append(query_info)

    def message_in(self, message, tags=None):
        ## Message handling
        message = self._enrich_message(message, 'user', tags)
        self._record_conversation(message)

    def message_out(self, message, tags=None):
        ## Message handling
        message = self._enrich_message(message, 'bot', tags)
        self._record_conversation(message)

    def _enrich_message(self, message, sender, tags):
#        if message == {}:
#            message = {'message': ''}
        message['from'] = sender
        if tags is not None:
            message['tags'] = tags
        message['time'] = time.strftime(datetime_format)
        return message

    def _record_conversation(self, message):
        self.messagesDB.append(message)

    def query_past_messages(self, number=1, sender=None, tag=None):
        retrieved = []
        i = 1
        while (len(retrieved) < number) and (i <= (len(self.messagesDB))):
            m = self.messagesDB[-i]
            logi = True
            if tag is not None:
                if 'tags' in m:
                    logi = logi and (tag in m['tags'])
                else:
                    logi = False
            if sender is not None:
                logi = logi and (m['from'] == sender)
            if logi:
                retrieved.append(m)
            i += 1
        return retrieved

    def query_past_queries(self, number=1):
        retrieved = []
        i = 1
        while (len(retrieved) < number) and (i <= (len(self.messagesDB))):
            m = self.messagesDB[-i]
            if 'query' in m:
                if m['query']:
                    retrieved.append(m)
            i += 1
        return retrieved

    def get_last_query(self):
        ## Temporal
        return {}

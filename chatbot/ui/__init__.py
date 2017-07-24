
import time
import copy
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import LSHForest, NearestNeighbors


datetime_format = '%Y-%m-%d %H-%m-%S %z'


class ProfileUser(object):
    """Profile user of the chatbot.
    """

    def __init__(self, profile_user):
        if profile_user is None:
            self.profile = {}
        elif isinstance(profile_user, ProfileUser):
            self.profile = profile_user.profile
        else:
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
        if databases is None:
            self.databases = {}
        elif isinstance(databases, DataBaseAPI):
            self.databases = {'db': databases}
        else:
            assert(type(databases) == dict)
            self.databases.update(databases)

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


class HandlerConvesationUI(object):
    """Object which manage the whole converation interaction.

    It should be able to:
    * Interact with the IO sources
    * Tracking and managing the interaction
    * Store messages

    """

    def __init__(self, handler_db, converation_machine):
        self.handler_db = handler_db
        self.converation_machine = converation_machine

    def run(self, message={}):
        while message is not None:
            self.handler_db.message_in(message,
                                       self.converation_machine.next_tags)
            answer = self.converation_machine.get_message(self.handler_db,
                                                          message)
            if answer is None:
                break
            self.handler_db.message_out(answer,
                                        self.converation_machine.next_tags)
            message = self.ask(answer)


class TerminalUIHandler(HandlerConvesationUI):

    def ask(self, message):
        response = input(message['message']+"\n")
        if response is not None:
            response = {'message': response}
        return response


class DataBaseAPI(object):

    def __init__(self, data_path, main_var, label_var):
        self.data = pd.read_csv(data_path, index_col=0)
        self.main_var = main_var
        self.label_var = label_var
#        self.encoded_variables, self.matrix, self.ids =\
#            encode(self.data)
        self.tfidf_vec = TfidfVectorizer(list(self.data[main_var]),
                                         ngram_range=(1, 4))
        data_sp = self.tfidf_vec.fit_transform(list(self.data[main_var]))
        self.ret = NearestNeighbors(metric='cosine', algorithm='brute')
        self.ret.fit(data_sp)
        self.description = "{productname} of the brand {brand}."

    def query(self, keywords):
        ids = self.ret.radius_neighbors(self.tfidf_vec.transform(keywords).A,
                                        0.75)
        ids = ids[1][0]
        return ids

    def get(self, ids):
        assert(len(ids) == 1)
        d = dict(zip(['productname', 'brand'], self.data.loc[ids].as_matrix()))
        row = copy.copy(self.description).format(**d)
        return row

    def get_label(self, ids):
        labels = self.data.loc[self.data.index[ids], self.label_var]
        labels = [str(e) for e in labels.as_matrix().around(decimals=2)]
        return labels

    def get_names(self, ids):
        names = self.data.loc[self.data.index[ids], self.main_var]
        names = [e for e in names.as_matrix()]
        return names

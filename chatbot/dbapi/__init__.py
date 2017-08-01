
import copy
import pandas as pd
import numpy as np
import functools

from os.path import isfile

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
#from sklearn.feature_extraction.text import CountVectorizer
#from sklearn.neighbors import LSHForest


class DataBaseAPI(object):

    def __init__(self, data_info, type_vars, responses_formatter):
        if isinstance(data_info, pd.DataFrame):
            self.data = data_info
        else:
            assert(isfile(data_info))
            self.data = pd.read_csv(data_info, index_col=0)

        ## Type vars: dictionary with 'main_var', 'cat_vars', 'label_var'
        assert(all([v in type_vars
                    for v in ['main_var', 'cat_vars', 'label_var']]))
        self.type_vars = type_vars
#        self.main_var = main_var
#        self.label_var = label_var
#        self.encoded_variables, self.matrix, self.ids =\
#            encode(self.data)

        ## Data transformed
        names = list(self.data[self.type_vars['main_var']['name']])
        categories = dict([(c, list(self.data[c].unique()))
                           for c in type_vars['cat_vars']['name']])
#        cats_ids = dict([(c, dict([(v,
#                                    list(self.data.index[self.data[c] == v]))
#                                   for v in categories[c]]))
#                         for c in type_vars['cat_vars']['name']])
        dummy_idxs = np.arange(self.data.shape[0])
        cats_ids = dict([(c, dict([(v, dummy_idxs[np.array(self.data[c] == v)])
                                   for v in categories[c]]))
                         for c in type_vars['cat_vars']['name']])
        self.categories = categories
        self.cats_ids = cats_ids
        self.cats_codenames = dict(zip(type_vars['cat_vars']['name'],
                                       type_vars['cat_vars']['codename']))
        ## Main parameters
        self.main_vectorizer = TfidfVectorizer(ngram_range=(1, 4))
        self.main_ret = NearestNeighbors(metric='cosine', algorithm='brute')
        data_sp = self.main_vectorizer.fit_transform(names)
        self.main_ret.fit(data_sp)

        self.cat_vectorizers, self.cat_rets = {}, {}
        for var, vals in categories.items():
#            self.cat_vectorizers[var] = CountVectorizer(binary=True)
#            self.cat_rets[var] = NearestNeighbors(radius=.9, metric='hamming')
            self.cat_vectorizers[var] = DummyVectorizer()
            self.cat_rets[var] = DummyRetriever(radius=1)
#            data_sp = self.cat_vectorizers[var].fit_transform(categories[var])
#            self.cat_rets[var].fit(data_sp)
            data_sp = self.cat_vectorizers[var].fit_transform(categories[var])
            self.cat_rets[var].fit(data_sp)

        self.responses_formatter = responses_formatter

    def query(self, keywords, pre=None):
        ids = self.complete_query(keywords, pre)
#        ids = self.ret.radius_neighbors(self.vectorizer.transform(keywords).A,
#                                        0.75)
#        ids = ids[1]
        return ids

    def complete_query(self, keywords, pre=None):
        queried = {}
        ## Main query
        ids = self.main_ret.radius_neighbors(self.main_vectorizer.
                                             transform(keywords).A, 0.75)
#        queried['main_var'] = {self.type_vars['main_var']['name']: ids}
        queried['main_var'] = ids[1]
        ## Category queries
        queried_cat = {}
        for var, vals in self.categories.items():
            queried_cat[var] =\
                self.cat_rets[var].radius_neighbors(self.cat_vectorizers[var].
                                                    transform(keywords))
        queried['cat_vars'] = queried_cat
        if pre is not None:
            queried = self.query_intersection(queried, pre)
        return queried

    def query_intersection(self, queried0, queried1):
        ids_cat = []
        for c in queried0['cat_vars']:
            ids_cat_c = np.array([], dtype=np.int64)
            for c_i in queried1['cat_vars'][c][0]:
                ids_cat_c =\
                    np.union1d(self.cats_ids[c][self.categories[c][c_i]],
                               ids_cat_c)
            ids_cat.append(ids_cat_c)
        pos_q1 = np.union1d(*ids_cat).astype(np.int64)

        queried0['main_var'] = [np.intersect1d(queried0['main_var'][0],
                                               pos_q1)]
        return queried0

#    def get(self, ids):
#        assert(len(ids) == 1)
#        d = dict(zip(['productname', 'brand'], self.data.loc[ids].as_matrix()))
#        row = copy.copy(self.description).format(**d)
#        return row

    def get_label(self, ids):
        labels = self.data.loc[self.data.index[ids['main_var'][0]],
                               self.type_vars['label_var']['name']]
        labels = [str(e) for e in np.round(labels.as_matrix(), decimals=2)]
        return labels

    def get_names(self, ids):
        names = {}
        main_names = self.data.loc[self.data.index[ids['main_var'][0]],
                                   self.type_vars['main_var']['name']]
        names['main_var'] = [e for e in main_names.as_matrix()]
        names_cat = {}
        for c in self.type_vars['cat_vars']['name']:
            names_cat[c] =\
                [self.categories[c][i]
                 for i in ids['cat_vars'][c][0]]
        names['cat_vars'] = names_cat
        return names

    def get_reponses(self, ids_names):
       ## Initialization of utils
        responses = {}
#        main_code = self.type_vars['main_var']['codename']
#        cat_code = self.cats_codenames
        category_joiner = self.responses_formatter['join_cats'][0]
        category_code = self.responses_formatter['join_cats'][1]

        ## Building possible responses
        responses[self.responses_formatter['main_var'][1]] = self.\
            responses_formatter['main_var'][0](ids_names['main_var'])
        responses_cat = []
        for c, f in self.responses_formatter['cat_vars'].items():
            if len(ids_names['cat_vars'][c]):
                responses_cat.append(f(self.cats_codenames[c],
                                       ids_names['cat_vars'][c]))
        responses[category_code] = category_joiner(responses_cat)

        return responses

    def get_label_reponses(self, ids):
        ids_names = self.get_names(ids)
       ## Initialization of utils
        responses = {}
#        main_code = self.type_vars['main_var']['codename']
#        cat_code = self.cats_codenames
        category_joiner = self.responses_formatter['join_cats'][0]
        category_code = self.responses_formatter['join_cats'][1]

        ## Building possible responses
        responses[self.responses_formatter['label_var'][1]] = self.\
            responses_formatter['label_var'][0](ids_names['main_var'],
                                                self.get_label(ids))
        responses_cat = []
        for c, f in self.responses_formatter['cat_vars'].items():
            if len(ids_names['cat_vars'][c]):
                responses_cat.append(f(self.cats_codenames[c],
                                       ids_names['cat_vars'][c]))
        responses[category_code] = category_joiner(responses_cat)
        return ids_names, responses

    def get_query_info(self, keywords, pre=None, label=False):
        ids = self.query(keywords, pre)
        query_info = self.get_query_info_from_ids(ids, label)
        return query_info

    def get_query_responses(self, ids, label=False):
        if label:
            ids_names, responses = self.get_label_reponses(ids)
        else:
            ids_names = self.get_names(ids)
            responses = self.get_reponses(ids_names)
        return ids_names, responses

    def get_query_info_from_ids(self, ids, label=False):
        ids_names, responses = self.get_query_responses(ids, label)
        query_info = {'query': {'query_idxs': ids, 'query_names': ids_names},
                      'answer_names': responses}
        return query_info

    def get_reflection_query(self, message):
        query_info = {'query': {'query_idxs': message['query']['query_idxs'],
                      'query_names': message['query']['query_names']},
                      'answer_names': message['answer_names']}
        return query_info


class DummyRetriever(object):

    def __init__(self, radius):
        self.n_coinc = radius

    def fit(self, categories):
        self.categories = categories
        return self

    def radius_neighbors(self, keywords):
        retrieved = [[] for _ in range(len(keywords))]
        for i in range(len(self.categories)):
            k = 0
            for kwrds in keywords:
                n_coinc = 0
                for keyword in kwrds:
                    if keyword in self.categories[i]:
                        n_coinc += 1
                        if self.n_coinc == n_coinc:
                            retrieved[k].append(i)
                            k += 1
                            break
                else:
                    k += 1
        retrieved = [np.array(ret) for ret in retrieved]
        return retrieved


class DummyVectorizer(object):

    def __init__(self):
        pass

    def fit(self, data):
        return self

    def transform(self, data):
        return [e.replace(' &', '').strip().lower().split(' ')
                for e in data]

    def fit_transform(self, data):
        self.fit(data)
        return self.transform(data)

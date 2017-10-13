
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

    def __init__(self, data_info, type_vars, responses_formatter,
                 parameter_formatter={}):
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
        self.parameter_formatter = parameter_formatter

    @classmethod
    def from_parameters(cls, parameters):
        return DataBaseAPI(**parameters)

    def query(self, keywords, pre=None, label=None):
        pars = self._format_parameters(keywords, pre, label)
        # TODO: Use in the future
        ifchanged = self.changed_labels(pre, pars)

        ids, query_result = self.complete_query(keywords, pre)
        if self.empy_ids(ids['main_var']):
            if pre is not None:
                ids['main_var'] = pre['query_idxs']['main_var']
        pars['query_result'] = query_result
        return ids, pars

    def empy_ids(self, ids):
        return any([(len(e) == 0) for e in ids])

    def complete_query(self, keywords, pre=None):
        queried = self.columwise_query(keywords)
        queried, query_result = self.join_w_prequeries(queried, pre)
        return queried, query_result

    def columwise_query(self, keywords):
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
        return queried

    def _evaluate_queried(self, queried):
        cat = not all([len(v[0]) == 0 for c, v in queried['cat_vars'].items()])
        main_len = len(queried['main_var'][0])
        ## WARNING: Hardcoded arbitrary quantity: len(self.data)/5
        main = (main_len != 0) or (main_len >= 8)
        if main:
            query_result = {'query_type': 'elements'}
        elif cat:
            query_result = {'query_type': 'categories'}
        else:
            query_result = {'query_type': 'none'}
        return query_result

    def join_w_prequeries(self, queried, pre):
        query_result = self._evaluate_queried(queried)
        if pre is not None:
            q_pre_type = pre['query_result']['query_type']
            q_type = query_result['query_type']
            if (q_pre_type == 'elements') and (q_type == 'elements'):
                queried =\
                    self._cross_element_element_query(queried,
                                                      pre['query_idxs'])
                query_result = {'query_type': 'elements'}
            elif ((q_pre_type == 'elements') and (q_type == 'categories')
                  or (q_pre_type == 'categories') and (q_type == 'elements')):
                if q_pre_type == 'elements':
                    queried =\
                        self._cross_category_element_query(pre['query_idxs'],
                                                           queried)
                else:
                    queried =\
                        self._cross_category_element_query(queried,
                                                           pre['query_idxs'])
                query_result = {'query_type': 'elements'}
            elif (q_pre_type == 'categories') and (q_type == 'categories'):
                queried =\
                    self._cross_category_category_query(queried,
                                                        pre['query_idxs'])
                query_result = {'query_type': 'elements'}
            else:
                # Query and query type of the last one
                pass
        return queried, query_result

    def _cross_category_element_query(self, ids_ele, ids_cat):
        ## Get the indices associated at each category
        ids_i_cat = []
        for c in ids_cat['cat_vars']:
            ids_cat_each = []
            for i in range(len(ids_cat['cat_vars'][c])):
                ids_cat_c = np.array([], dtype=np.int64)
                for c_i in ids_cat['cat_vars'][c][i]:
                    ids_cat_c =\
                        np.union1d(ids_cat_c,
                                   self.cats_ids[c][self.categories[c][c_i]])
                ids_cat_each.append(copy.copy(ids_cat_c))
            ids_i_cat.append(ids_cat_each)
        ## Get indices for each query
        ids_i = []
        for i in range(len(ids_i_cat[0])):
            aux = np.union1d(*[ids[i] for ids in ids_i_cat]).astype(np.int64)
            ids_i.append(aux)
        ## Union in its own query
        for i in range(len(ids_i)):
            ids_i[i] = np.union1d(ids_i[i], ids_cat['main_var'][i])

        ## Intersection with indices
        for i in range(len(ids_i)):
            ids_i[i] = np.intersect1d(ids_ele['main_var'][i], ids_i[i])

        ## Categories
        cat_ids = {}
        for c in self.categories:
            cat_ids[c] =\
                [np.array([], dtype=np.int64) for i in range(len(ids_i))]
        ids = {'main_var': ids_i, 'cat_vars': cat_ids}

        return ids

    def _cross_element_element_query(self, ids0, ids1):
        for i in range(len(ids0['main_var'])):
            ids0['main_var'][i] = np.intersect1d(ids0['main_var'][i],
                                                 ids1['main_var'][i])
        return ids0

    def _cross_category_category_query(self, ids0, ids1):
        for c in ids0['cat_vars']:
            for i in range(len(ids0['cat_vars'][c])):
                ids0['cat_vars'][c][i] = np.union1d(ids0['cat_vars'][c][i],
                                                    ids1['cat_vars'][c][i])
        return ids0

#    def query_intersection(self, queried0, queried1):
#        ids_cat = []
#        for c in queried0['cat_vars']:
#            ids_cat_c = np.array([], dtype=np.int64)
#            for c_i in queried1['cat_vars'][c][0]:
#                ids_cat_c =\
#                    np.union1d(self.cats_ids[c][self.categories[c][c_i]],
#                               ids_cat_c)
#            ids_cat.append(ids_cat_c)
#        pos_q1 = np.union1d(*ids_cat).astype(np.int64)
#
#        queried0['main_var'] = [np.intersect1d(queried0['main_var'][0],
#                                               pos_q1)]
#        return queried0

#    def get(self, ids):
#        assert(len(ids) == 1)
#        d = dict(zip(['productname', 'brand'],
#                     self.data.loc[ids].as_matrix()))
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

    def get_query_info(self, keywords, pre=None, label=None):
        ids, pars = self.query(keywords, pre, label)
        query_info = self.get_query_info_from_ids(ids, **pars)
        return query_info

    def get_query_responses(self, ids, label=False):
        if label:
            ids_names, responses = self.get_label_reponses(ids)
        else:
            ids_names = self.get_names(ids)
            responses = self.get_reponses(ids_names)
        return ids_names, responses

    def get_query_info_from_ids(self, ids, label=False, query_result={}):
        ids_names, responses = self.get_query_responses(ids, label)
        query_info = {'query': {'query_idxs': ids, 'query_names': ids_names,
                                'query_pars': {'label': label},
                                'query_result': query_result},
                      'answer_names': responses}
        return query_info

    def get_reflection_query(self, message):
        query_info = {'query': {'query_idxs': message['query']['query_idxs'],
                      'query_names': message['query']['query_names'],
                      'query_pars': message['query']['query_pars'],
                      'query_result': message['query']['query_result']},
                      'answer_names': message['answer_names']}
        return query_info

    def _format_parameters(self, keywords, pre, label):
        pars = {}
        for l in self.parameter_formatter:
            pars[l] = self.parameter_formatter[l](keywords, pre)
        if 'label' not in pars:
            pars['label'] = False
        if pre is not None:
#            if 'query' in pre:
#                if pre['query'] is not None:
#                    pars = pre['query']['query_pars']
            if 'query_pars' in pre:
                pars = pre['query_pars']
        if label:
            pars['label'] = True

        return pars

    def changed_labels(self, pre, pars):
        labels_old = False
        if pre is not None:
            if 'query' in pre:
                if pre['query'] is not None:
                    labels_old = pre['query']['query_pars']
        new_labels = False
        if 'label' in pars:
            new_labels = pars['label']
        return (not labels_old) and new_labels


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

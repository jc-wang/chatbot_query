# -*- coding: utf-8 -*-

import unittest
import pandas as pd
import os
import copy

from chatbot.dbapi import DataBaseAPI


### Auxiliar functions
def category_joiner(l):
    if len(l) == 0:
        return ''
    elif len(l) == 1:
        return l[0]
    else:
        return ', '.join(l[0:len(l)-1])+' and '+l[-1]


def joiner_brands(code, l):
    if len(l) == 1:
        s = "of a "+l[0]+"'s "+code
    else:
        s = "between the brands like "+category_joiner(l)
    return s


def joiner_categories(code, l):
    if len(l) == 1:
        s = "of a "+l[0]+"'s "+code
    else:
        s = "between the categories like "+category_joiner(l)
    return s


def price_q_keywords(keywords, pre):
    from stemming.porter2 import stem
    from textblob import TextBlob
    words = ['price', 'cost']
    if type(keywords) == list:
        keywords = copy.copy(keywords[0])
    text = TextBlob(keywords)
    logi = any([word in [stem(w) for w in text.stripped.split()]
                for word in words])
    return logi


class Test_DataBaseAPI(unittest.TestCase):
    """Testing and standarization of the interface of DBAPI.
    """

    def setUp(self):
        type_vars =\
            {'main_var': {'name': 'Product Name',
                          'codename': 'productname'},
             'cat_vars': {'name': ['Brand', 'Category'],
                          'codename': ['brand', 'category']},
             'label_var': {'name': 'Subscription Plan'}}
        responses_formatter =\
            {'main_var': (lambda l: ''.join(['\n    * '+s for s in l]),
                          'query_productnames'),
             'cat_vars': {'Brand': joiner_brands,
                          'Category': joiner_categories},
             'label_var': (lambda l, p: ''.join(['\n    * '+r+': '+s+"€"
                                                 for r, s in zip(l, p)]),
                           'query_productnames'),
             'join_cats': (category_joiner, 'query_catnames')
             }
        parameter_formatter =\
            {'label': price_q_keywords}
        ## Test the constructor
        datafile = os.path.join(os.path.abspath(__file__),
                                '../../data/products.csv')
        datafile = os.path.abspath(datafile)

#        data = DataBaseAPI(pd.read_csv(datafile, index_col=0), type_vars,
#                           responses_formatter)
        self.data = DataBaseAPI(datafile, type_vars, responses_formatter,
                                parameter_formatter)

        ## Get keywords for queries
        keywords_cat = []
        for e in self.data.categories.keys():
            keywords_cat += self.data.categories[e]
        keywords_main =\
            list(self.data.data[self.data.type_vars['main_var']['name']])
        self.keywords_cat = keywords_cat
        self.keywords_main = keywords_main

        ## Message
        self.message =\
            {'query': {'query_idxs': [],
                       'query_names': [],
                       'query_result': {},
                       'query_pars': {'label': True}},
             'answer_names': []}

        self.create_pre = lambda x: {'query_idxs': x,
                                     'query_result': {'query_type': True}}

    def query_test(self):
        ## Query for categories
        ids_cat, pars = self.data.query(self.keywords_cat)
        print(ids_cat)
        ids_cat, pars =\
            self.data.query(self.keywords_cat, pre=self.create_pre(ids_cat))

        ## Query main
        ids_main, pars = self.data.query(self.keywords_main)
        ids_main, pars =\
            self.data.query(self.keywords_main, pre=self.create_pre(ids_main))

        ## Cross queries
        ids, pars =\
            self.data.query(self.keywords_cat, pre=self.create_pre(ids_main))
        ids, pars =\
            self.data.query(self.keywords_main, pre=self.create_pre(ids_cat))

        ## Get label
        labels = self.data.get_label(ids)

    def complete_query_test(self):
        q_cat = self.data.get_query_info(self.keywords_cat)
        q_main = self.data.get_query_info(self.keywords_main)

        q_info = self.data.get_query_info(self.keywords_main,
                                          pre=q_cat['query'])
        q_info = self.data.get_query_info(self.keywords_cat,
                                          pre=q_main['query'])
        q_info = self.data.get_query_info(self.keywords_main,
                                          pre=q_cat['query'], label=True)
        q_info = self.data.get_query_info(self.keywords_cat,
                                          pre=q_main['query'], label=True)
        q_info = self.data.get_query_info(self.keywords_cat,
                                          pre=q_info['query'])

    def get_message_reflection_test(self):
        self.data.get_reflection_query(self.message)

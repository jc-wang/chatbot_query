
"""
Collection of auxiliar functions used in `dbquery` example.

"""

import copy
import numpy as np
from chatbotQuery.aux_functions import splitter, create_yes_no_question,\
    create_fixed_condition, yes_no_answer


###############################################################################
###############################################################################
### Auxiliar functions to define dbapi response formatter
### Definition of responses
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


def retrieve_text_main_var(l):
    return ''.join(['\n'+' '*8+'* '+s for s in l])


def retrieve_text_label_var(l, p):
    return ''.join(['\n'+' '*8+'* '+r+': '+s+"€/month" for r, s in zip(l, p)])


###############################################################################


###############################################################################
###############################################################################
### Auxiliar functions to define dbapi response formatter
### Definition of responses
def checker_cats_sure(h, m):
    ## 'Ensure categories' state definition `querier`
    return m


def check_storer_products(h, m):
    ## 'Explore products' state definition `querier`
    q = h.query_past_queries()
    h.store_query(q[0])
    return m


def querier_prices_f(h, m):
    ## 'Shows prices' state definition `querier`
    last_query = h.query_past_queries()
    ids = last_query[0]['query']['query_idxs']
    query_info = h.databases['db'].get_query_info_from_ids(ids,
                                                           label=True)
    return query_info


def storer_query(h, m):
    ## 'Store categories' state definition 'querier'
#    m2 = h.query_past_queries(1)[0]
    m2 = copy.copy(m)
    m2['query']['query_names']['main_var'] = []
    m2['query']['query_idxs']['main_var'] =\
        np.array([np.array([], dtype=np.int64)])
    h.store_query(m2)
    return m


def price_q(response):
    ## TODO: pass into DBAPI: DONE
    from stemming.porter2 import stem
    from textblob import TextBlob
    words = ['price', 'cost']
    text = TextBlob(response['message'])
    logi = any([word in [stem(w) for w in text.stripped.split()]
                for word in words])
    return int(logi)


def cond_queries_db(message):
    ## 'Explore products' state definition `transition`.
    ## Dummy selection to keep exploring in that way or not
    ## The good is to insert a classifier
    ## 0. Query with price and products
    ## 1. Only yes answer
    ## 2. No
    f_no = create_yes_no_question('yes')
    f_price = lambda x: price_q_keywords(x, None)
    m = message['message']
    ms = [e.strip() for e in m.replace('.', ' ').split(' ')]
    if (len(ms) > 10):
        i = 0
    else:
        if f_price(m):
            i = 0
        if not f_no(message):
            i = 0
            if len(ms) == 1:
                i = 1
        else:
            i = 2
    return i


############################ Querier DB definition ############################
def querier_f(h, m):
    ## 'Querier DB' state definition `querier`.
#    m = h.query_past_messages(sender='user', tag='query')[0]['message']
#    keywords = get_keywords(m)
    pre_query = None
    if len(h.queriesDB):
        pre_query = h.queriesDB[-1]['query']
    if 'query' in m:
        pre_query = m['query']
    mess = m['message'] if isinstance(m['message'], list) else [m['message']]
    query_info = h.databases['db'].get_query_info(mess, pre_query)
    return query_info


def cond_selector(query_info):
    ## 'Querier DB' state definition `chooser` function
    i = splitter(len(query_info['main_var'][0]), [0, .1, 1, 5, 20000])
    if i == 3:
        if all([len(v[0]) == 0 for c, v in query_info['cat_vars'].items()]):
            i = 4
#        for c, v in query_info['cat_vars'].items():
#            if len(v) != 0:
#                break
#        i = 4
    return i


def cond_collapser_trans(message):
    ## 'Querier DB' state definition `transition` function
    i = message['level_query']
    collapsing_info = [[0], [1, 2], [3], [4]]
    for j in range(len(collapsing_info)):
        if i in collapsing_info[j]:
            break
    else:
        raise Exception("Not in collapsing info.")
    return j


def closing_check(h, m):
    ## Clean queries
    h.queriesDB.append({'query': None})
    m['query'] = None
#    return h.query_past_messages(sender='user')[0]
    return m

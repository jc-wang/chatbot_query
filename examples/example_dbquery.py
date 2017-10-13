
"""
Example DB QUERY
----------------
Example of a basic query.

How to run the example:

1. Run the script calling as a parameter the table you want to be queried.
2. Take the conversation.

"""

import sys
import copy
from os.path import isfile
import numpy as np

from chatbotQuery.conversation import TalkingState, SequentialChooser,\
    TransitionConversationStates, ConversationStateMachine, QuerierState,\
    QuerierSplitterChooser, CheckerState, StoringState, QuestioningState

from chatbotQuery.aux_functions import create_fixed_condition, splitter,\
    yes_no_answer, create_yes_no_question
from chatbotQuery.ui import HandlerConvesationDB, TerminalUIHandler
from chatbotQuery.dbapi import DataBaseAPI


### DB interface salutations
HELLO_SENTENCES =\
    ["Hi! Nice to see you. I'm here to help you finding products."]

QUESTIONS_SALUT_DB =\
    ["Are you interested in something new? Which products?",
     "Do you want me to find something? Which products?",
     "What are the products you are interested in?"]
QUESTIONS_QUERY_DB =\
    [{'message': "I haven't find anything for you.", 'level_query': 4},
     {'message': 'Are you searching for products {query_catnames}?',
      'level_query': 3},
     {'message': 'We have: {query_productnames}', 'level_query': 2},
     {'message': 'Could be one of these products: {query_productnames}',
      'level_query': 1},
     {'message': 'Your interests are too general.', 'level_query': 0}
     ]
SHOW_PRICES =\
    [{}]

### INTEREST
QUESTIONS_QUEST = ["And what do you want?",
                   "And what are your interests?",
                   "And what bring you here?"]
QUESTIONS_UNDERSTOOD = ["I am not sure what are your interests."]
QUESTIONS_FOCUS = ["Please, focus! What do you want?"]
QUESTIONS_MORE = ['Do you want something more?',
                  'Do you have any other question?',
                  'Anything else?']
QUESTIONS_REASKER = ['Be more specific.']
QUESTION_EXTRA_Q =\
    ["""Do you want to keep exploring that options?
Or there is between these products the one you are searching for."""]
QUESTION_EXTRA_PRODUCTS = ["Which products?"]

QUESTIONS_END_EXPLORE = ['Do you want to keep exploring that options?']

## Questions Goodbye
QUESTIONS_END_SURE = ['Do you want something else?']
QUESTIONS_GOODBYE = ["It's been a pleasure. See you next time!",
                     "Have a nice day!"]


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
    last_query = handler_db.query_past_queries()
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
    query_info =\
        h.databases['db'].get_query_info([m['message']], pre_query)
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
    ## 'Querier DB' state definition `chooser` function
    i = message['level_query']
    collapsing_info = [[0], [1, 2], [3], [4]]
    for j in range(len(collapsing_info)):
        if i in collapsing_info[j]:
            break
    else:
        raise Exception("Not in collapsing info.")
    return j


############################### Store categories ##############################
if __name__ == "__main__":

    # Parse data
    args = sys.argv
    assert(len(args) == 2)
    assert(isfile(args[1]))
    datapath = args[1]

    ############################ Query conversation ###########################
    ## Defining query conversation
    states = []

    ## Defining 'Hello DB' state
    q_hello_db = [{'message': m} for m in QUESTIONS_SALUT_DB]
    cond_hellodb = create_fixed_condition(0)
    trans_states = ['Querier DB']
    trans_hellodb = TransitionConversationStates(trans_states, cond_hellodb)
    chooser_askquery = SequentialChooser(q_hello_db)
    states.append(TalkingState('Hello DB', chooser_askquery, None,
                               tags=['query'], transition=trans_hellodb,
                               shadow=False))

    ## Defining 'Querier DB' state
    chooser_query = QuerierSplitterChooser(QUESTIONS_QUERY_DB, 'level_query',
                                           cond_selector,
                                           query_var='query_idxs')
    trans_states = ['Keep Trying', 'Explore products',
                    'Explore extra products', 'Closing Check']
    query_trans = TransitionConversationStates(trans_states,
                                               cond_collapser_trans)
    states.append(QuerierState('Querier DB', querier_f, chooser_query,
                               tags=['query'], transition=query_trans,
                               shadow=True))

#    ## Defining 'Ensure categories' state
#    q_null = [{'message': ''}]
#    chooser_null = SequentialChooser(q_null)
#    trans_states = ['Querier DB']
#    cond_trans = create_fixed_condition(0)
#    trans_cats_sure = TransitionConversationStates(trans_states, cond_trans)
##    states.append(CheckerState('Ensure categories', checker_cats_sure,
##                               transition=trans_cats_sure))
#    states.append(QuestioningState('Ensure categories',
#                                   chooser_null,
#                                   transition=trans_cats_sure,
#                                   shadow=False))

#    ## Defining 'Store categories' state
#    cond_trans = create_fixed_condition(0)
#    trans_states = ['ReAsker']
#    trans_storename = TransitionConversationStates(trans_states, cond_trans)
#    states.append(StoringState('Store categories', storer_query,
#                               trans_storename))
#
#    ## Defining 'ReAsker' state
#    ## Define a yes_no final asker
#    q_reasker = [{'message': m} for m in QUESTIONS_REASKER]
#    cond_trans = create_fixed_condition(0)
#    trans_states = ['Querier DB']
#    trans_reask = TransitionConversationStates(trans_states, cond_trans)
#    chooser_end = SequentialChooser(q_reasker)
#    states.append(TalkingState('ReAsker', chooser_end,
#                               transition=trans_reask))

    ## Defining 'Explore products' state
    q_explore_products = [{'message': m} for m in QUESTION_EXTRA_Q]
    chooser_explore_products = SequentialChooser(q_explore_products)
    trans_states = ['Querier DB', 'Explore extra products', 'Closing Check']
    trans_explore = TransitionConversationStates(trans_states, cond_queries_db)
#    states.append(CheckerState('Explore products', check_storer_products,
#                               transition=trans_explore))
    states.append(QuestioningState('Explore products',
                                   chooser_explore_products,
                                   transition=trans_explore,
                                   shadow=False))

#    ## Defining 'Reset Query' state
#    # Download questions
#    q_null = [{'message': ''}]
#    chooser_null = SequentialChooser(q_null)
#    trans_states = ['Closing Check']
#    cond_trans = create_fixed_condition(0)
#    trans_null = TransitionConversationStates(trans_states, cond_trans)
#    states.append(QuestioningState('Reset Query', chooser_null,
#                                   transition=trans_null, shadow=True))

    ## Defining 'Explore extra products' state
    q_explore_xtra_products = [{'message': m} for m in QUESTION_EXTRA_PRODUCTS]
    chooser_xtra_explore_products = SequentialChooser(q_explore_xtra_products)
    cond_trans = create_fixed_condition(0)
    trans_states = ['Querier DB']
    trans_explore = TransitionConversationStates(trans_states, cond_trans)
    states.append(QuestioningState('Explore extra products',
                                   chooser_xtra_explore_products,
                                   transition=trans_explore,
                                   shadow=False))

#    ## Defining 'Show Prices' state
#    cond_trans = create_fixed_condition(0)
#    trans_states = ['Keep Trying']
#    chooser_query = QuerierSplitterChooser(QUESTIONS_QUERY_DB, 'level_query',
#                                           lambda x: 2,
#                                           query_var='query_idxs')
#    query_trans = TransitionConversationStates(trans_states, cond_trans)
#    states.append(QuerierState('Show Prices', querier_prices_f, chooser_query,
#                               tags=['query'], transition=query_trans))

    ## Defining 'Keep Trying' state
    ## Define a yes_no keep trying
    q_end_explore = [{'message': m} for m in QUESTIONS_END_EXPLORE]
    trans_states = ['Closing Check', 'Querier DB']
    trans_askmore = TransitionConversationStates(trans_states, yes_no_answer)
    chooser_end = SequentialChooser(q_end_explore)
    states.append(TalkingState('Keep Trying', chooser_end,
                               transition=trans_askmore))

    ## Defining 'Closing Check' state
#    closing_check = lambda h, m: m
    def closing_check(h, m):
        ## Clean queries
        h.queriesDB.append({'query': None})
        m['query'] = None
#        return h.query_past_messages(sender='user')[0]
        return m
    states.append(CheckerState('Closing Check', closing_check))

    ############################ Query conversation
    ### Conversation Query
    cond_query = create_fixed_condition(0)
    trans_states = ['Final Asker']
    trans_query = TransitionConversationStates(trans_states, cond_query)

    query_conv = ConversationStateMachine('Query Conversation', states,
                                          'Hello DB', ['Closing Check'],
                                          transition=trans_query)

    ############################ Hello conversation ###########################
    ### Hello
    q_hello = [{'message': m} for m in HELLO_SENTENCES]
    cond_hello = create_fixed_condition(0)
    trans_states = ['Query Conversation']
    trans_hello = TransitionConversationStates(trans_states, cond_hello)
    chooser_hello = SequentialChooser(q_hello)
    hello_state = TalkingState('Hello', chooser_hello, None,
                               shadow=True)
    hello_conv = ConversationStateMachine('Hello', [hello_state], 'Hello',
                                          ['Hello'], transition=trans_hello)

    ########################## Final Ask conversation #########################
    ## Define a yes_no final asker
    q_end_sure = [{'message': m} for m in QUESTIONS_END_SURE]
    trans_states = ['Say goodbye', 'Query Conversation']

    trans_askcont = TransitionConversationStates(trans_states, yes_no_answer)
    chooser_end = SequentialChooser(q_end_sure)
    final_ask = TalkingState('Final Asker', chooser_end,
                             transition=trans_askcont)
    final_ask_conv = ConversationStateMachine('Final Asker', [final_ask],
                                              'Final Asker', ['Final Asker'],
                                              transition=trans_askcont)

    ######################### Say Goodbye conversation ########################
    ## Say goodbye
    q_goodbye = [{'message': m} for m in QUESTIONS_GOODBYE]
    state_goodbye = TalkingState('Say goodbye', SequentialChooser(q_goodbye))
    goodbye_conv = ConversationStateMachine('Say goodbye', [state_goodbye],
                                            'Say goodbye', ['Say goodbye'])

    ############################### Conversation ##############################
    ## Aggregation of the conversation
    end_states = ['Say goodbye']
    conv_states = [hello_conv, query_conv, final_ask_conv, goodbye_conv]
    conversa = ConversationStateMachine('Conversation', conv_states,
                                        'Hello', end_states)

    ###########################################################################

    ## DB information
    type_vars =\
        {'main_var': {'name': 'Product Name', 'codename': 'productname'},
         'cat_vars': {'name': ['Brand', 'Category'],
                      'codename': ['brand', 'category']},
         'label_var': {'name': 'Subscription Plan'}}
    responses_formatter =\
        {'main_var': (lambda l: ''.join(['\n'+' '*8+'* '+s for s in l]),
                      'query_productnames'),
         'cat_vars': {'Brand': joiner_brands, 'Category': joiner_categories},
         'label_var': (lambda l, p: ''.join(['\n'+' '*8+'* '+r+': '+s+"€/month"
                                             for r, s in zip(l, p)]),
                       'query_productnames'),
         'join_cats': (category_joiner, 'query_catnames')
         }
    parameter_formatter =\
        {'label': price_q_keywords}

    db_api = DataBaseAPI(datapath, type_vars, responses_formatter,
                         parameter_formatter)
    handler_db = HandlerConvesationDB(databases=db_api)

    ## Running a conversation
    handler_ui = TerminalUIHandler(handler_db, conversa)
    handler_ui.run()

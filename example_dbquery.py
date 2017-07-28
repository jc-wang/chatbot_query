
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

from chatbot.conversation import TalkingState, SequencialChooser,\
    TransitionConversationStates, ConversationStateMachine, QuerierState,\
    QuerierSplitterChooser, CheckerState, StoringState, clean_message

from chatbot.aux_functions import create_fixed_condition, splitter,\
    yes_no_answer
from chatbot.ui import HandlerConvesationDB, TerminalUIHandler
from chatbot.dbapi import DataBaseAPI


### DB interface salutations
HELLO_SENTENCES =\
    ["Hi! Nice to see you. I'm here to help you finding products."]

QUESTIONS_SALUT_DB =\
    ["Are you interested in something new?",
     "Do you want me to find something?",
     "What are the products you are interested in?"]
QUESTIONS_QUERY_DB =\
    [{'message': 'I have not find anything for you.', 'level_query': 4},
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

QUESTIONS_END_EXPLORE = ['Do you want to keep exploring that options?']

## Questions Goodbye
QUESTIONS_END_SURE = ['Do you want something else?']
QUESTIONS_GOODBYE = ["It's been a pleasure. See you next time!",
                     "Have a nice day!"]


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


def checker_cats_sure(h, m):
    return m


def price_q(response):
    from stemming.porter2 import stem
    from textblob import TextBlob
    words = ['price', 'cost']
    text = TextBlob(response['message'])
    logi = any([word in [stem(w) for w in text.stripped.split()]
                for word in words])
    return int(logi)


def check_storer_products(h, m):
    q = h.query_past_queries()
    h.store_query(q[0])
    return m


def querier_prices_f(h, m):
        last_query = handler_db.query_past_queries()
        ids = last_query[0]['query']['query_idxs']
        query_info = h.databases['db'].get_query_info_from_ids(ids,
                                                               label=True)
        return query_info


if __name__ == "__main__":

    # Parse data
    args = sys.argv
    assert(len(args) == 2)
    assert(isfile(args[1]))
    datapath = args[1]

    states = []
    ### Conversation querier
    q_hello_db = [{'message': m} for m in QUESTIONS_SALUT_DB]
    cond_hellodb = create_fixed_condition(0)
    trans_states = ['Querier DB']
    trans_hellodb = TransitionConversationStates(trans_states, cond_hellodb)
    chooser_askquery = SequencialChooser(q_hello_db)
    states.append(TalkingState('Hello DB', chooser_askquery, None,
                               tags=['query'], transition=trans_hellodb))

    def querier_f(h, m):
#        m = h.query_past_messages(sender='user', tag='query')[0]['message']
#        keywords = get_keywords(m)
        pre_query = None
        if len(h.queriesDB):
            pre_query = h.queriesDB[0]['query']['query_idxs']
        query_info =\
            h.databases['db'].get_query_info([m['message']], pre_query)
        return query_info

    def cond_selector(query_info):
        i = splitter(len(query_info['main_var'][0]), [0, .1, 1, 5, 20000])
        if i == 3:
            for c, v in query_info['cat_vars'].items():
                if len(v) != 0:
                    break
            else:
                i = 4
        return i

    def cond_collapser_trans(message):
        i = message['level_query']
        collapsing_info = [[0, 4], [1, 2], [3]]
        for j in range(len(collapsing_info)):
            if i in collapsing_info[j]:
                break
        else:
            raise Exception("Not in collapsing info.")
        return j

    chooser_query = QuerierSplitterChooser(QUESTIONS_QUERY_DB, 'level_query',
                                           cond_selector,
                                           query_var='query_idxs')
    trans_states = ['Keep Trying', 'Explore products', 'Ensure categories']
    query_trans = TransitionConversationStates(trans_states,
                                               cond_collapser_trans)
    states.append(QuerierState('Querier DB', querier_f, chooser_query,
                               tags=['query'], transition=query_trans))

    ############################ Storing categories ###########################
    ## Defining 'Ensure categories' state
    trans_states = ['Querier DB', 'Store categories']
    trans_cats_sure = TransitionConversationStates(trans_states, yes_no_answer)
    states.append(CheckerState('Ensure categories', checker_cats_sure,
                               transition=trans_cats_sure))

    def storer_query(h, m):
#        m2 = h.query_past_queries(1)[0]
        m2 = copy.copy(m)
        m2['query']['query_names']['main_var'] = []
        m2['query']['query_idxs']['main_var'] =\
            np.array([np.array([], dtype=np.int64)])
        h.store_query(m2)
        new_m = clean_message(m2)
        return new_m
    cond_trans = create_fixed_condition(0)
    trans_states = ['ReAsker']
    trans_storename = TransitionConversationStates(trans_states, cond_trans)
    states.append(StoringState('Store categories', storer_query,
                               trans_storename))

    ## Define a yes_no final asker
    q_reasker = [{'message': m} for m in QUESTIONS_REASKER]
    cond_trans = create_fixed_condition(0)
    trans_states = ['Querier DB']
    trans_reask = TransitionConversationStates(trans_states, cond_trans)
    chooser_end = SequencialChooser(q_reasker)
    states.append(TalkingState('ReAsker', chooser_end,
                               transition=trans_reask))

    ############################# Storing Products ############################
    ## Defining 'Explore products' state
    trans_states = ['Keep Trying', 'Show Prices']
    trans_prices = TransitionConversationStates(trans_states, price_q)
    states.append(CheckerState('Explore products', check_storer_products,
                               transition=trans_prices))

    ## Defining 'Show Prices' state
    cond_trans = create_fixed_condition(0)
    trans_states = ['Keep Trying']
    chooser_query = QuerierSplitterChooser(QUESTIONS_QUERY_DB, 'level_query',
                                           lambda x: 2,
                                           query_var='query_idxs')
    query_trans = TransitionConversationStates(trans_states, cond_trans)
    states.append(QuerierState('Show Prices', querier_prices_f, chooser_query,
                               tags=['query'], transition=query_trans))

    ################################# Goodbye #################################
    ## Define a yes_no keep trying
    q_end_explore = [{'message': m} for m in QUESTIONS_END_EXPLORE]
    trans_states = ['Closing Check', 'Querier DB']
    trans_askmore = TransitionConversationStates(trans_states, yes_no_answer)
    chooser_end = SequencialChooser(q_end_explore)
    states.append(TalkingState('Keep Trying', chooser_end,
                               transition=trans_askmore))

    ## Defining 'Closing Check' state
#    closing_check = lambda h, m: print(m);m
    def closing_check(h, m):
        return h.query_past_messages(sender='user')[0]
    states.append(CheckerState('Closing Check', closing_check))

    ### Hello
    q_hello = [{'message': m} for m in HELLO_SENTENCES]
    cond_hello = create_fixed_condition(0)
    trans_states = ['Query Conversation']
    trans_hello = TransitionConversationStates(trans_states, cond_hello)
    chooser_hello = SequencialChooser(q_hello)
    hello_state = TalkingState('Hello', chooser_hello, None,
                               transition=trans_hello)
    hello_conv = ConversationStateMachine('Hello', [hello_state], 'Hello',
                                          ['Hello'])
    ## Define a yes_no final asker
    q_end_sure = [{'message': m} for m in QUESTIONS_END_SURE]
    trans_states = ['Say goodbye', 'Query Conversation']

    trans_askcont = TransitionConversationStates(trans_states, yes_no_answer)
    chooser_end = SequencialChooser(q_end_sure)
    final_ask = TalkingState('Final Asker', chooser_end,
                             transition=trans_askcont)
    ## Say goodbye
    q_goodbye = [{'message': m} for m in QUESTIONS_GOODBYE]
    state_goodbye = TalkingState('Say goodbye', SequencialChooser(q_goodbye))

    ### Conversation Query
    trans_states = ['Final Asker', 'Say goodbye']
    trans_query = TransitionConversationStates(trans_states, yes_no_answer)
    query_conv = ConversationStateMachine('Query Conversation', states,
                                          'Hello DB', ['Closing Check'],
                                          transition=trans_query)

    ############################### Conversation ##############################

    end_states = ['Say goodbye']
    conv_states = [hello_state, query_conv, final_ask, state_goodbye]
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
        {'main_var': (lambda l: ''.join(['\n    * '+s for s in l]),
                      'query_productnames'),
         'cat_vars': {'Brand': joiner_brands, 'Category': joiner_categories},
         'label_var': (lambda l, p: ''.join(['\n    * '+r+': '+s+"€"
                                             for r, s in zip(l, p)]),
                       'query_productnames'),
         'join_cats': (category_joiner, 'query_catnames')
         }

    db_api = DataBaseAPI(datapath, type_vars, responses_formatter)
    handler_db = HandlerConvesationDB(databases=db_api)

    ## Running a conversation
    handler_ui = TerminalUIHandler(handler_db, conversa)
    handler_ui.run()

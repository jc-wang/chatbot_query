
"""
Example DB QUERY
----------------
Example of a basic query.

How to run the example:

1. Run the script calling as a parameter the table you want to be queried.
2. Take the conversation.

"""

import sys
from os.path import isfile

from chatbot.conversation import TalkingState, SequencialChooser,\
    TransitionConversationStates, ConversationStateMachine, QuerierState,\
    QuerierSizeDrivenChooser

from chatbot.aux_functions import create_fixed_condition, splitter
from chatbot.ui import HandlerConvesationDB, TerminalUIHandler, DataBaseAPI


### DB interface salutations
QUESTIONS_SALUT_DB =\
    ["Hi! I'm here to help you finding products. What do you want?"]
QUESTIONS_QUERY_DB =\
    [{'message': 'I have not find anything for you.', 'level_query': 3},
     {'message': 'We have {query_names}.', 'level_query': 2},
     {'message': 'Could be one of these objects: {query_names}',
      'level_query': 1},
     {'message': 'Your interests are too general.', 'level_query': 0}
     ]

### INTEREST
QUESTIONS_QUEST = ["And what do you want?",
                   "And what are your interests?",
                   "And what bring you here?"]
QUESTIONS_UNDERSTOOD = ["I am not sure what are your interests."]
QUESTIONS_FOCUS = ["Please, focus! What do you want?"]
QUESTIONS_MORE = ['Do you want something more?',
                  'Do you have any other question?',
                  'Anything else?']


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

    def querier_f(h):
        m = h.query_past_messages(sender='user', tag='query')[0]['message']
#        keywords = get_keywords(m)
        ids = h.databases['db'].query([m])
        ids_names = h.databases['db'].get_names(ids)
        return {'query': ids, 'query_names': ids_names}

    def cond_lvl_query(value):
        return splitter(value, [0, .1, 1, 5, 20000])
    chooser_query = QuerierSizeDrivenChooser(QUESTIONS_QUERY_DB, 'level_query',
                                             cond_lvl_query, query_var='query')
    states.append(QuerierState('Querier DB', querier_f, chooser_query,
                               tags=['query']))

    ### Conversation Query
    end_states = ['Querier DB']
    query_conv = ConversationStateMachine('Query conversation', states,
                                          'Hello DB', end_states)

    db_api = DataBaseAPI(datapath, 'Product Name', 'Subscription Plan')
    handler_db = HandlerConvesationDB(databases=db_api)
    handler_ui = TerminalUIHandler(handler_db, query_conv)
    handler_ui.run()


"""
Example Basic conversation
--------------------------
Example of a basic conversation (hello, goodbye).

How to run the example:

1. Run the script using python3.
2. Take the conversation.


"""

from chatbot.conversation import TalkingState, SequentialChooser,\
    TransitionConversationStates, NullTransitionConversation, BaseDetector,\
    ConversationStateMachine, CheckerState, StoringState, AnsweringState,\
    QuestioningState

from chatbot.aux_functions import create_probsplitter_condition,\
    create_fixed_condition, yes_no_answer

from chatbot.ui import HandlerConvesationDB, TerminalUIHandler


### HELLO QUESTIONS
QUESTIONS_HELLO = ["Hello {username}! Nice to see you again."]

### NAME QUESTIONS
QUESTIONS_NAME = ["Hello! I don't know you. What's your name?"
                  ]
QUESTIONS_NAME_SURE = ["Are you sure '{nameprovided}' is your name?"]
QUESTIONS_RETRY_NAME = ["So, what is your name?",
                        "But, what is your name?",
                        "I am still not knowing your name. What is it?",
                        "Please! Don't play with me :(. What's your name?"]
QUESTIONS_PLEASURE = ["Nice to meet you {username}!"]

### GOODBYE
QUESTIONS_GOODBYE = ["It's been a pleasure. See you next time {username}!",
                     "Have a nice day!"]


if __name__ == "__main__":

    ### Define states
    # ['Asking name', 'Store name', 'Store tempname', 'Refocus name',
    #  'Ensure name', 'Greetings name']
    states = []

    ## Defining 'Asking name' state
    q_username = [{'message': m} for m in QUESTIONS_NAME]

    def dummy_name_detector(message):
        m = message['message']
        if type(m) == list:
            m = message['message'][-1]['message']
        m = m.strip().replace(',', '')
        if m == '':
            m = []
        else:
            m = m.split(' ')
        if 1 <= len(m) <= 2:
            return 0.9, 0.1
        elif 3 <= len(m) <= 4:
            return 0.5, 0.5
        else:
            return 0.15, 0.85
    pos_types = ('name', 'notname')
    name_detector = BaseDetector(pos_types, dummy_name_detector)
    splits = [0, 0.5, 0.8, 1.]
    cond_trans = create_probsplitter_condition(splits, ('selector_types',
                                                        'name'))
    trans_states = ['Store name', 'Store tempname', 'Refocus name']
    trans_askname = TransitionConversationStates(trans_states, cond_trans)
    chooser_askname = SequentialChooser(q_username)
    state_askname = QuestioningState('Asking name', chooser_askname,
                                     name_detector, tags=['name'],
                                     transition=trans_askname)
    states.append(state_askname)

    ## Defining 'Store name' state
    cond_trans = create_fixed_condition(0)
    trans_states = ['Greetings name']
    trans_storename = TransitionConversationStates(trans_states, cond_trans)

    def storer_name(h, m):
#        h.profile_user.profile['username'] =\
#            h.query_past_messages(sender='user', tag='name')[0]['message']
        if 'nameprovided' in h.profile_user.profile:
            h.profile_user.profile['username'] =\
                h.profile_user.profile['nameprovided']
            del h.profile_user.profile['nameprovided']
        else:
            h.profile_user.profile['username'] = m['message']

    states.append(StoringState('Store name', storer_name, trans_storename))

    ## Defining 'Store tempname' state
    cond_trans = create_fixed_condition(0)
    trans_states = ['Ensure name']
    trans_storename = TransitionConversationStates(trans_states, cond_trans)

    def storer_tempname(h, m):
        h.profile_user.profile['nameprovided'] = m['message']
#        h.profile_user.profile['nameprovided'] =\
#            h.query_past_messages(sender='user', tag='name')[0]['message']
    states.append(StoringState('Store tempname', storer_tempname,
                               transition=trans_storename))

    ## Defining 'Greetings name' state
    q_username_pleasure = [{'message': m} for m in QUESTIONS_PLEASURE]
    chooser_pleasurename = SequentialChooser(q_username_pleasure)
    states.append(TalkingState('Greetings name', chooser_pleasurename,
                               shadow=True))

    ## Defining 'Ensure name' state
    def yes_no_answer_d(message):
        if message['collection']:
            return yes_no_answer(message['message'][-1])
        else:
            return yes_no_answer(message)

    q_username_sure = [{'message': m} for m in QUESTIONS_NAME_SURE]
    trans_states = ['Refocus name', 'Store name']
    trans_askname = TransitionConversationStates(trans_states, yes_no_answer_d)
    chooser_surename = SequentialChooser(q_username_sure)
    states.append(QuestioningState('Ensure name', chooser_surename,
                                   transition=trans_askname))

    ## Defining 'Refocus name' state
    q_retry = [{'message': m} for m in QUESTIONS_RETRY_NAME]
    splits = [0, 0.5, 0.8, 1.]
    cond_trans_probs = create_probsplitter_condition(splits, ('selector_types',
                                                              'name'))

    def cond_transf(message):
        i = cond_trans_probs(message)
        return i
    trans_states = ['Store name', 'Store tempname', 'Refocus name']
    trans_reaskname = TransitionConversationStates(trans_states, cond_transf)
    chooser_reaskname = SequentialChooser(q_retry)
    states.append(TalkingState('Refocus name', chooser_reaskname,
                               name_detector, tags=['name'],
                               transition=trans_reaskname))

    ### Hello conversation
    ## Defining 'Say hello' state
    q_hello = [{'message': m} for m in QUESTIONS_HELLO]
    trans_hello = NullTransitionConversation()
    chooser_hello = SequentialChooser(q_hello)
    states_hello = [TalkingState('Say hello', chooser_hello, shadow=True,
                                 transition=trans_hello)]

    ### Checker username
    bool_cond = lambda x: int(x['query']['check'])

    trans = TransitionConversationStates(['Ask name', 'Say hello'], bool_cond)
#    checker_username =\
#        lambda h, m: {'check': 'username' in h.profile_user.profile}

    def checker_username(h, m):
        return {'query': {'check': 'username' in h.profile_user.profile}}
    check_username = CheckerState('if_username', checker=checker_username,
                                  transition=trans)
    check_user_conv = ConversationStateMachine('if_username_conv',
                                               [check_username],
                                               'if_username', ['if_username'],
                                               transition=trans)

    ### Conversation setting
    cond_trans = create_fixed_condition(0)
    trans_states = ['Say goodbye']
    trans = TransitionConversationStates(trans_states, cond_trans)
    say_hello_conv = ConversationStateMachine('Say hello', states_hello,
                                              'Say hello', ['Say hello'],
                                              transition=trans)

    get_name_conv = ConversationStateMachine('Ask name', states, 'Asking name',
                                             ['Greetings name'],
                                             transition=trans)

    ### Say goodbye conversation
    q_goodbye = [{'message': m} for m in QUESTIONS_GOODBYE]
    say_goodbye = TalkingState('Say goodbye', SequentialChooser(q_goodbye),
                               shadow=True)
    say_goodbye_conv = ConversationStateMachine('Say goodbye', [say_goodbye],
                                                'Say goodbye', 'Say goodbye')

    PoCs = [check_user_conv, say_hello_conv, get_name_conv, say_goodbye_conv]
    end_states = ['Say goodbye']
    general_conv = ConversationStateMachine('Conversation', PoCs,
                                            'if_username_conv', end_states)

    ### Conversation
#    handler_io = HandlerConvesationIO()
    #handler_io.profile_user.profile = {'username': '0'}
#    get_name_conv.run(handler_io)
#    general_conv.run(handler_io)

    handler_db = HandlerConvesationDB()
#    handler_db.profile_user.profile = {'username': 'antonio'}
    handler_ui = TerminalUIHandler(handler_db, general_conv)
#    handler_ui = FlaskUIHandler(handler_db, general_conv)

    handler_ui.run()

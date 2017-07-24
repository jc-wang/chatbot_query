
"""
Example Basic conversation
--------------------------
Example of a basic conversation (hello, goodbye).

How to run the example:

1. Run the script using python3.
2. Take the conversation.

"""

from chatbot.conversation import TalkingState, SequencialChooser,\
    TransitionConversationStates, NullTransitionConversation, BaseDetector,\
    ConversationStateMachine, CheckerState, StoringState

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
            return 0.1, 0.9
    pos_types = ('name', 'notname')
    name_detector = BaseDetector(pos_types, dummy_name_detector)
    splits = [0, 0.5, 0.8, 1.]
    cond_trans = create_probsplitter_condition(splits, ('type', 'name'))
    trans_states = ['Store name', 'Store tempname', 'Refocus name']
    trans_askname = TransitionConversationStates(trans_states, cond_trans)
    chooser_askname = SequencialChooser(q_username)
    states.append(TalkingState('Asking name', chooser_askname, name_detector,
                               tags=['name'], transition=trans_askname))

    ## Defining 'Store name' state
    cond_trans = create_fixed_condition(0)
    trans_states = ['Greetings name']
    trans_storename = TransitionConversationStates(trans_states, cond_trans)

    def storer_name(h):
        h.profile_user.profile['username'] =\
            h.query_past_messages(sender='user', tag='name')[0]['message']

        if 'nameprovided' in h.profile_user.profile:
            del h.profile_user.profile['nameprovided']
    states.append(StoringState('Store name', storer_name, trans_storename))

    ## Defining 'Store tempname' state
    cond_trans = create_fixed_condition(0)
    trans_states = ['Ensure name']
    trans_storename = TransitionConversationStates(trans_states, cond_trans)

    def storer_tempname(h):
        h.profile_user.profile['nameprovided'] =\
            h.query_past_messages(sender='user', tag='name')[0]['message']
    states.append(StoringState('Store tempname', storer_tempname,
                               trans_storename))

    ## Defining 'Greetings name' state
    q_username_pleasure = [{'message': m} for m in QUESTIONS_PLEASURE]
    chooser_pleasurename = SequencialChooser(q_username_pleasure)
    states.append(TalkingState('Greetings name', chooser_pleasurename))

    ## Defining 'Ensure name' state
    q_username_sure = [{'message': m} for m in QUESTIONS_NAME_SURE]
    trans_states = ['Refocus name', 'Store name']
    trans_askname = TransitionConversationStates(trans_states, yes_no_answer)
    chooser_surename = SequencialChooser(q_username_sure)
    states.append(TalkingState('Ensure name', chooser_surename,
                               transition=trans_askname))

    ## Defining 'Refocus name' state
    q_retry = [{'message': m} for m in QUESTIONS_RETRY_NAME]
    splits = [0, 0.5, 0.8, 1.]
    cond_trans = create_probsplitter_condition(splits, ('type', 'name'))
    trans_states = ['Store name', 'Store tempname', 'Refocus name']
    trans_reaskname = TransitionConversationStates(trans_states, cond_trans)
    chooser_reaskname = SequencialChooser(q_retry)
    states.append(TalkingState('Refocus name', chooser_reaskname,
                               name_detector, tags=['name'],
                               transition=trans_reaskname))

    ### Hello conversation
    ## Defining 'Say hello' state
    q_hello = [{'message': m} for m in QUESTIONS_HELLO]
    trans_hello = NullTransitionConversation()
    chooser_hello = SequencialChooser(q_hello)
    states_hello = [TalkingState('Say hello', chooser_hello,
                                 transition=trans_hello)]

    ### Checker username
    bool_cond = lambda x: int(x)
    trans = TransitionConversationStates(['Ask name', 'Say hello'], bool_cond)
    checker_username = lambda h: 'username' in h.profile_user.profile
    check_username = CheckerState('if_username', checker_username, trans)

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

    q_goodbye = [{'message': m} for m in QUESTIONS_GOODBYE]
    say_goodbye = TalkingState('Say goodbye', SequencialChooser(q_goodbye))

    PoCs = [check_username, say_hello_conv, get_name_conv, say_goodbye]
    end_states = ['Say goodbye']
    general_conv = ConversationStateMachine('Conversation', PoCs,
                                            'if_username', end_states)

    ### Conversation
#    handler_io = HandlerConvesationIO()
    #handler_io.profile_user.profile = {'username': '0'}
#    get_name_conv.run(handler_io)
#    general_conv.run(handler_io)

    handler_db = HandlerConvesationDB()
    handler_ui = TerminalUIHandler(handler_db, general_conv)

    handler_ui.run()

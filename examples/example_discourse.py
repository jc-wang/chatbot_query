
"""
Example Basic discourse
-----------------------
Example of a basic discourse (hello, goodbye).

How to run the example:

1. Run the script using python3.
2. Take the conversation.

"""

from chatbotQuery.conversation import TalkingState, SequentialChooser,\
    TransitionConversationStates, NullTransitionConversation, BaseDetector,\
    ConversationStateMachine, CheckerState, StoringState, AnsweringState,\
    QuestioningState, GeneralConversationState
from chatbotQuery.aux_functions import create_probsplitter_condition,\
    create_fixed_condition, yes_no_answer
from chatbotQuery.ui import HandlerConvesationDB, TerminalUIHandler

### HELLO QUESTIONS
QUESTIONS_HELLO = ["Hello! Nice to see you."]
PRESENTATION = ["My name is ChatBot."]
TALKING_LEARNING = ["I am learning to talk."]
QUESTIONS_GOODBYE = ["It's been a pleasure. See you next time!",
                     "Have a nice day!"]


if __name__ == "__main__":
    states = []

    ## Defining 'Greetings name' state
    q_hello = [{'message': m} for m in QUESTIONS_HELLO]
    chooser_hello = SequentialChooser(q_hello)
    cond_trans = create_fixed_condition(0)
    trans_states = ['Presentation']
    trans_hello = TransitionConversationStates(trans_states, cond_trans)
    hello_state = TalkingState('Hello', chooser_hello, shadow=True,)
#                               transition=trans_hello)
    states.append(hello_state)

    q_presentation = [{'message': m} for m in PRESENTATION]
    chooser_presentation = SequentialChooser(q_presentation)
    cond_trans = create_fixed_condition(0)
    trans_states = ['Learning']
    trans_press = TransitionConversationStates(trans_states, cond_trans)
    presentation_state = TalkingState('Presentation', chooser_presentation,
                                      shadow=True,)  # transition=trans_press)
    states.append(presentation_state)

    q_learning = [{'message': m} for m in TALKING_LEARNING]
    chooser_learning = SequentialChooser(q_learning)
    cond_trans = create_fixed_condition(0)
    trans_states = ['Bye']
    trans_learn = TransitionConversationStates(trans_states, cond_trans)
    learning_state = TalkingState('Learning', chooser_learning,
                                  shadow=True)  # , transition=trans_learn)
    states.append(learning_state)

    q_bye = [{'message': m} for m in QUESTIONS_GOODBYE]
    chooser_bye = SequentialChooser(q_bye)
#    cond_trans = create_fixed_condition(0)
#    trans_states = ['Bye']
#    trans = TransitionConversationStates(trans_states, cond_trans)
    bye_state = TalkingState('Bye', chooser_bye, shadow=True)
    states.append(bye_state)

    trans_hello = TransitionConversationStates(['Presentation conv'],
                                               cond_trans)
    hello_conv = ConversationStateMachine('Hello conv', [hello_state],
                                          'Hello', ['Hello'],
                                          transition=trans_hello)

    trans_press = TransitionConversationStates(['Learning conv'], cond_trans)
    press_conv = ConversationStateMachine('Presentation conv',
                                          [presentation_state],
                                          'Presentation', ['Presentation'],
                                          transition=trans_press)

    trans_learn = TransitionConversationStates(['Bye conv'], cond_trans)
    learn_conv = ConversationStateMachine('Learning conv', [learning_state],
                                          'Learning', ['Learning'],
                                          transition=trans_learn)

    goodb_conv = ConversationStateMachine('Bye conv', [bye_state],
                                          'Bye', ['Bye'])

#    discourse1 = ConversationStateMachine('Conversation', states, 'Hello',
#                                          ['Bye'])

    conv_states = [hello_conv, press_conv, learn_conv, goodb_conv]
    discourse2 = ConversationStateMachine('Conversation', conv_states,
                                          'Hello conv', ['Bye conv'])

    handler_db = HandlerConvesationDB()
    handler_ui = TerminalUIHandler(handler_db, discourse2)
#    handler_ui = FlaskUIHandler(handler_db, general_conv)
    handler_ui.run()

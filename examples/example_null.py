
import copy
from chatbotQuery.conversation import GeneralConversationState, CheckerState,\
    QuerierState, StoringState, TalkingState, QuestioningState,\
    AnsweringState, BaseConversationState, ConversationStateMachine
from chatbotQuery.conversation import SequentialChooser,\
    TransitionConversationStates
from chatbotQuery import ChatbotMessage
from chatbotQuery.ui import HandlerConvesationDB, TerminalUIHandler


if __name__ == "__main__":
    ask_chooser = SequentialChooser([{'message': 'question?'}])
    res_chooser = SequentialChooser([{'message': 'response'}])
    asking_state = {'name': 'questioning_state',
                    'asker': True,
                    'shadow': False,
                    'tags': 'questioning',
                    'chooser': ask_chooser}
    answering_state_pars = {'name': 'answering_state',
                            'asker': False,
                            'shadow': False,
                            'tags': 'answering',
                            'chooser': res_chooser}
    shadow_state_pars = {'name': 'shadow_state',
                         'shadow': True}

#    pars = copy.copy(answering_state_pars)
#    state = GeneralConversationState(**pars)
#    statemachine = ConversationStateMachine(name='statemachine1',
#                                            states=[state],
#                                            startState=state.name,
#                                            endStates=state.name)
#
#    handler_db = HandlerConvesationDB()
#    handler_ui = TerminalUIHandler(handler_db, statemachine)
##    handler_ui = FlaskUIHandler(handler_db, general_conv)
#    handler_ui.run()

    pars = copy.copy(asking_state)
    pars['transition'] = (['shadow_state'], lambda m: 0)
    initstate = GeneralConversationState(**pars)

    pars = copy.copy(shadow_state_pars)
    pars['transition'] = (['answering_state'], lambda m: 0)
    innnerstate = GeneralConversationState(**pars)

    pars = copy.copy(answering_state_pars)
    endstate = GeneralConversationState(**pars)

    states = [initstate, innnerstate, endstate]
    statemachine = ConversationStateMachine(name='statemachine3',
                                            states=states,
                                            startState=initstate.name,
                                            endStates=endstate.name)
    handler_db = HandlerConvesationDB()
    handler_ui = TerminalUIHandler(handler_db, statemachine)
#    handler_ui = FlaskUIHandler(handler_db, general_conv)
    handler_ui.run()


"""
TODO
----
Problems with Chooser.

"""
import numpy as np
from chatbotQuery.io.parameters_processing import parse_configuration_file,\
    parse_configuration_file_dbapi, create_tables, create_graphs,\
    create_testing_mode_parameters, path_builder_states
from chatbotQuery.conversation import ConversationStateMachine
from chatbotQuery.ui import TerminalUIHandler, HandlerConvesationDB,\
    HandlerConvesationUI
from chatbotQuery.dbapi import DataBaseAPI


class Autotesting_Handling(HandlerConvesationUI):

    def __init__(self, configuration_file, db_configuration_file):

        ## Parser parameters
        parameters = parse_configuration_file(configuration_file)
        db_pars = parse_configuration_file_dbapi(db_configuration_file)

        ## Obtain description
        states_list_table, path_states, xstates, transitions =\
            create_tables(parameters)
        treestates, graphs_statemachines, complete_network =\
            create_graphs(states_list_table, path_states, xstates, transitions)
        self.complete_network = complete_network

        ## Testing state machine
        testing_pars = create_testing_mode_parameters(parameters)
        if not isinstance(testing_pars, dict):
            testing_pars = testing_pars[0]
        statemachine = ConversationStateMachine.from_parameters(testing_pars)

        ## DB setting
        db_api = DataBaseAPI(**db_pars)
        handler_db = HandlerConvesationDB(databases=db_api)

        super().__init__(handler_db, statemachine)

        ## Functions
        def ifstate(pathname):
            aux = states_list_table[states_list_table['Pathname'] == pathname]
            aux = list(aux['IfStateMachine'])[0]
            return not aux

        def get_sonstate(path):
            if ifstate(path):
                return path
            path = path_builder_states(xstates[path]['StartState'], path)
            if not ifstate(path):
                return get_sonstate(path)
            return path

        ## Initial setting
        initials = states_list_table[states_list_table['level'] == 0]
        initial_state = get_sonstate(list(initials['Pathname'])[0])
        self.current_state = initial_state[:]

    def ask(self, message):
        def get_random_next_state(transitions):
            i = np.random.randint(0, len(transitions.keys()))
            for next_state, tr in transitions.items():
                if tr['transition'] == i:
                    break
            return i, next_state

        i, next_state =\
            get_random_next_state(self.complete_network[self.current_state])
        response = {'message': str(i)}
        self.current_state = next_state
        return response

    def post(self, message):
        pass


def automatic_testing(configuration_file, db_configuration_file, n_runs):
    ## Instantiation
    tester_handler =\
        Autotesting_Handling(configuration_file, db_configuration_file)
    ## Run test
    for _ in range(n_runs):
        tester_handler.run()


def create_handler_ui_test(configuration_file, db_configuration_file):
    ## Parser parameters
    parameters = parse_configuration_file(configuration_file)
    db_pars = parse_configuration_file_dbapi(db_configuration_file)

    ## Testing state machine
    testing_pars = create_testing_mode_parameters(parameters)
    if not isinstance(testing_pars, dict):
        testing_pars = testing_pars[0]
    statemachine = ConversationStateMachine.from_parameters(testing_pars)

    ## DB setting
    db_api = DataBaseAPI(**db_pars)
    handler_db = HandlerConvesationDB(databases=db_api)

    ## Handler
    tester_handler = TerminalUIHandler(handler_db, statemachine)
    return tester_handler


def generate_explorer_chatbot():
    ## Parser parameters
    parameters = parse_configuration_file(configuration_file)
    db_pars = parse_configuration_file_dbapi(db_configuration_file)

    ## Obtain description
    states_list_table, path_states, xstates, transitions =\
        create_tables(parameters)
    treestates, graphs_statemachines, complete_network =\
        create_graphs(states_list_table, path_states, xstates, transitions)


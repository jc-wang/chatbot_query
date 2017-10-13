
import os

from chatbotQuery.ui import TerminalUIHandler
#from chatbotQuery.ui import HandlerConvesationDB
#from chatbotQuery.dbapi import DataBaseAPI
#from chatbotQuery.conversation import ConversationStateMachine
#from chatbotQuery.io import parse_configuration_file_dbapi,\
#    parse_configuration_file


if __name__ == "__main__":

    # Parse data
    configuration_file =\
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     'dbparser_parameter.yml')
    db_configuration_file =\
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     'db_handler_parameters.yml')
#    db_conn_configuration_file =\
#        os.path.join(os.path.dirname(os.path.abspath(__file__)),
#                     'db_connection.yml')
#
#    parameters = parse_configuration_file(configuration_file)
#    db_pars = parse_configuration_file_dbapi(db_conn_configuration_file)
#
#    ## State machine
#    statemachine = ConversationStateMachine.from_parameters(parameters)
#
#    ## DB setting
#    db_api = DataBaseAPI(**db_pars)
#    handler_db = HandlerConvesationDB(databases=db_api)
#
#    ## Handler
#    terminal_handler = TerminalUIHandler(handler_db, statemachine)
#    terminal_handler.run()

    ## Parser parameters
    terminal_handler =\
        TerminalUIHandler.from_configuration_files(db_configuration_file,
                                                   configuration_file)
    terminal_handler.run()

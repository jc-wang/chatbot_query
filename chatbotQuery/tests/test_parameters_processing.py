
import os
import unittest
#import mock
from unittest import mock
import numpy as np

from chatbotQuery.io.parameters_processing import parse_configuration_file,\
    create_condition_parsing_chatbotquery_parameters, create_tables,\
    create_graphs, parse_configuration_file_dbapi, parse_configuration_file_db
from chatbotQuery.io.parameters_processing import\
    create_testing_mode_parameters


class Test_Parsers_Parameters(unittest.TestCase):
    """Testing parsers of parameters
    """

    def setUp(self):
        package_path =\
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.example_yaml =\
            os.path.join(os.path.dirname(package_path),
                         'examples/example_dbparser/dbparser_parameter.yml')
        self.example_pickle =\
            os.path.join(os.path.dirname(package_path),
                         'examples/example_dbparser/dbparser_parameter.pkl')
        self.example_db_yaml =\
            os.path.join(os.path.dirname(package_path),
                         'examples/example_dbparser/db_connection.yml')
        self.example_db_hand_yaml =\
            os.path.join(os.path.dirname(package_path),
                         'examples/example_dbparser/db_handler_parameters.yml')

    def test_parser_example(self):
        parameters = parse_configuration_file(self.example_yaml)
        parameters = parse_configuration_file(self.example_pickle)

    def test_create_condition(self):
        cond = create_condition_parsing_chatbotquery_parameters()

        pathtree = 'parameters'
        tree = {'parameters': 0}
        cond(pathtree, tree)

        pathtree = ['parameters']
        tree = {'parameters': [0]}
        cond(pathtree, tree)

    def test_create_tables(self):
        parameters = parse_configuration_file(self.example_yaml)
        create_tables(parameters)

    def test_create_graphs(self):
        parameters = parse_configuration_file(self.example_yaml)
        create_graphs(*create_tables(parameters))

    def test_testing_mode(self):
        parameters = parse_configuration_file(self.example_yaml)
        create_testing_mode_parameters(parameters)

    def test_parsing_db_connection(self):
        parameters = parse_configuration_file_dbapi(self.example_db_yaml)

    def test_parse_dbparameters(self):
        parameters = parse_configuration_file_db(self.example_db_hand_yaml)

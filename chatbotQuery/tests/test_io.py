
import os
import yaml
import copy
import unittest
#import mock
from unittest import mock

from chatbotQuery.io import chooser_io, parse_parameter_functions,\
    create_parsing_function_functions, parse_trainning_configuration_file,\
    get_patterns, store_training

from chatbotQuery.io.io_transition_information import parse_patterns_yml


class Test_TreePath(unittest.TestCase):
    """
    """

    def setUp(self):
        package_path =\
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.example_trans_f =\
            os.path.join(os.path.dirname(package_path),
                         'examples/example_dbparser/aux_functions.py')
        self.example_chooser_xml =\
            os.path.join(os.path.join(os.path.dirname(package_path),
                                      'examples/example_dbparser/Answers/'),
                         'Salutations/HELLO_SENTENCES.xml')

    def test_(self):
        chooser_io(self.example_chooser_xml)

    def test_parameter_functions(self):
        paramaters = {'filepath': self.example_trans_f,
                      'function_name': 'create_fixed_condition',
                      'function_parameters': {'selected': 0}}
        parse_parameter_functions(paramaters)

        paramaters = {'filepath': self.example_trans_f,
                      'function_name': 'querier_f'}
        parse_parameter_functions(paramaters)

    def test_parameter_function_relative(self):
        folder = os.path.dirname(self.example_chooser_xml)
        create_parsing_function_functions(parse_parameter_functions, folder)


class Test_ParsePatterns(unittest.TestCase):
    """
    """

    def setUp(self):
        package_path =\
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.example_trans_yml =\
            os.path.join(os.path.dirname(package_path),
                         'examples/example_dbparser/train_null_transition.yml')

    def test_parse_train_configuration(self):
        parameters = parse_trainning_configuration_file(self.example_trans_yml)
        self.assertIsInstance(parameters, dict)

    def test_parse_patterns_transition(self):
        parameters = parse_trainning_configuration_file(self.example_trans_yml)
        dirname = os.path.dirname(self.example_trans_yml)
        parse_patterns_yml(os.path.join(dirname, parameters['patterns']))

    def test_get_patterns(self):
        dirname = os.path.dirname(self.example_trans_yml)
        parameters = parse_trainning_configuration_file(self.example_trans_yml)
        filepatterns = os.path.join(dirname, parameters['patterns'])
        patterns = yaml.load(open(filepatterns).read())
        get_patterns(patterns, self.example_trans_yml)

        get_patterns(parameters['patterns'], self.example_trans_yml)

        get_patterns(os.path.join(dirname, parameters['patterns']),
                     self.example_trans_yml)

    def test_store_model(self):
        store_training('prueba.pkl', self.example_trans_yml, None,
                       None, None, {})
        dirname = os.path.dirname(self.example_trans_yml)
        os.remove(os.path.join(dirname, 'prueba.pkl'))

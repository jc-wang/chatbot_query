
import os
import shutil
import unittest

from chatbotQuery.io import prepare_states_list_table,\
    prepare_transitions, create_testing_project, parse_configuration_file,\
    create_tables, generate_info_reports

from chatbotQuery.io.prepare_reports import generate_html_states_table,\
    generate_html_transitions_table


class Test_Prepare_Reports(unittest.TestCase):
    """Testing parsers of parameters
    """

    def setUp(self):
        package_path =\
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.chat_conf_file =\
            os.path.join(os.path.dirname(package_path),
                         'examples/example_dbparser/dbparser_parameter.yml')
        self.db_conf_file =\
            os.path.join(os.path.dirname(package_path),
                         'examples/example_dbparser/db_handler_parameters.yml')
        self.templates_folder =\
            os.path.join(os.path.dirname(package_path),
                         'examples/example_testing_framework_templates')
        self.outputfolder =\
            os.path.join(os.path.dirname(package_path),
                         'examples/example_testing_framework_templates/prueba')
        parameters = parse_configuration_file(self.chat_conf_file)
        self.tables = create_tables(parameters)

    def test_prepare_states_list_table(self):
        states_list_table = self.tables[0]
        prepare_states_list_table(states_list_table)

    def test_prepare_transitions(self):
        transitions = self.tables[3]
        prepare_transitions(transitions)

    def test_create_dashboard_utils(self):
        create_testing_project(self.chat_conf_file, self.db_conf_file,
                               self.templates_folder, self.outputfolder)
        shutil.rmtree(self.outputfolder)

    def test_create_json_information(self):
        generate_info_reports(self.chat_conf_file)

    def test_create_html(self):
        states_list_table, transitions_table, _, _, _, _ =\
            generate_info_reports(self.chat_conf_file)
        generate_html_states_table(states_list_table)
        generate_html_transitions_table(transitions_table)

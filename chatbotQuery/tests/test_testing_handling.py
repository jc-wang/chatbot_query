
import os
import unittest
from chatbotQuery.testing_handling import automatic_testing,\
    create_handler_ui_test


class Test_testing_handling(unittest.TestCase):
    """Testing test utils.
    """

    def setUp(self):
        package_path =\
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.example_yaml =\
            os.path.join(os.path.dirname(package_path),
                         'examples/example_dbparser/dbparser_parameter.yml')
        self.example_db_yaml =\
            os.path.join(os.path.dirname(package_path),
                         'examples/example_dbparser/db_connection.yml')

#    def test_automatic_testing(self):
#        automatic_testing(self.example_yaml, self.example_db_yaml, 10)

    def test_automatic_ui_test(self):
        create_handler_ui_test(self.example_yaml, self.example_db_yaml)

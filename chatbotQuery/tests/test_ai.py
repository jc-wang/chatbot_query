
import os
import yaml
import copy
import unittest
#import mock
from unittest import mock

from chatbotQuery.ai import create_trainning_transition


class Test_TreePath(unittest.TestCase):
    """
    """

    def setUp(self):
        package_path =\
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.example_trans_yml =\
            os.path.join(os.path.dirname(package_path),
                         'examples/example_dbparser/train_null_transition.yml')

    def test_transition_ai(self):
        dirname = os.path.dirname(self.example_trans_yml)
        create_trainning_transition(self.example_trans_yml, out_filepath='')

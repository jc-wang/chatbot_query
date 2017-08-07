
import unittest
import pandas as pd

from chatbotQuery.datasets import fetch_data_products

from chatbotQuery.aux_functions import yes_no_answer, create_yes_no_question,\
    create_probsplitter_condition, create_fixed_condition, splitter,\
    create_fixed_reacted_condition, create_null_condition, check_name


class Test_AuxFunctions(unittest.TestCase):
    """Testing and standarization transitions between states.
    """

    def setUp(self):
        self.messages = [{'message': 'hello how are you', 'value': 2},
                         {'message': 'No, I do not like it', 'value': 0.1},
                         {'message': 'yes!', 'value': 0}]

    def test_aux_functions(self):

        y_no_alt = create_yes_no_question('yes')
        no_y_alt = create_yes_no_question('no')
        for m in self.messages:
            yes_no_answer(m)
            y_no_alt(m)
            no_y_alt(m)

        cond0 = create_probsplitter_condition([0, 1, 2], ['value'])
        cond1 = create_fixed_condition()
        cond2 = create_fixed_reacted_condition()
        cond3 = create_null_condition()

        for m in self.messages:
            cond0(m)
            cond1(m)
            cond2(m)
            cond3(m)

        check_name(None)

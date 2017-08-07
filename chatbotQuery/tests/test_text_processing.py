

import unittest
from itertools import product

from chatbotQuery.dbapi.text_processing import steming_words,\
    computing_str_distance_matrix, Preprocessor, Words_collapser


class Test_HandlerConvesationDB(unittest.TestCase):

    def setUp(self):
        self.vocabulary = ['yes', 'no', 'probably']
        self.synonyms = dict(zip(self.vocabulary,
                                 [['of course'], ['nein'], ['maybe']]))

    def test_stemming_words(self):
        preproc = lambda s: s.strip().lower()
        steming_words(self.vocabulary, self.synonyms, preproc)

    def test_computing_str_distance(self):
        computing_str_distance_matrix(['ye', 'propbably'], self.vocabulary)

    def test_preprocessor(self):
        pre = Preprocessor(['NN'], lambda s: s.lower(), True)
        pre('Hello, this is a test.')

    def test_collapser(self):
        pos_inputs = [[None, 'pre', 'post'], [None, lambda x: x]]

        for p in product(*pos_inputs):
            w_col = Words_collapser(*p)
            w_col.fit(self.vocabulary)
            w_col.fit_transform(self.vocabulary)

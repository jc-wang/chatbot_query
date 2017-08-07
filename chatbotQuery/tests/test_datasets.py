
import unittest
import pandas as pd

from chatbotQuery.datasets import fetch_data_products


class Test_DataLoader(unittest.TestCase):
    """Testing and standarization transitions between states.
    """

    def test_dataproducts(self):
        data = fetch_data_products()
        self.assertIsInstance(data, pd.DataFrame)


import pandas as pd
import os


def fetch_data_products():
    parentpath = os.path.dirname(os.path.realpath(__file__))
    data = pd.read_csv(os.path.join(parentpath, 'products.csv'), index_col=0)
    return data

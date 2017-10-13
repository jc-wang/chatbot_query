
"""

{'parameters':
    {'parameters_cv': {'n_splits': 10, 'test_size': 0.5}
     'parameters_model': {'n_estimators': (10, 50, 100)}
    }
}


############################## Sample file train ##############################
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
patterns: pathfile
preprocess_pars:
    -
        preprocess_text_to_features
    -
        null
model_pars:
    -
        train_random_forest
    -
        parameters_cv:
            n_splits: 10
            test_size: 0.5
        parameters_model:
            n_estimators:
                    - 10
                    - 50
                    - 100
out_filepath: pathfile
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

############################ Sample file patterns #############################
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-
    -
        filepath:
        type: keywords
    -
        filepath:
        type: table
        include:
        exclude:
    -
        filepath:
        type: text

"""

import os
import yaml
import pickle
import pandas as pd


def parse_trainning_configuration_file(configuration_file):
    parameters = yaml.load(open(configuration_file).read())
    parameters = parameters if isinstance(parameters, dict) else parameters[0]
    return parameters


def store_training(filepath, configuration_file, vec, model, transition,
                   score_report):
    storer = {}
    storer['vectorizer'] = vec
    storer['model'] = model
    storer['transition'] = transition
    storer['score_report'] = score_report
    if not os.path.isfile(filepath):
        filepath = os.path.join(os.path.dirname(configuration_file),
                                filepath)
    with open(filepath, 'wb') as file_to_store:
        pickle.dump(storer, file_to_store)


def get_patterns(patterns_info, configuration_file):
    if isinstance(patterns_info, list):
        dirname = os.path.dirname(configuration_file)
        text_data = parse_patterns(patterns_info, dirname)
    else:
        assert(isinstance(patterns_info, str))
        if os.path.isfile(patterns_info):
            text_data = parse_patterns_yml(patterns_info)
        else:
            patterns_info = os.path.join(os.path.dirname(configuration_file),
                                         patterns_info)
            text_data = parse_patterns_yml(patterns_info)
    if isinstance(text_data, tuple):
        assert(len(text_data) == 2)
        text_data, labels_data = text_data
    else:
        assert(all([len(e) == 3 for e in text_data]))
        labels_data = list(range(len(text_data)))
    return text_data, labels_data


def parse_patterns_yml(filepath):
    patterns = yaml.load(open(filepath).read())
    patterns = patterns if isinstance(patterns, list) else [patterns]
    dirname = os.path.dirname(filepath)
    return parse_patterns(patterns, dirname)


def parse_patterns(patterns, dirname=''):
    assert(isinstance(patterns, (list, tuple)))
    assert(all([isinstance(e, list) for e in patterns]))
    assert(all([all(['type' in d for d in e]) for e in patterns]))
#    keywords, text, table = [], [], []
    text_data = []
    for e in patterns:
        keywords_e, text_e, table_e = [], [], []
        for data in e:
            filepath = data['filepath']
            logifl = os.path.isfile(filepath)
            filepath = filepath if logifl else os.path.join(dirname, filepath)
            if data['type'] == 'keywords':
                parsed = parse_keywords(filepath)
                keywords_e.extend(parsed)
            elif data['type'] == 'text':
                parsed = parse_text(filepath)
                text_e.extend(parsed)
            elif data['type'] == 'table':
                parsed = parse_table(filepath)
                table_e.extend(parsed)
        text_data.append((keywords_e, text_e, table_e))
    return text_data


def parse_keywords(filepath):
    with open(filepath, 'rb') as filereader:
        keywords = filereader.readlines()
    return keywords


def parse_text(filepath):
    with open(filepath, 'rb') as filereader:
        text = filereader.read()
    return text


def parse_table(filepath, include=(), exclude=()):
    _, ext = os.path.splitext(filepath)
    if ext == '.csv':
        data = pd.read_csv(filepath)
    if include:
        data = data[include]
    else:
        data = data[[var for var in data.columns if var not in exclude]]

    table = []
    for var in data.columns:
        data_var = list(data[var])
        for i, data_v in enumerate(data_var):
            data_var[i] = ' '.join([var, str(data_v)])
        table.extend(data_var)
    return table

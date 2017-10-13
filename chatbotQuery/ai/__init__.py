
"""

https://radimrehurek.com/gensim/models/doc2vec.html
https://github.com/Avkash/mldl/blob/master/tensorbeat-answerbot/
PositiveNegative.ipynb

"""
#keywords = [s.strip() for s in text.replace('\n', ' ').split(' ')]
#
#batch_size = 50
#filters = 25
#number_words = 24
#embedding_dims = 3
#kernel_size_head, kernel_size_body = 3, 5
#hidden_dims = 20
#epochs = 5
#model_keywords = Sequential()
### Mapping word indices to float numbers
#model_keywords.add(Input((maxlen_head,)))
#model_keywords.add(Embedding(number_words,
#                         embedding_dims,
#                         input_length=maxlen_head))
#model_keywords.add(Dropout(0.2))


#keras.preprocessing.text.\
#    Tokenizer(num_words=None,
#              filters='!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n',
#              lower=True,
#              split=" ",
#              char_level=False)
#

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedShuffleSplit, GridSearchCV
#from sklearn.base import BaseEstimator, TransformerMixin

from chatbotQuery.io import store_training, get_patterns,\
    parse_trainning_configuration_file


############################## Model application ##############################
###############################################################################
def create_trainning_transition(configuration_file, out_filepath=''):
    ## Parameters parsing
    parameters = parse_trainning_configuration_file(configuration_file)

    text_data, labels_data = get_patterns(parameters['patterns'],
                                          configuration_file)
    preprocess_pars = parameters['preprocess_pars']
    model_pars = parameters['model_pars']
    if not out_filepath:
        out_filepath = parameters['out_filepath']

    ## Pipeline application
    vec, X, y = apply_preprocessing(text_data, labels_data, *preprocess_pars)
    model, score_report = apply_model(X, y, *model_pars)
    transition = create_transition_function(vec, model)

#    ## Store results
#    store_training(out_filepath, configuration_file, vec, model, transition,
#                   score_report)


def apply_preprocessing(text_data, labels_data, name_preprocessor,
                        preprocess_pars):
    preprocess_pars = {} if preprocess_pars is None else preprocess_pars
    vec, X, y = eval(name_preprocessor)(text_data, labels_data,
                                        **preprocess_pars)
    return vec, X, y


def apply_model(X, y, model_name, model_pars):
    model_pars = {} if model_pars is None else model_pars
    print(model_pars)
    model_selection, score_report = eval(model_name)(X, y, model_pars)

    def model(X):
        return int(model_selection.predict(X[0])[0])
    return model, score_report


###############################################################################


############################# Transition function #############################
###############################################################################
def create_transition_function(vec, model):
    def transition(X):
#        return int(model.predict(vec.transform(X[0]))[0])
        return model(vec(X))
    return transition


############################# Preprocess function #############################
###############################################################################
def preprocess_text_to_features(text_data, labels_data):
    keywords, labels = format_text_data(text_data, labels_data)
    ## WARNING:!!!
    collection =\
        '! " # $ % & () * + , - . / : ; < = > ? @ [ \\ ] ^ _ ` { | } ~ \t \n'
    stop_elements = collection.split(' ')
    main_vectorizer =\
        TfidfVectorizer(ngram_range=(1, 10),
                        stop_words=stop_elements,
                        max_features=1000)
    data_sp = main_vectorizer.fit_transform(keywords)
    vectorizer = lambda x: main_vectorizer.transform(x)
    return vectorizer, data_sp, labels


def format_text_data(text_data, labels_data=None):
    if labels_data is None:
        labels_data = list(range(len(text_data)))
    assert(len(text_data) == len(text_data))

    labels = []
    for i, td in enumerate(text_data):
        text_data[i] = format_keywords(*td)
        labels.append(np.ones(len(text_data[i]))*i)
    labels = np.concatenate(labels).astype(int)
    text_data = flatten_1lvl(text_data)
    return text_data, labels


def format_keywords(keywords, data_keywords, text=[]):
    if text:
        if isinstance(text, str):
            text = text.split('.')
        else:
            assert(isinstance(text, list))
            text = flatten_1lvl([t.split('.') for t in text])
    assert(isinstance(keywords, list))
    assert(isinstance(data_keywords, list))
    assert(isinstance(text, list))
    keywords = keywords + data_keywords + text
    return keywords


######################### Model trainning functions ###########################
###############################################################################
def train_random_forest(X, y, parameters):
    cv_selection = StratifiedShuffleSplit(**parameters['parameters_cv'])
    model = RandomForestClassifier()
    model_selection = GridSearchCV(model, parameters['parameters_model'],
                                   cv=cv_selection)
    model_selection = model_selection.fit(X, y)
    score_report = model_selection.cv_results_
    return model_selection, score_report


############################### Utils functions ###############################
###############################################################################
def flatten_1lvl(list_of_lists):
    lista = []
    for l in list_of_lists:
        if isinstance(l, list):
            lista.extend(l)
        else:
            lista.append(l)
    return lista

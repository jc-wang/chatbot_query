

from collections import defaultdict
import jellyfish
# from pyxDamerauLevenshtein import damerau_levenshtein_distance_ndarray
import numpy as np
from stemming.porter2 import stem
from textblob import TextBlob


class defaultmirrordict(defaultdict):

    def __missing__(self, key):
        return key


class Preprocessor(object):

    def __init__(self, pos_tag_filter, f_proc, returntext=True):
        assert(type(pos_tag_filter) == list)
        self.pos_tag_filter = pos_tag_filter
        self.preproc = f_proc
        self.returntext = returntext

    def __call__(self, text):
        blob = TextBlob(text)
        words = [self.preproc(e[0]) for e in blob.tags
                 if e[1] in self.pos_tag_filter]
        if self.returntext:
            words = ' '.join(words)
        return words


class Words_collapser(object):
    """It tries to put all together the words with misspelling, synonyms to
    easy the work of the training.
    """

    def __init__(self, stemming_=None, text_preproc=None):

        assert(stemming_ in [None, 'pre', 'post'])
        self.stemming = stemming_

        ## Compute the maximum accepted edit distance
        def f(x):
            return np.floor(np.log2(max(x, 2)))-1
        f_vec = np.vectorize(f)

        def max_distort(lenght):
            lenght = np.atleast_1d(lenght)
            return f_vec(lenght)
        self.max_distort = max_distort

        ## Text preprocessing
        if text_preproc is None:
            text_preproc = lambda x: x
        assert(callable(text_preproc))
        self.text_preproc = text_preproc

    def fit(self, vocabulary, synonyms=None, misspelling_memory=None):
        self.synonyms = defaultmirrordict()
        if synonyms is None:
            synonyms = defaultmirrordict()
        if misspelling_memory is None:
            misspelling_memory = defaultmirrordict()
        if self.stemming == 'pre':
            vocabulary, synonyms = steming_words(vocabulary, synonyms)
        self.vocabulary = vocabulary
        self.synonyms.update(synonyms)
        self.misspelling_memory = misspelling_memory
        return self

    def transform(self, vocabulary):
        ## Correct misspellings
        # Memory misspellings
        vocabulary = map(lambda x: self.misspelling_memory[x], vocabulary)
        # Distance misspellings
        # TODO: computing_str_distance_matrix(vocabulary, self.vocabulary)
        # TODO: matching algorithm

        ## Pre-stemming
        if self.stemming == 'pre':
            vocabulary, _ = steming_words(vocabulary)
        ## Mapping to known vocabulary
        vocabulary = [self.synonyms[voc] for voc in vocabulary]
        ## Post-stemming
        if self.stemming == 'post':
            vocabulary, _ = steming_words(vocabulary)
        return vocabulary

    def fit_transform(self, vocabulary, synonyms=None,
                      misspelling_memory=None):
        cls = self.fit(vocabulary, synonyms, misspelling_memory)
        self._update_class(cls)
        return self.transform(vocabulary)

    def _update_class(self, cls):
        self.vocabulary = cls.vocabulary
        self.synonyms = cls.synonyms
        self.misspelling_memory = self.misspelling_memory


def computing_str_distance_matrix(words, vocabulary):
#    dist_matrix = np.zeros(len(words), len(vocabulary))
    def str_distance(i, j):
        return jellyfish.damerau_levenshtein_distance(words[i], vocabulary[j])
#    dist_matrix = np.fromfunction(str_distance, (len(words), len(vocabulary)),
#                                  dtype=np.float)

    def str_distance_matrix(n, m):
        x = np.zeros((n, m)).astype(float)
        for i in range(n):
            for j in range(m):
                x[i, j] = str_distance(i, j)
        return x
    str_dist_f = np.vectorize(str_distance_matrix)
    dist_matrix = str_dist_f(len(words), len(vocabulary))
    return dist_matrix


def steming_words(vocabulary, synonyms=None, preproc=None):
    preproc = lambda s: s if preproc is None else preproc
    vocabulary = [preproc(stem(word)) for word in vocabulary]
    if synonyms is not None:
        synonyms = dict([(preproc(stem(key)), preproc(stem(value)))
                         for (key, value) in synonyms.items()])
    return vocabulary, synonyms

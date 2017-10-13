
import os
import copy
import unittest
#import mock
from unittest import mock

from chatbotQuery.io.parameters_processing import parse_configuration_file
from chatbotQuery.io.tree_process_functions import find_descriptions_new,\
    PathGenerator, edit_in_tree, find_descriptions, edit_in_tree_new,\
    find_in_tree


class Test_TreePath(unittest.TestCase):
    """
    """

    def setUp(self):
        package_path =\
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        example_yaml =\
            os.path.join(os.path.dirname(package_path),
                         'examples/example_dbparser/dbparser_parameter.yml')
        self.parameters = parse_configuration_file(example_yaml)

    def assert_pathgen(self, pathgen):
        def generate_path_test(pathgen):
            new_path, n = [], len(pathgen.path_generators)
            if n == 0:
                new_path.append(['path'])
            else:
                new_path.extend([['path'] for i in range(n+1)])
            return new_path

        ## Initialization test
        pathgen.initial_path()
        pathgen.isnull_path([])
        pathgen.isnull_path(generate_path_test(pathgen))
        self.assertTrue(pathgen.isnull_path(pathgen.initial_path()))

        ## Path retrieving
        pathgen.get_last(pathgen.initial_path())
        pathgen.get_last(generate_path_test(pathgen))
        pathgen.get_treepath(generate_path_test(pathgen))

        pathgen.increment_path(0, None, generate_path_test(pathgen))

    def test_pathgen(self):
        pathgen = PathGenerator()
        self.assert_pathgen(pathgen)

        def increment_path_state(key, value, path):
            new_path = path[:]
            if isinstance(value, dict):
                if 'name' in value:
                    if path:
                        new_path = '.'.join([path, value['name']])
                    else:
                        new_path = value['name']
            return new_path

        def initial_path_state():
            return ''

        def get_last_state(path):
            return path.split('.')[-1]

        pars_path = (initial_path_state, increment_path_state, get_last_state)
        pathgen = PathGenerator(pars_path)
        self.assert_pathgen(pathgen)

    def test_find_in_tree(self):
        pars = copy.copy(self.parameters)
        for t in find_in_tree(pars, 'states'):
            pass

    def test_edit_in_tree(self):
        pars = copy.copy(self.parameters)
        condition_function = lambda key, value: key == 'transition'
        f_edit = lambda tree: [None]

        pars = edit_in_tree(pars, condition_function, f_edit, path=None,
                            if_flatten=True)

    def test_edit_in_tree_new(self):
        pars = copy.copy(self.parameters)
        condition_function = lambda key, value: key == 'transition'
        pathgenerator = PathGenerator()
        pars = copy.copy(self.parameters)
        f_edit = lambda tree: [None]

        pars = edit_in_tree_new(pars, condition_function, pathgenerator,
                                f_edit, path=None)

    def test_find_descriptors(self):
        pars = copy.copy(self.parameters)
        condition_function = lambda key, value: key == 'transition'
        for t in find_descriptions(pars, condition_function):
            t

    def test_find_descriptors_new(self):
        pars = copy.copy(self.parameters)
        condition_function = lambda key, value: key == 'transition'
        pathgenerator = PathGenerator()
        retriever = lambda x, y: (x, y)
        for t in find_descriptions_new(pars, condition_function, pathgenerator,
                                       retriever):
            t

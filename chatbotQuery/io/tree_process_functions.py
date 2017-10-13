

############################## Parsing functions ##############################
###############################################################################
def edit_in_tree(tree, condition_function, f_edit, path=None, if_flatten=True):
    # Null path case
    if path is None:
        path = []

    # In case this is a list
    if isinstance(tree, list):
        any_trans = False
        for idx, val in enumerate(tree):
            new_path = list(path)
            if condition_function(path[-1], val):
                tree[idx] = f_edit(val)
                any_trans = True
            else:
                new_path.append(idx)
                edit_in_tree(val, condition_function, f_edit, path=new_path,
                             if_flatten=if_flatten)
        if any_trans and if_flatten:
            tree[:] = flatten_1lvl(tree)

    # In case this is a dictionary
    if isinstance(tree, dict):
        for k, v in tree.items():
            new_path = list(path)
            new_path.append(k)
            edit_in_tree(v, condition_function, f_edit, path=new_path,
                         if_flatten=if_flatten)

    if path:
        if condition_function(path[-1], tree):
            tree = f_edit(tree)


def edit_in_tree_new(tree, condition_function, pathgenerator, f_edit,
                     path=None):
    # Null path case
#    if path is None:
#        path = []
    if path is None:
        path = pathgenerator.initial_path()

    # In case this is a list
    if isinstance(tree, list):
        for idx, val in enumerate(tree):
#            new_path = list(path)
#            new_path.append(idx)
            new_path = pathgenerator.increment_path(idx, val, list(path))
            if condition_function(pathgenerator.get_treepath(new_path), val):
                tree[idx] = f_edit(val)
            else:
                edit_in_tree_new(val, condition_function, pathgenerator,
                                 f_edit, path=new_path)

    # In case this is a dictionary
    if isinstance(tree, dict):
        for k, v in tree.items():
#            new_path = list(path)
#            new_path.append(k)
            new_path = pathgenerator.increment_path(k, v, list(path))
            if condition_function(pathgenerator.get_treepath(new_path), v):
                tree[k] = f_edit(v)
            else:
                edit_in_tree_new(v, condition_function, pathgenerator,
                                 f_edit, path=new_path)

    if pathgenerator.isnull_path(path):
#        if condition_function(path[-1], tree):
        if condition_function(pathgenerator.get_treepath(path), tree):
            tree = f_edit(tree)


def find_in_tree(tree, key, path=None):
    # Null path case
    if path is None:
        path = []

    # In case this is a list
    if isinstance(tree, list):
        for idx, val in enumerate(tree):
            new_path = list(path)
            new_path.append(idx)
            for result in find_in_tree(val, key, path=new_path):
                yield result

    # In case this is a dictionary
    if isinstance(tree, dict):
        for k, v in tree.items():
            new_path = list(path)
            new_path.append(k)
            for result in find_in_tree(v, key, path=new_path):
                yield result

            if key == k:
                new_path = list(path)
                new_path.append(key)
                yield new_path


def flatten_1lvl(lista):
    new_list = []
    for l in lista:
        if isinstance(l, list):
            new_list.extend(l)
        else:
            new_list.append(l)
    return new_list


def find_descriptions(tree, condition_function, path=None):
    # Null path case
    if path is None:
        path = []

    # In case this is a list
    if isinstance(tree, list):
        for idx, val in enumerate(tree):
            new_path = list(path)
            new_path.append(idx)
            for result in find_descriptions(val, condition_function,
                                            path=new_path):
                yield result
            if condition_function(path[-1], val):
                yield path

    # In case this is a dictionary
    if isinstance(tree, dict):
        for k, v in tree.items():
            new_path = list(path)
            new_path.append(k)
            for result in find_descriptions(v, condition_function,
                                            path=new_path):
                yield result

            if condition_function(k, tree):
                new_path = list(path)
                new_path.append(k)
                yield new_path

    if path:
        if condition_function(path[-1], tree):
            yield path


def find_descriptions_new(tree, condition_function, pathgenerator, retriever,
                          path=None):
    # Null path case
#    if path is None:
#        path = []
    if path is None:
        path = pathgenerator.initial_path()

    # In case this is a list
    if isinstance(tree, list):
        for idx, val in enumerate(tree):
#            new_path = list(path)
#            new_path.append(idx)
            new_path = pathgenerator.increment_path(idx, val, list(path))
            for result in find_descriptions_new(val, condition_function,
                                                pathgenerator, retriever,
                                                path=new_path):
                yield result
#            if condition_function(path[-1], val):
            if condition_function(pathgenerator.get_treepath(new_path), val):
                yield retriever(new_path, val)

    # In case this is a dictionary
    if isinstance(tree, dict):
        for k, v in tree.items():
#            new_path = list(path)
#            new_path.append(k)
            new_path = pathgenerator.increment_path(k, v, list(path))
            for result in find_descriptions_new(v, condition_function,
                                                pathgenerator, retriever,
                                                path=new_path):
                yield result

            if condition_function(pathgenerator.get_treepath(new_path), v):
#                new_path = list(path)
#                new_path.append(k)
#                new_path = pathgenerator.increment_path(k, v, list(path))
                yield retriever(new_path, v)

    if pathgenerator.isnull_path(path):
#        if condition_function(path[-1], tree):
        if condition_function(pathgenerator.get_treepath(path), tree):
            yield retriever(path, tree)


class PathGenerator(object):
    ## WARNING: Failing with pathgenerators

    def __init__(self, *path_generators):
        new_path_gen = []
        for gen in path_generators:
            if type(gen) in [list, tuple]:
                gen = PathGenerator.from_functions(*gen)
            assert(isinstance(gen, PathGenerator))
            new_path_gen.append(gen)
        self.path_generators = new_path_gen

    @classmethod
    def from_functions(cls, initial_path_f, increment_path_f, get_last_f):
        assert(callable(initial_path_f))
        assert(callable(increment_path_f))
        assert(callable(get_last_f))
        pathgen = cls()
        pathgen.initial_path = initial_path_f
        pathgen.increment_path = increment_path_f
        pathgen.get_last = get_last_f
        return pathgen

    def isnull_path(self, path):
        return path == self.initial_path()

    def initial_path(self):
        init_path = [p.initial_path() for p in self.path_generators]
        if len(self.path_generators):
            init_path = [[]]+init_path
        return init_path

    def increment_path(self, key, value, path):
        new_path = list(path)
        if len(self.path_generators) == 0:
            new_path.append(key)
        else:
            new_path[0].append(key)
            for i, gen in enumerate(self.path_generators):
                new_path[i+1] = gen.increment_path(key, value, new_path[i+1])
        return new_path

    def get_last(self, path):
        pathtree = self.get_treepath(path)
        if pathtree:
            return pathtree[-1]
        else:
            return ''

    def get_treepath(self, path):
        if len(self.path_generators) == 0:
            pathtree = path
        else:
            pathtree = path[0]
        return pathtree

#        if len(self.path_generators) == 0:
#            return path[-1]
#        else:
#            last_path = [path[0][-1]]
#            for i, gen in enumerate(self.path_generators):
#                last_path.append(gen.get_last(path[i+1]))
#            return last_path


############### Example PathGenerator
#def function(parameters):
#    # Edit finding functions
#    def condition_function_states(tree):
#        "Explorer the tree of states of parameters."
#        logi = False
#        if isinstance(tree, dict):
#            logi = ('name' in tree)
#        return logi
#
#    def condition_function_states_key(key):
#        "Exploring lists in the tree of states of parameters."
#        if isinstance(key, (list, tuple)):
#            key = key[0]
#        return isinstance(key, (int, np.int))
#    condition_function =\
#        create_condition(condition_function_states_key,
#                         condition_function_states, 'or')

#    def increment_path_state(key, value, path):
#        new_path = path[:]
#        if isinstance(value, dict):
#            if 'name' in value:
#                if path:
#                    new_path = '.'.join([path, value['name']])
#                else:
#                    new_path = value['name']
#        return new_path
#
#    def initial_path_state():
#        return ''
#
#    def get_last_state(path):
#        return path.split('.')[-1]

#    f_state_path = (initial_path_state, increment_path_state, get_last_state)
#    pathgen = PathGenerator(f_state_path)


#def edit_in_tree_list(tree, condition_function, f_edit, path=None):
#    # Null path case
#    if path is None:
#        path = []
#
#    # In case this is a list
#    if isinstance(tree, list):
#        for idx, val in enumerate(tree):
#            new_path = list(path)
#            if condition_function(path[-1], val):
#                tree[idx] = f_edit(val)
#            else:
#                new_path.append(idx)
#                edit_in_tree(val, condition_function, f_edit, path=new_path)
#
#    # In case this is a dictionary
#    if isinstance(tree, dict):
#        for k, v in tree.items():
#            new_path = list(path)
#            new_path.append(k)
#            edit_in_tree(v, condition_function, f_edit, path=new_path)

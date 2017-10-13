
import os
import yaml
import pickle
import numpy as np
import pandas as pd
import networkx as nx

from chatbotQuery.io.tree_process_functions import PathGenerator,\
    find_descriptions_new, edit_in_tree, edit_in_tree_new
from chatbotQuery.io import parse_parameter_functions,\
    create_parsing_function_functions, create_abspath_function_functions


############################## Parsing functions ##############################
###############################################################################
def parse_configuration_file(configuration_file):
    filename, ext = os.path.splitext(configuration_file)
    if ext in ['.yaml', '.yml']:
        conv_pars = parse_configuration_file_yaml(configuration_file)
    else:
        conv_pars = parse_configuration_file_pickle(configuration_file)
    return conv_pars


def parse_configuration_file_yaml(configuration_file):
    # Parse parent directory
    conv_pars = yaml.load(open(configuration_file).read())[0]
    # Edit functions
    folder = os.path.dirname(configuration_file)
    cond_parsing_tree = create_condition_function_parsing_tree(folder)
    condition_function = create_condition('states', cond_parsing_tree, 'and')
    f_edit = create_recursive_parsing_function(parsing_function_yaml, folder)
    # Parsing son files
    edit_in_tree(conv_pars, condition_function, f_edit, if_flatten=True)

    # Edit paths
    conv_pars = edit_relative_paths_functions(conv_pars, configuration_file)
    conv_pars = edit_relative_paths(conv_pars, configuration_file)

    return conv_pars


def parse_configuration_file_pickle(configuration_file):
    # Parse parent directory
    conv_pars = pickle.load(open(configuration_file, "rb"))
    conv_pars = conv_pars if isinstance(conv_pars, dict) else conv_pars[0]
    # Edit functions
    folder = os.path.dirname(configuration_file)
    cond_parsing_tree = create_condition_function_parsing_tree(folder)
    condition_function = create_condition('states', cond_parsing_tree, 'and')
    f_edit = create_recursive_parsing_function(parsing_function_pickle, folder)

    # Parsing son files
    edit_in_tree(conv_pars, condition_function, f_edit, if_flatten=True)

    # Edit paths
    conv_pars = edit_relative_paths_functions(conv_pars, configuration_file)
    conv_pars = edit_relative_paths(conv_pars, configuration_file)
    return conv_pars


def parse_configuration_file_db(configuration_file):
    # Parse parent directory
    conv_pars = yaml.load(open(configuration_file).read())
    conv_pars = conv_pars if isinstance(conv_pars, dict) else conv_pars[0]
    folder = os.path.dirname(configuration_file)

    # To parameters
    def to_parameters(par):
        assert('name' in par)
        if 'filepath' in par:
            filepath = par['filepath']
            if not os.path.isfile(filepath):
                filepath = os.path.join(folder, filepath)
            par_db = parse_configuration_file_dbapi(filepath)
            edit_functions_in_parameters(par_db, filepath)
        else:
            assert('parameters' in par)
            par_db = par['parameters']
        return {par['name']: par_db}

    databases = {}
    if isinstance(conv_pars['databases'], list):
        for i, par in enumerate(conv_pars['databases']):
            databases.update(to_parameters(par))
    conv_pars['databases'] = databases
    return conv_pars


def parse_configuration_file_dbapi(configuration_file):
    # Parse parent directory
    conv_pars = yaml.load(open(configuration_file).read())
    conv_pars = conv_pars if isinstance(conv_pars, dict) else conv_pars[0]

    # Edit paths
    folder = os.path.dirname(configuration_file)
    conv_pars = edit_relative_paths(conv_pars, configuration_file)
    conv_pars = abspath_dbapi(conv_pars, folder)

    # Edit functions
    edit_functions_in_parameters(conv_pars, configuration_file)
    return conv_pars


def create_recursive_parsing_function(parser, abspath):
    def parser_function(conf_file):
        if not os.path.isabs(conf_file):
            conv_pars = parser(os.path.join(abspath, conf_file))
        else:
            conv_pars = parser(conf_file)
        return conv_pars
    return parser_function


def parsing_function_yaml(conf_file):
    # Parse file
    conv_pars = yaml.load(open(conf_file).read())
    return conv_pars


def parsing_function_pickle(conf_file):
    # Parse file
    conv_pars = pickle.load(open(conf_file, "rb"))
    return conv_pars


################################ Utils Parsing ################################
def edit_functions_in_parameters(conv_pars, configuration_file):
    condition_function =\
        create_condition_parsing_functions_chatbotquery_parameters()
    folder = os.path.dirname(configuration_file)
    f_edit = create_parsing_function_functions(parse_parameter_functions,
                                               folder)
    pathgen = PathGenerator()
    # Parsing son files
#    edit_in_tree(conv_pars, condition_function, f_edit, if_flatten=False)
    edit_in_tree_new(conv_pars, condition_function, pathgen, f_edit)


def condition_function_parsing_tree(tree):
    logi = False
    if type(tree) == str:
        logi = os.path.isfile(tree)
    return logi


def create_condition_function_parsing_tree(abspath):
    def condition_function_parsing_tree(tree):
        logi = False
        if type(tree) == str:
            abstree = os.path.join(abspath, tree)
            logi = os.path.isfile(tree) or os.path.isfile(abstree)
        return logi
    return condition_function_parsing_tree


def create_condition(cond_key, cond_tree, logical_add='and'):
    # Create bi logic function
    if logical_add == 'and':
        f_logic = lambda x, y: x and y
    else:
        f_logic = lambda x, y: x or y
    # Create key logic function
    if not callable(cond_key):
        key_eq = cond_key[:]

        def cond_key(pathtree):
            if isinstance(pathtree, list):
                return pathtree[-1] == key_eq
            else:
                return pathtree == key_eq

    # Create function condition
    def condition_function(pathtree, tree):
        x_key = cond_key(pathtree)
        y_tre = cond_tree(tree)
        return f_logic(x_key, y_tre)
    return condition_function


def create_condition_parsing_chatbotquery_parameters():
    def condition_function_states(tree):
        "Explorer the tree of states of parameters."
        logi = False
        if isinstance(tree, dict):
            logi = ('name' in tree)
        return logi

    def condition_function_states_key(pathtree):
        "Exploring lists in the tree of states of parameters."
        logi = False
        if isinstance(pathtree, (list, tuple)):
            if len(pathtree):
                logi = isinstance(pathtree[-1], (int, np.int))
                if len(pathtree) > 1:
                    logi = logi and not isinstance(pathtree[-2], (int, np.int))
        else:
            logi = isinstance(pathtree, (int, np.int))
        return logi
    condition_function =\
        create_condition(condition_function_states_key,
                         condition_function_states, 'and')
    return condition_function


def create_condition_parsing_functions_chatbotquery_parameters():
    def condition_function_functions(tree):
        "Explorer the tree of states of parameters."
        logi = False
        if isinstance(tree, dict):
            logi = ('filepath' in tree) and ('function_name' in tree)
        return logi

    def condition_function_functions_key(pathtree):
        "Exploring lists in the tree of states of parameters."
        logi = True
        return logi
    condition_function =\
        create_condition(condition_function_functions_key,
                         condition_function_functions, 'and')
    return condition_function


def edit_relative_paths_functions(parameters, configuration_file):
    # Edit functions
    condition_function =\
        create_condition_parsing_functions_chatbotquery_parameters()
    folder = os.path.dirname(configuration_file)
    f_edit = create_abspath_function_functions(folder)
    pathgen = PathGenerator()
    # Parsing son files
#    edit_in_tree(conv_pars, condition_function, f_edit, if_flatten=False)
    edit_in_tree_new(parameters, condition_function, pathgen, f_edit)
    return parameters


def edit_relative_paths(parameters, configuration_file):
    # Edit functions
    def condition_function_paths(tree):
        "Explorer the tree of states of parameters."
        logi = False
        if isinstance(tree, dict):
            logi = ('filepath' in tree)
        return logi
    condition_function =\
        create_condition(lambda pathtree: True,
                         condition_function_paths, 'and')

    folder = os.path.dirname(configuration_file)
    f_edit = create_abspath_function_functions(folder)
    pathgen = PathGenerator()
    # Parsing son files
#    edit_in_tree(conv_pars, condition_function, f_edit, if_flatten=False)
    edit_in_tree_new(parameters, condition_function, pathgen, f_edit)
    return parameters


def abspath_dbapi(parameters, abspath):
    if not os.path.isabs(parameters['data_info']):
        parameters['data_info'] = os.path.join(abspath,
                                               parameters['data_info'])
    return parameters


############################## Storing functions ##############################
###############################################################################
def storing_parameters_pickle(configuration_pars, conf_file):
    pickle.dump(configuration_pars, open(conf_file, "wb"))


def storing_parameters_yaml(configuration_pars, conf_file):
    if isinstance(configuration_pars, dict):
        configuration_pars = [configuration_pars]
    pickle.dump(configuration_pars, open(conf_file, "wb"),
                default_flow_style=False)


################################# Testing mode ################################
###############################################################################
def create_testing_mode_parameters(parameters):
    ## 0. Parameters parsing
    parameters = parameters if isinstance(parameters, list) else [parameters]
    condition_function = create_condition_parsing_chatbotquery_parameters()
    pathgen = PathGenerator()

    ## 1. Edit states
    edit_in_tree_new(parameters, condition_function, pathgen,
                     testing_mode_editing)

    return parameters


def testing_mode_editing(tree):
    tree['test_mode'] = True
    return tree


############################## Create descriptors #############################
###############################################################################
def create_tables(parameters):
    ## 0. Table of states
    parameters = parameters if isinstance(parameters, list) else [parameters]
    states_list_table, path_states, xstates = create_states_table(parameters)

    ## 1A. Prepare table of transitions
    def retriever_transitions(path, state):
        if 'transition' not in state:
            return path, []
        if state['transition'] is None:
            return path, []
        if isinstance(state['transition'], list):
            states_transitions = [s['transition_states']
                                  for s in state['transition']]
        else:
            states_transitions = state['transition']['transition_states']
        return path, states_transitions
    pathgen = PathGenerator()
    condition_function = create_condition_parsing_chatbotquery_parameters()
    description_pars = condition_function, pathgen, retriever_transitions

    ## 1B. Table of transitions
    transitions = create_transitions(parameters, description_pars, path_states)

    return states_list_table, path_states, xstates, transitions


def create_graphs(states_list_table, path_states, xstates, transitions):
    treestates = create_tree_states(states_list_table)
    graphs_statemachines = create_graphs_by_statemachine(transitions, xstates)
    complete_network =\
        create_network_whole_machine(states_list_table, transitions, xstates)
    return treestates, graphs_statemachines, complete_network


def create_tree_states(states_list_table):
    def get_parentpath(path):
        return '.'.join(path.split('.')[:-1])

    ## Create edgelist
    edgelist = []
    for i, element in states_list_table.iterrows():
        if element['level'] != 0:
            edgelist.append((get_parentpath(element['Pathname']),
                             element['Pathname']))

    ## Graph in networkx
    G = nx.DiGraph(edgelist)
    return G


def create_graphs_by_statemachine(transitions, xstates):
    statemachines = transitions['StateMachine'].unique()
    statemachines = [s for s in statemachines if s != '']

    levels = []
    for smachine in statemachines:
        aux = transitions[transitions['StateMachine'] == smachine]['level']
        levels.append(list(aux)[0])

    graphs = []
    for i, smachine in enumerate(statemachines):
        tr = transitions[transitions['StateMachine'] == smachine]
        startstate = xstates[smachine]['StartState']
        endstates = xstates[smachine]['EndStates']
        if len(tr) == 1:
            G = nx.DiGraph()
            ending_states = list(tr['initial'])
            G.add_node(ending_states[0])
        else:
            edgelist = []
            for j, r in tr.iterrows():
                if r['end'] is not None:
                    edgelist.append((r['initial'], r['end'],
                                     {'transition': int(r['transition_number'])
                                      }))
            G = nx.DiGraph(edgelist)

        graphs.append((levels[i], smachine, G, startstate, endstates))

    return graphs


def create_network_whole_machine(states_list_table, transitions, xstates):
    initial =\
        list(states_list_table[states_list_table['level'] == 0]['Pathname'])[0]
    initial_state = initial[:]
    endstates = list(transitions[transitions['end'].isnull()]['initial'])

    def ifstate(pathname):
        aux = states_list_table[states_list_table['Pathname'] == pathname]
        aux = list(aux['IfStateMachine'])[0]
        return not aux

    def get_startState(pathname):
        aux = states_list_table[states_list_table['Pathname'] == pathname]
        aux = list(aux['StartState'])[0]
        return path_builder_states(aux, pathname)

    def get_states_transition(initial_pathname):
        aux = transitions[transitions['initial'] == initial_pathname]['end']
        #### WARNING: Sorted by transitions_number
        next_states = [aux.iloc[i] for i in range(len(aux))]
        return next_states

    def get_parentpath(path):
        return '.'.join(path.split('.')[:-1])

    def get_highparent(path):
        path = get_parentpath(path)
        if path == initial_state:
            return path
        if path in endstates:
            return get_highparent(path)
        return path

    def get_sonstate(path):
        if ifstate(path):
            return path
        path = path_builder_states(xstates[path]['StartState'], path)
        if not ifstate(path):
            return get_sonstate(path)
        return path

    def get_next_state(initial_pathname):
        next_states = get_states_transition(initial_pathname)
        if next_states[0] is None:
            # Get parent not ending state
            next_state = get_highparent(initial_pathname)
            if next_state == initial_state:
                return None
            next_states = get_states_transition(next_state)
            next_states = [get_sonstate(next_s) for next_s in next_states]
        return next_states

    def flatten_1lvl(endstates):
        if endstates:
            if isinstance(endstates[0], list):
                new_endstates = []
                for ends in endstates:
                    new_endstates.extend(ends)
                return new_endstates
        return endstates

    def get_endstates():
        pos_end = []
        for ends in states_list_table['EndStates']:
            if ends is not None:
                pos_end.extend(flatten_1lvl(list(ends)))
        logi = states_list_table['IfStateMachine'].apply(lambda x: x is False)
        statesnames = list(states_list_table.loc[logi, 'NameState'])
        ends = []
        for end in pos_end:
            if end in statesnames:
                ends.append(end)

    def get_end_states(i_state):
        ends = flatten_1lvl(xstates[i_state]['EndStates'])
        end_states = []
        for st in ends:
            cst = '.'.join([i_state, st.replace(' ', '_')])
            if cst in xstates:
                cst = get_end_states(cst)
                cst = cst if isinstance(cst, list) else [cst]
                end_states.extend(cst)
            else:
                end_states.append(cst)
        return end_states

    ## Graph transitions
    initial = get_sonstate(initial)
    to_explore = [initial]
    explored = []
    edgelist = []
    while to_explore:
        initial = to_explore.pop()
        nextstates = get_next_state(initial)
        if nextstates is not None:
            for i, nextstate in enumerate(nextstates):
                edgelist.append((initial, nextstate,
                                 {'transition': int(i)}))
                if (nextstate not in explored+to_explore):
                    to_explore.append(nextstate)
        explored.append(initial)

    ## Graph strutcture
    G = nx.DiGraph(edgelist)

    ## Ensure correctness
    statesnames = states_list_table[~states_list_table['IfStateMachine']]
    statesnames = list(statesnames['Pathname'])
    if len(G.nodes()) != len(statesnames):
        notexplored = [s for s in statesnames if s not in G.nodes()]
        msg = "There are some states not connected with the initial state."
        msg += '\n * '+'\n * '.join(notexplored)
        raise KeyError(msg)
    graph = (0, initial_state, G, get_sonstate(initial_state),
             get_end_states(initial_state))
    return graph


def create_states_table(parameters):
    ## 0. Parameters parsing
    def retriever_state_names(path, state):
        if 'states' in state:
            ifstatemachine = True
            initialstate = state['startState']
            endstates = state['endStates']
        else:
            ifstatemachine = False
            initialstate = None
            endstates = None
        return path, state['name'], ifstatemachine, initialstate, endstates
    parameters = parameters if isinstance(parameters, list) else [parameters]
    condition_function = create_condition_parsing_chatbotquery_parameters()
    pathgen = PathGenerator()

    ## 1. Finding states
    states = []
    for p in find_descriptions_new(parameters, condition_function, pathgen,
                                   retriever_state_names):
        states.append(p)
    levels_len = list(set([len(s[0]) for s in states]))

    ## 2. Create tables
    states_list_table, path_states, xstates =\
        ensemble_table_states(states, levels_len)
    return states_list_table, path_states, xstates


def create_transitions(parameters, description_pars, raw_paths_conv):
    parameters = parameters if isinstance(parameters, list) else [parameters]

    transitions = []
    for p in find_descriptions_new(parameters, *description_pars):
        ## Preparing transtitions
        pathname = raw_paths_conv[tuple(p[0])]
        pathlist = pathname.split('.')
        level_p = len(pathlist)-1
        parentpath = '.'.join(pathlist[:-1])
        ## Transition storing
        if len(p[1]) == 0:
            transition = (level_p, parentpath, pathname, None, None)
            transitions.append(transition)
        else:
            if isinstance(p[1][0], list):
                assert(all([isinstance(pi, list) for pi in p[1]]))
                for trans in p[1]:
                    for i, tr in enumerate(trans):
                        transition = (level_p, parentpath, pathname,
                                      path_builder_states(tr, parentpath), i)
                        transitions.append(transition)
            else:
                for i, tr in enumerate(p[1]):
                    transition = (level_p, parentpath, pathname,
                                  path_builder_states(tr, parentpath), i)
                    transitions.append(transition)

    column_names = ['level', 'StateMachine', 'initial', 'end',
                    'transition_number']
    transitions = pd.DataFrame(transitions, columns=column_names)
    return transitions


########################## Utils descriptors creation #########################
def ensemble_table_states(states, levels_len):
    def path_builder(namepath, parentpath=''):
        namepath = namepath.replace(' ', '_')
        parentpath = parentpath.replace(' ', '_')
        if parentpath:
            namepath = parentpath+'.'+namepath
        return namepath

    states_list_table = []
    path_states = {}
    xstates = {}
    for i, l in enumerate(levels_len):
        for s in states:
            path_s, namepath_s, ifstatemachine, initialstate, endstates = s
            if l == len(path_s):
                ## Search parent path
                if i != 0:
                    parentpath = path_states[tuple(path_s[:levels_len[i-1]])]
                else:
                    parentpath = ''
                ## Store
                pathname_s = path_builder(namepath_s, parentpath)
                path_states[tuple(path_s)] = pathname_s
                states_list_table.append((i, pathname_s, namepath_s,
                                          ifstatemachine, initialstate,
                                          endstates))
                if ifstatemachine:
                    xstates[pathname_s] = {'StartState': initialstate,
                                           'EndStates': endstates}
    states_list_table =\
        pd.DataFrame(states_list_table,
                     columns=['level', 'Pathname', 'NameState',
                              'IfStateMachine', 'StartState', 'EndStates'])
    return states_list_table, path_states, xstates


def path_builder_states(namepath, parentpath=''):
    namepath = namepath.replace(' ', '_')
    parentpath = parentpath.replace(' ', '_')
    if parentpath:
        namepath = parentpath+'.'+namepath
    return namepath

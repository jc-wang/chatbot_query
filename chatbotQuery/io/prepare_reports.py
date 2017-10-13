
import re
import os
import shutil
import numpy as np
import pandas as pd
import networkx as nx

from networkx.algorithms.traversal.depth_first_search import dfs_tree

from chatbotQuery.io.parameters_processing import create_tables,\
    create_graphs, parse_configuration_file, parse_configuration_file_db


######################### Old Auxiliar create reports #########################
###############################################################################
"""
def generate_html_states_table_file(states_list_table):
    html_file = os.path.join(os.path.dirname(__file__),
                             'templates/table_states.html')
    script_file = os.path.join(os.path.dirname(__file__),
                               'templates/script_tablefilter.txt')
    with open(html_file, 'r') as html_template:
        html_table_file = html_template.read()
    with open(script_file, 'r') as html_template:
        script_tf = html_template.read()

    ## Display changes
    old_width = pd.get_option('display.max_colwidth')
    pd.set_option('display.max_colwidth', -1)

    ## To html
    html_table = states_list_table.to_html(index=False, border=0,
                                           classes=['table', 'filterable'])

    ## Reset old values of display
    pd.set_option('display.max_colwidth', old_width)

    html_table_file = html_table_file.format(table=html_table,
                                             script_tablefilter=script_tf)
    return html_table_file


def generate_html_transitions_table_file(transitions_table):
    html_file = os.path.join(os.path.dirname(__file__),
                             'templates/table_transitions.html')
    script_file = os.path.join(os.path.dirname(__file__),
                               'templates/script_tablefilter.txt')
    with open(html_file, 'r') as html_template:
        html_table_file = html_template.read()
    with open(script_file, 'r') as html_template:
        script_tf = html_template.read()

    ## Display changes
    old_width = pd.get_option('display.max_colwidth')
    pd.set_option('display.max_colwidth', -1)

    ## To html
    html_table = transitions_table.to_html(index=False, border=0,
                                           classes=['table', 'filterable'])

    ## Reset old values of display
    pd.set_option('display.max_colwidth', old_width)

    html_table_file = html_table_file.format(table=html_table,
                                             script_tablefilter=script_tf)
    return html_table_file


def write_html_states_table(states_list_table, output_file):
    html_table_file = generate_html_states_table_file(states_list_table)
    with open(output_file, 'wb') as f:
        f.write(bytes(html_table_file, 'UTF-8'))


def write_html_transitions_table(transitions_table, output_file):
    html_table_file = generate_html_transitions_table_file(transitions_table)
    with open(output_file, 'wb') as f:
        f.write(bytes(html_table_file, 'UTF-8'))
"""


########################### Auxiliar create reports ###########################
###############################################################################
def prepare_states_list_table(states_list_table):
    def remove_nones(s):
        if s is None:
            return ''
        return s

    def getParentPath(s):
        return '.'.join(s.split('.')[:-1])

    ## Edit table
    states_list_table['StartState'] =\
        states_list_table['StartState'].apply(remove_nones)
    states_list_table['EndStates'] =\
        states_list_table['EndStates'].apply(remove_nones)
    states_list_table['StateMachine'] =\
        states_list_table['Pathname'].apply(getParentPath)

    filterable = ['level', 'StateMachine', 'NameState', 'IfStateMachine',
                  'StartState', 'EndStates']
    states_list_table = states_list_table[filterable]

    return states_list_table


def prepare_transitions(transitions):
    def remove_nones_getting_name(s):
        if s is None:
            return ''
        return s.split('.')[-1]

    def remove_number(r):
        if np.isnan(r):
            return ''
        else:
            return str(int(r))

    ## Edit table
    transitions['initial'] =\
        transitions['initial'].apply(remove_nones_getting_name)
    transitions['end'] = transitions['end'].apply(remove_nones_getting_name)
    transitions['transition_number'] =\
        transitions['transition_number'].apply(remove_number)
    # Sort table
    transitions = transitions.sort_values(['level', 'StateMachine', 'initial',
                                           'transition_number'],
                                          ascending=[True, True, True, True])
    return transitions


def build_tree_recursive(tree, parent, treegraph):
    # find children
    children = treegraph.neighbors(parent)
    # build a subtree for each child
    if children:
        tree["children"] = []
        for i, child in enumerate(children):
            # start new subtree
            tree["children"].append({"name": child.split('.')[-1]})
            # call recursively to build a subtree for current node
            build_tree_recursive(tree["children"][i], child,
                                 dfs_tree(treegraph, child))


############################## Old Create reports #############################
###############################################################################
"""
def create_reports(chat_conf_file, db_conf_file, outputfolder):
    ## Read parameters
    cf_pars = parse_configuration_file(chat_conf_file)
    db_pars = parse_configuration_file_db(db_conf_file)

    ## Create folder
    if not os.path.exists(outputfolder):
        os.makedirs(outputfolder)
    html_folder = os.path.join(outputfolder, 'templates')
    if not os.path.exists(html_folder):
        os.makedirs(html_folder)
    pars_folder = os.path.join(outputfolder, 'parameters')
    if not os.path.exists(pars_folder):
        os.makedirs(pars_folder)
    static_folder = os.path.join(outputfolder, 'static')
    if not os.path.exists(static_folder):
        os.makedirs(static_folder)

    ## Copy static files folder
    dirname = os.path.dirname(__file__)
    static_files = os.path.join(dirname, '../storage/static')
    copy_folder(static_files, os.path.join(outputfolder, 'static'))

    ## Copy scripts files
    main_script = os.path.join(dirname, '../storage/scripts/test_script.txt')
    parameters_main_script = {'db_configuration_file': db_conf_file,
                              'configuration_file': chat_conf_file}
    copy_format_script(main_script, outputfolder, parameters_main_script)

    ## Copy parameter folder
    folderparameters = os.path.dirname(chat_conf_file)
    outputfolderparameters = os.path.join(outputfolder, 'parameters')
    copy_folder(folderparameters, outputfolderparameters)
    if folderparameters != os.path.dirname(db_conf_file):
        outputfolderparameters = os.path.join(outputfolder, 'parameters')
        copy_folder(folderparameters, outputfolderparameters)

    ## Write html files
    states_list_file = os.path.join(html_folder, 'states_list_table.html')
    transitions_file = os.path.join(html_folder, 'transitions_table.html')
    states_list_table, _, _, transitions_table = create_tables(cf_pars)
    states_list_table = prepare_states_list_table(states_list_table)
    transitions_table = prepare_transitions(transitions_table)
    write_html_states_table(states_list_table, states_list_file)
    write_html_transitions_table(transitions_table, transitions_file)
    testingchat_file = os.path.join(dirname, 'templates/testing_chat.html')
    copy_file(testingchat_file, html_folder)
    treegraph_file = os.path.join(dirname, 'templates/tree_graph.html')
    copy_file(treegraph_file, html_folder)
"""


########################## Initialize testing folder ##########################
###############################################################################
def create_testing_project(chat_conf_file, db_conf_file, templates_folder,
                           outputfolder):
    ## Create folder
    if not os.path.exists(outputfolder):
        os.makedirs(outputfolder)
    html_folder = os.path.join(outputfolder, 'templates')
    if not os.path.exists(html_folder):
        os.makedirs(html_folder)
    pars_folder = os.path.join(outputfolder, 'parameters')
    if not os.path.exists(pars_folder):
        os.makedirs(pars_folder)
    static_folder = os.path.join(outputfolder, 'static')
    if not os.path.exists(static_folder):
        os.makedirs(static_folder)

    ## Copy static files folder
    static_files = os.path.join(templates_folder, 'static')
    copy_folder(static_files, os.path.join(outputfolder, 'static'))

    ## Copy templates files folder
    static_files = os.path.join(templates_folder, 'templates')
    copy_folder(static_files, os.path.join(outputfolder, 'templates'))

    ## Copy parameter folder
    folderparameters = os.path.dirname(chat_conf_file)
    outputfolderparameters = os.path.join(outputfolder, 'parameters')
    copy_folder(folderparameters, outputfolderparameters)
    if folderparameters != os.path.dirname(db_conf_file):
        outputfolderparameters = os.path.join(outputfolder, 'parameters')
        copy_folder(folderparameters, outputfolderparameters)

    ## Copy scripts files
    main_script = os.path.join(templates_folder, 'scripts/test_script.txt')
    parameters_main_script = {'db_configuration_file': db_conf_file,
                              'configuration_file': chat_conf_file}
    copy_format_script(main_script, outputfolder, parameters_main_script)


############################# Generate html tables ############################
###############################################################################
def generate_info_reports(chat_conf_file):
    ## Parse file
    cf_pars = parse_configuration_file(chat_conf_file)
    ## Raw information
    states_list_table, path_states, xstates, transitions =\
        create_tables(cf_pars)
    treestates, graphs_statemachines, complete_network =\
        create_graphs(states_list_table, path_states, xstates, transitions)
    ## Prepare data for reports
    states_list_table = prepare_states_list_table(states_list_table)
    transitions_table = prepare_transitions(transitions)
    treestates = prepare_treestates(treestates)
    complete_network = prepare_complete_graph(complete_network)
    graphs_json = prepare_statemachines_graphs(graphs_statemachines)
    return states_list_table, transitions_table, treestates, complete_network,\
        graphs_statemachines, graphs_json


def generate_html_states_table(states_list_table):
    ## Display changes
    old_width = pd.get_option('display.max_colwidth')
    pd.set_option('display.max_colwidth', -1)

    ## To html
    html_table = states_list_table.to_html(index=False, border=0,
                                           classes=['table', 'filterable'])

    ## Reset old values of display
    pd.set_option('display.max_colwidth', old_width)

    return html_table


def generate_html_transitions_table(transitions_table):
    ## Display changes
    old_width = pd.get_option('display.max_colwidth')
    pd.set_option('display.max_colwidth', -1)

    ## To html
    html_table = transitions_table.to_html(index=False, border=0,
                                           classes=['table', 'filterable'])

    ## Reset old values of display
    pd.set_option('display.max_colwidth', old_width)

    return html_table


def prepare_treestates(treestates):
    root = nx.topological_sort(treestates)[0]
    # create empty tree to fill
    tree = {"name": root}
    # fill in tree starting with roots (those with no parent)
    build_tree_recursive(tree, root, treestates)
    return tree


def prepare_complete_graph(complete_graph):
    ### TODO: initial and end node
    def get_path(s):
        return '.'.join(s.split('.')[1:])
    _, _, graph, initial, endstates = complete_graph

    graph_json = {}
    graph_json["nodes"] = [{"id": get_path(node), "type": "normal"}
                           for node in graph.nodes()
                           if (node != initial) and (node not in endstates)]
    graph_json["nodes"].append({"id": get_path(initial), "type": "init"})
    graph_json["nodes"].extend([{"id": get_path(node), "type": "end"}
                                for node in endstates])
    graph_json["links"] = [{"source": get_path(s), "target": get_path(t),
                            "transition": d['transition']}
                           for s, t, d in graph.edges(data=True)]
    return graph_json


def prepare_statemachines_graphs(graphs_statemachines):
    def flatten_1lvl(endstates):
        if endstates:
            if isinstance(endstates[0], list):
                new_endstates = []
                for ends in endstates:
                    new_endstates.extend(ends)
                return new_endstates
        return endstates

    def get_path(s):
        return '.'.join(s.split('.')[1:])

    graphs_json = []
    for lvl, name, graph, init, ends in graphs_statemachines:
        init = '.'.join([name, init.replace(' ', '_')])
        ends = ['.'.join([name, end.replace(' ', '_')])
                for end in flatten_1lvl(ends)]
        graph_json = {}
        graph_json['lvl'] = lvl
        graph_json["name"] = name
        graph_json["nodes"] = [{"id": get_path(node), "type": "normal"}
                               for node in graph.nodes()
                               if ((node != init) and
                                   (node not in flatten_1lvl(ends)))]
        graph_json["nodes"].append({"id": get_path(init), "type": "init"})
        graph_json["nodes"].extend([{"id": get_path(node), "type": "end"}
                                    for node in flatten_1lvl(ends)
                                    if node != init])
        graph_json["links"] = [{"source": get_path(s), "target": get_path(t),
                                "transition": d['transition']}
                               for s, t, d in graph.edges(data=True)]
        graphs_json.append(graph_json)
    return graphs_json


############################## Auxiliar functions #############################
###############################################################################
def copy_file(inputfile, outputfolder):
    with open(inputfile, 'r') as text_template:
        filetext = text_template.read()
    basename = os.path.basename(inputfile)
    with open(os.path.join(outputfolder, basename), 'wb') as f:
        f.write(bytes(filetext, 'UTF-8'))


def copy_folder(inputfolder, outputfolder):
    ## Copy parameter folder
    for name in os.listdir(inputfolder):
        from_element = os.path.join(inputfolder, name)
        to_element = os.path.join(outputfolder, name)
        if (os.path.isfile(from_element) and not os.path.isfile(to_element)):
            shutil.copy2(from_element, to_element)
        elif not (os.path.isdir(to_element) or os.path.isfile(to_element)):
            shutil.copytree(from_element, to_element)
#        if os.path.isfile(from_element):
#            shutil.copy2(from_element, to_element)
#        else:
#            shutil.copytree(from_element, to_element)


def copy_format_script(inputfile, outputfolder, parameters={}):
    with open(inputfile, 'r') as script_template:
        script_lines = script_template.readlines()

    script = []
    if parameters != {}:
        pars_keys = ["'{"+key+"}'" for key in parameters]
#        patterns = [re.compile(pk) for pk in pars_keys]
        for line in script_lines:
            if not all([(re.search(pk, line) is None) for pk in pars_keys]):
                line = line.format(**parameters)
            script.append(line)
    script = ''.join(script)

    filename, _ = os.path.splitext(os.path.basename(inputfile))
    filename = filename+'.py'
    outputfile = os.path.join(outputfolder, filename)
#    shutil.copy2(inputfile, outputfile)

    with open(outputfile, 'wb') as script_file:
        script_file.write(bytes(script, 'UTF-8'))

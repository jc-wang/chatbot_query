
import xmltodict
import os
from importlib.machinery import SourceFileLoader


def chooser_io(filepath):
    answers = xmltodict.parse(open(filepath).read(), process_namespaces=True)
    answers = answers['answer_collection']['answer']
    answers = answers if type(answers) == list else [answers]
    answers = [dict(answer) for answer in answers]
    return answers


def parse_parameter_functions(parameters):
    assert('filepath' in parameters)
    assert('function_name' in parameters)
    logi = 'function_parameters' in parameters
    filepath = os.path.abspath(parameters['filepath'])
    filename = os.path.splitext(os.path.basename(filepath))[0]
#    path2file = os.path.dirname(filepath)
#    mod = __import__(filename)
    mod = SourceFileLoader(filename, filepath).load_module()
    functions_collection = vars(mod)
    f_selected = functions_collection[parameters['function_name']]
    if logi:
        f_selected = f_selected(**parameters['function_parameters'])
    return f_selected


def create_abspath_function_functions(abspath):
    def abspath_function(parameters):
        if not os.path.isabs(parameters['filepath']):
            parameters['filepath'] = os.path.join(abspath,
                                                  parameters['filepath'])
        return parameters
    return abspath_function


def create_parsing_function_functions(parser, abspath):
    def parser_function(parameters):
        f_selected = parser(parameters)
        return f_selected
    return parser_function


"""
Auxiliar functions
------------------
Some auxiliar functions to help carry out some tasks.

"""

import copy


def yes_no_answer(message):
    """Condition function for yes and no answers.
    Yes: 1, No: 0
    """
    #no = ['n', 'no', 'not']
    response = message['message']
    yes = ['y', 'yes']
    split_response = response.lower().split(' ')
    affirmative = False
    for st in yes:
        affirmative = affirmative or (st in split_response)
    return int(affirmative)


def create_probsplitter_condition(splits, value_path):

    def condition(message):
        value = copy.copy(message)
        for var in value_path:
            value = value[var]
        # Probability splitter
        interval = splitter(value, splits)
        return interval

    return condition


def create_fixed_condition(selected=0):

    def condition(message):
        return selected

    return condition


def create_fixed_reacted_condition():

    def condition(message):
        return message

    return condition


def create_null_condition():

    def condition(message):
        return 0

    return condition


def check_name(candidatename):
    return 1.


def splitter(value, splits):
    interval = -1
    for i in range(len(splits)-1):
        if splits[i] <= value <= splits[i+1]:
            interval = len(splits)-2-i
    return interval

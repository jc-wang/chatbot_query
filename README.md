[![Build Status](https://travis-ci.org/tgquintela/chatbot_query.svg?branch=master)](https://travis-ci.org/tgquintela/chatbot_query)
[![Coverage Status](https://coveralls.io/repos/github/tgquintela/chatbot_query/badge.svg?branch=master)](https://coveralls.io/github/tgquintela/chatbot_query?branch=master)

# ChatbotQuery

Framework to easily build functional simple chatbots with purpose of maintain basic conversations for querying databases.


## Installation

It could be installed using shell

```shell
git clone https://github.com/tgquintela/chatbot_query
.\install
```

### Main dependences:
* [numpy](http://www.numpy.org/)
* [scipy](https://www.scipy.org/)
* [scikit-learn](http://scikit-learn.org/stable/)
* [pandas](http://pandas.pydata.org/)
* [jellyfish](https://github.com/jamesturk/jellyfish)
* [textblob](https://textblob.readthedocs.io/en/dev/)
* [stemming](https://pypi.python.org/pypi/stemming/1.0)

## Testing

You need to ensure that all the package requirements are installed. ChatbootQuery provide a testing module which could be called by importing the module and applying test function.
It can be tested from the shell

```shell
>> ./test_script.sh
```
and also for developers you can test from the source using nosetests of nose package.

```shell
>> python3 -m "nose" --with-coverage --cover-package=chatbotQuery
```

## Examples
There are different examples. That scripts can be runned using python

```shell
>> python example_script.py
```

The examples are:
* `example_discourse.py`: A simple bot who only speaks.
* `example_basic_conversation.py`: A simple bot who creates a profile of the user, if it don't have that profile in its database.
* `example_dbquery.py`: Example of querying a database. There is a process of interaction as a substitution of a simple query. It is an accumulative query using the accepted queries done before.


### Next steps
- [ ] Parse XML and AIML format file for chooser.
- [ ] Support for AIML sentence buildings.
- [ ] Refactorize DBAPI to Support other DBs and different queries communication.
- [ ] Build network of possible states in conversation state machines.

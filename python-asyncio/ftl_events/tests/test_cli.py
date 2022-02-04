

import ftl_events.cli
import docopt
import os
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))

def test_cli():
    with pytest.raises(docopt.DocoptExit):
        ftl_events.cli.main([])


def test_cli2():
    os.chdir(HERE)
    ftl_events.cli.main(['-M', 'modules', '-i', 'inventory.yml', '--debug', 'test_rules2.yml'])


def test_cli3():
    os.chdir(HERE)
    ftl_events.cli.main(['-M', 'modules', '-i', 'inventory.yml', '--verbose', 'test_rules2.yml'])


def test_cli4():
    os.chdir(HERE)
    os.environ['TEST_X'] = '5'
    ftl_events.cli.main(['-M', 'modules', '-i', 'inventory.yml', '--vars', 'vars.yml', 'test_rules2.yml'])

def test_cli5():
    os.chdir(HERE)
    os.environ['TEST_X'] = '5'
    ftl_events.cli.main(['-M', 'modules', '-i', 'inventory.yml', '--env-vars', 'TEST_X', 'test_rules2.yml'])


def test_cli6():
    os.chdir(HERE)
    os.environ['TEST_X'] = '5'
    ftl_events.cli.main(['-M', 'modules', '-i', 'inventory.yml', '--requirements', 'requirements.txt', 'test_rules2.yml'])

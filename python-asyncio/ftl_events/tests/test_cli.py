

import ftl_events.cli
import docopt
import os

HERE = os.path.dirname(os.path.abspath(__file__))

def test_cli():
    try:
        ftl_events.cli.main([])
        assert False
    except docopt.DocoptExit:
        pass


def test_cli2():
    os.chdir(HERE)
    ftl_events.cli.main(['-M', 'modules', '-i', 'inventory.yml', 'test_rules2.yml'])

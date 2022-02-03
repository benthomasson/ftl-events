

import ftl_events.cli
import docopt

def test_cli():
    try:
        ftl_events.cli.main()
        assert False
    except docopt.DocoptExit:
        pass

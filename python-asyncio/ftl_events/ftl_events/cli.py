"""
Usage:
    ftl-events [options] <rules.yml>

Options:
    -h, --help                  Show this page
    -v, --vars=<v>              Variables file
    -i, --inventory=<i>         Inventory
    -M=<M>, --module_dir=<M>    Module dir
    --env-vars=<e>              Comma separated list of variables to import from the environment
    --redis_host_name=<h>       Redis host name
    --redis_port=<p>            Redis port
    --debug                     Show debug logging
    --verbose                   Show verbose logging
    --requirements=<r>          Requirements.txt for gate
"""
from docopt import docopt
import os
import logging
import sys
import yaml
import multiprocessing as mp

import ftl_events.rules_parser as rules_parser
from faster_than_light import load_inventory
from ftl_events.engine import start_sources, run_ruleset

logger = logging.getLogger("cli")


def load_vars(parsed_args):
    variables = dict()
    if parsed_args["--vars"]:
        with open(parsed_args["--vars"]) as f:
            variables.update(yaml.safe_load(f.read()))

    if parsed_args["--env-vars"]:
        for env_var in parsed_args["--env-vars"].split(","):
            env_var = env_var.strip()
            if env_var not in os.environ:
                raise KeyError(f'Could not find environment variable "{env_var}"')
            variables[env_var] = os.environ[env_var]

    return variables


def load_rules(parsed_args):
    with open(parsed_args["<rules.yml>"]) as f:
        return rules_parser.parse_rule_sets(yaml.safe_load(f.read()))


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parsed_args = docopt(__doc__, args)
    if parsed_args["--debug"]:
        logging.basicConfig(level=logging.DEBUG)
    elif parsed_args["--verbose"]:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
    logger = mp.log_to_stderr()
    logger.setLevel(logging.INFO)
    variables = load_vars(parsed_args)
    rulesets = load_rules(parsed_args)
    inventory = load_inventory(parsed_args["--inventory"])

    logger.info(f"Variables: {variables}")
    logger.info(f"Rulesets: {rulesets}")

    tasks = []

    dependencies = None
    if parsed_args["--requirements"]:
        with open(parsed_args["--requirements"]) as f:
            dependencies = [x for x in f.read().splitlines() if x]

    for ruleset in rulesets:
        sources = ruleset.sources
        queue = mp.Queue()

        tasks.append(mp.Process(target=start_sources, args=(sources, variables, queue)))
        tasks.append(
            mp.Process(
                target=run_ruleset,
                args=(
                    ruleset,
                    variables,
                    inventory,
                    queue,
                    parsed_args["--redis_host_name"],
                    parsed_args["--redis_port"],
                    [parsed_args["--module_dir"]],
                    dependencies,
                ),
            )
        )

    logger.info("Starting processes")
    for task in tasks:
        task.start()

    logger.info("Joining processes")
    for task in tasks:
        task.join()

    return 0


def entry_point():
    main(sys.argv[1:])

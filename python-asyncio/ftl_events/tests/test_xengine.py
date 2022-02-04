
from durable.lang import *
import durable.lang
import yaml
import os
import asyncio
import multiprocessing as mp

from pprint import pprint

from ftl_events.rules_parser import parse_rule_sets
from ftl_events.rule_generator import generate_rulesets
from ftl_events.util import get_modules
from ftl_events.engine import run_rulesets, start_sources
from ftl_events.messages import Shutdown
from ftl_events.rule_types import EventSource

HERE = os.path.dirname(os.path.abspath(__file__))

def test_start_sources():
    os.chdir(HERE)

    queue = mp.Queue()
    start_sources([EventSource('range', 'range', dict(limit=1), None)], ['sources'], dict(limit=1), queue)
    assert queue.get() == dict(i=0)


def test_run_rulesets():
    os.chdir(HERE)
    with open('test_rules.yml') as f:
        data = yaml.safe_load(f.read())

    rulesets = parse_rule_sets(data)
    pprint(rulesets)

    modules = get_modules(rulesets)
    assert modules == ['argtest']

    ruleset_queues = [(ruleset, mp.Queue()) for ruleset in rulesets]

    queue = ruleset_queues[0][1]
    queue.put(dict())
    queue.put(dict(i=1))
    queue.put(dict(i=2))
    queue.put(dict(i=3))
    queue.put(dict(i=4))
    queue.put(dict(i=5))
    queue.put(Shutdown())

    redis_host_name=None
    redis_port=None
    #redis_host_name='localhost'
    #redis_port=6379

    run_rulesets(ruleset_queues, dict(), dict(), module_dirs=[os.path.join(HERE, 'modules')], redis_host_name=redis_host_name, redis_port=redis_port)

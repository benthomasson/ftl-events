
import durable.lang

from typing import Dict


def assert_fact(ruleset: str, fact: Dict):
    durable.lang.assert_fact(ruleset, fact)


def retract_fact(ruleset: str, fact: Dict):
    durable.lang.retract_fact(ruleset, fact)


def post_event(ruleset: str, fact: Dict):
    durable.lang.post(ruleset, fact)


modules = dict(assert_fact=assert_fact,
               retract_fact=retract_fact,
               post_event=post_event)


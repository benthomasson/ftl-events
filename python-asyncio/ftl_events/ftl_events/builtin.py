
import durable.lang


def assert_fact(ruleset, fact):
    durable.lang.assert_fact(ruleset, fact)


def retract_fact(ruleset, fact):
    durable.lang.retract_fact(ruleset, fact)


def post_event(ruleset, fact):
    durable.lang.post(ruleset, fact)


modules = dict(assert_fact=assert_fact,
               retract_fact=retract_fact,
               post_event=post_event)


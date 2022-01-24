
from durable.lang import ruleset, rule, m
from functools import partial
import asyncio
from faster_than_light import run_module, load_inventory


def call_module(module, module_args):
    try:
        asyncio.run(run_module(load_inventory('inventory.yml'),
                               ['modules'],
                               module,
                               modules=[module],
                               module_args=module_args))
    except Exception as e:
        print(e)


def generate_condition(ftl_condition):
    return m.x == 5


def generate_rulesets(ftl_rulesets):

    rulesets = []

    for ftl_ruleset in ftl_rulesets:
        a_ruleset = ruleset(ftl_ruleset.name)
        with a_ruleset:

            for ftl_rule in ftl_ruleset.rules:
                fn = partial(call_module,
                             module=ftl_rule.action.module,
                             module_args=ftl_rule.action.module_args)
                rule('all', True, generate_condition(ftl_rule.condition))(fn)

    return rulesets

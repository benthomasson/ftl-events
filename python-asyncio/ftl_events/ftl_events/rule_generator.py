
from durable.lang import ruleset, rule, m
import asyncio
import jinja2
from faster_than_light import run_module, load_inventory


def substitute_variables(value, context):
    return jinja2.Template(value, undefined=jinja2.StrictUndefined).render(context)


def call_module(module, module_args, variables, c):
    try:
        print(c)
        variables_copy = variables.copy()
        variables_copy['event'] = str(c.m._d)
        print('running')
        asyncio.run(run_module(load_inventory('inventory.yml'),
                               ['modules'],
                               module,
                               modules=[module],
                               module_args={k: substitute_variables(v, variables_copy) for k, v in module_args.items()}))
        print('ran')
    except Exception as e:
        print(e)


def generate_condition(ftl_condition):
    return m.text != ''


def generate_rulesets(ftl_rulesets, variables):

    rulesets = []

    for ftl_ruleset in ftl_rulesets:
        a_ruleset = ruleset(ftl_ruleset.name)
        with a_ruleset:

            for ftl_rule in ftl_ruleset.rules:
                def fn(c):
                    call_module(ftl_rule.action.module,
                                ftl_rule.action.module_args,
                                variables,
                                c)
                rule('all', True, generate_condition(ftl_rule.condition))(fn)
        rulesets.append(a_ruleset)

    return rulesets

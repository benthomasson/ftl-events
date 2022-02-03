import jinja2
from .builtin import modules as builtin_modules


def get_modules(rulesets):

    modules = []

    for ruleset in rulesets:
        for rule in ruleset.rules:
            if rule.action.module not in builtin_modules:
                modules.append(rule.action.module)

    return list(set(modules))


def substitute_variables(value, context):
    if isinstance(value, str):
        return jinja2.Template(value, undefined=jinja2.StrictUndefined).render(context)
    else:
        return value

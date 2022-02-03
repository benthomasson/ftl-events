from durable.lang import ruleset, rule, m
import jinja2
import logging
from ftl_events.condition_parser import parse_condition
from ftl_events.condition_types import Identifier, String, OperatorExpression

logger = logging.getLogger("cli")


def substitute_variables(value, context):
    return jinja2.Template(value, undefined=jinja2.StrictUndefined).render(context)


def add_to_plan(module, module_args, variables, inventory, plan, c):
    plan.put_nowait((module, module_args, variables, inventory, c))


def visit_condition(parsed_condition, condition):
    if isinstance(parsed_condition, Identifier):
        return condition.__getattr__(parsed_condition.value)
    if isinstance(parsed_condition, String):
        return parsed_condition.value
    if isinstance(parsed_condition, OperatorExpression):
        if parsed_condition.operator == "!=":
            return visit_condition(parsed_condition.left, condition).__ne__(
                visit_condition(parsed_condition.right, condition)
            )
    if isinstance(parsed_condition, OperatorExpression):
        if parsed_condition.operator == "==":
            return visit_condition(parsed_condition.left, condition).__eq__(
                visit_condition(parsed_condition.right, condition)
            )


def generate_condition(ftl_condition):
    return visit_condition(parse_condition(ftl_condition.value), m)


def make_fn(ftl_rule, variables, inventory, plan):
    def fn(c):
        logger.info(f"calling {ftl_rule.name}")
        add_to_plan(
            ftl_rule.action.module,
            ftl_rule.action.module_args,
            variables,
            inventory,
            plan,
            c,
        )

    return fn


def generate_rulesets(ftl_ruleset_plans, variables, inventory):

    rulesets = []

    for ftl_ruleset, plan in ftl_ruleset_plans:
        a_ruleset = ruleset(ftl_ruleset.name)
        with a_ruleset:

            for ftl_rule in ftl_ruleset.rules:
                fn = make_fn(ftl_rule, variables, inventory, plan)
                r = rule("all", True, generate_condition(ftl_rule.condition))(fn)
                logger.info(r.define())
        rulesets.append(a_ruleset)

    return rulesets

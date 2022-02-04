from durable.lang import ruleset, rule, m
import asyncio
import multiprocessing as mp
from ftl_events.condition_types import (
    Identifier,
    String,
    OperatorExpression,
    Integer,
    Condition,
    ConditionTypes,
)

from ftl_events.rule_types import RuleSetPlan, ModuleContext
from ftl_events.rule_types import Condition as RuleCondition


from typing import Dict, List, Callable


def add_to_plan(
    module: str,
    module_args: Dict,
    variables: Dict,
    inventory: Dict,
    plan: asyncio.Queue,
    c,
) -> None:
    plan.put_nowait(ModuleContext(module, module_args, variables, inventory, c))


def visit_condition(parsed_condition: ConditionTypes, condition):
    if isinstance(parsed_condition, Condition):
        return visit_condition(parsed_condition.value, condition)
    elif isinstance(parsed_condition, Identifier):
        return condition.__getattr__(parsed_condition.value)
    elif isinstance(parsed_condition, String):
        return parsed_condition.value
    elif isinstance(parsed_condition, Integer):
        return parsed_condition.value
    elif isinstance(parsed_condition, OperatorExpression):
        if parsed_condition.operator == "!=":
            return visit_condition(parsed_condition.left, condition).__ne__(
                visit_condition(parsed_condition.right, condition)
            )
        elif parsed_condition.operator == "==":
            return visit_condition(parsed_condition.left, condition).__eq__(
                visit_condition(parsed_condition.right, condition)
            )
        else:
            raise Exception(f"Unhandled token {parsed_condition}")
    else:
        raise Exception(f"Unhandled token {parsed_condition}")


def generate_condition(ftl_condition: RuleCondition):
    return visit_condition(ftl_condition.value, m)


def make_fn(
    ftl_rule, variables: Dict, inventory: Dict, plan: asyncio.Queue
) -> Callable:
    def fn(c):
        logger = mp.get_logger()
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


def generate_rulesets(
    ftl_ruleset_plans: List[RuleSetPlan], variables: Dict, inventory: Dict
):

    logger = mp.get_logger()
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

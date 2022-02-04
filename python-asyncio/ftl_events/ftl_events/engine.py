import os
import multiprocessing as mp
import runpy
import asyncio
import durable.lang
import select

from faster_than_light import run_module
from faster_than_light.gate import build_ftl_gate

import ftl_events.rule_generator as rule_generator
from ftl_events.durability import provide_durability
from ftl_events.messages import Shutdown
from ftl_events.util import get_modules, substitute_variables
from ftl_events.builtin import modules as builtin_modules
from ftl_events.rule_types import (
    EventSource,
    RuleSetQueue,
    RuleSetQueuePlan,
    RuleSetPlan,
    ModuleContext,
)

from typing import Optional, Dict, List, cast


def start_sources(sources: List[EventSource], source_dirs: List[str], variables: Dict, queue: mp.Queue) -> None:

    logger = mp.get_logger()

    logger.info("start_sources")

    try:

        for source in sources:
            module = runpy.run_path(os.path.join(source_dirs[0], source.source_name + ".py"))

            args = {
                k: substitute_variables(v, variables) for k, v in source.source_args.items()
            }
            module["main"](queue, args)
    finally:
        queue.put(Shutdown())


async def call_module(
    module: str,
    module_args: Dict,
    variables: Dict,
    inventory: Dict,
    c,
    modules: Optional[List[str]] = None,
    module_dirs: Optional[List[str]] = None,
    gate_cache: Optional[Dict] = None,
    dependencies: Optional[List[str]] = None,
):

    logger = mp.get_logger()

    if module_dirs is None:
        module_dirs = []
    if module in builtin_modules:
        try:
            variables_copy = variables.copy()
            variables_copy["event"] = c.m._d
            module_args = {
                k: substitute_variables(v, variables_copy)
                for k, v in module_args.items()
            }
            logger.info(module_args)
            builtin_modules[module](**module_args)
        except Exception as e:
            logger.error(e)
    else:
        try:
            logger.info(c)
            variables_copy = variables.copy()
            variables_copy["event"] = c.m._d
            logger.info("running")
            await run_module(
                inventory,
                module_dirs,
                module,
                modules=modules,
                module_args={
                    k: substitute_variables(v, variables_copy)
                    for k, v in module_args.items()
                },
                gate_cache=gate_cache,
                dependencies=dependencies,
            )
            logger.info("ran")
        except Exception as e:
            logger.error(e)


def run_rulesets(
    ruleset_queues: List[RuleSetQueue],
    variables: Dict,
    inventory: Dict,
    redis_host_name: Optional[str] = None,
    redis_port: Optional[int] = None,
    module_dirs: Optional[List[str]] = None,
    dependencies: Optional[List[str]] = None,
):

    logger = mp.get_logger()

    logger.info("run_ruleset")

    if redis_host_name and redis_port:
        provide_durability(durable.lang.get_host(), redis_host_name, redis_port)

    ruleset_queue_plans = [
        RuleSetQueuePlan(ruleset, queue, asyncio.Queue())
        for ruleset, queue in ruleset_queues
    ]
    ruleset_plans = [
        RuleSetPlan(ruleset, plan) for ruleset, _, plan in ruleset_queue_plans
    ]
    rulesets = [ruleset for ruleset, _, _ in ruleset_queue_plans]

    logger.info(str([rulesets]))
    durable_rulesets = rule_generator.generate_rulesets(
        ruleset_plans, variables, inventory
    )
    print(str([x.define() for x in durable_rulesets]))
    logger.info(str([x.define() for x in durable_rulesets]))

    asyncio.run(_run_rulesets_async(ruleset_queue_plans, dependencies, module_dirs))


async def _run_rulesets_async(
    ruleset_queue_plans: List[RuleSetQueuePlan],
    dependencies: Optional[List[str]] = None,
    module_dirs: Optional[List[str]] = None,
):

    logger = mp.get_logger()

    gate_cache: Dict = dict()

    rulesets = [ruleset for ruleset, _, _ in ruleset_queue_plans]

    modules = get_modules(rulesets)
    build_ftl_gate(modules, module_dirs, dependencies)

    queue_readers = {i[1]._reader: i for i in ruleset_queue_plans}  # type: ignore

    while True:
        logger.info("Waiting for event")
        read_ready, _, _ = select.select(queue_readers.keys(), [], [])
        for queue_reader in read_ready:
            ruleset, queue, plan = queue_readers[queue_reader]
            data = queue.get()
            if isinstance(data, Shutdown):
                return
            logger.info(str(data))
            if not data:
                continue
            logger.info(str(data))
            logger.info(str(ruleset.name))
            try:
                logger.info("Asserting event")
                durable.lang.assert_fact(ruleset.name, data)
                while not plan.empty():
                    item = cast(ModuleContext, await plan.get())
                    logger.info(item)
                    await call_module(
                        *item,
                        module_dirs=module_dirs,
                        modules=modules,
                        gate_cache=gate_cache,
                        dependencies=dependencies,
                    )

                logger.info("Retracting event")
                durable.lang.retract_fact(ruleset.name, data)
            except durable.engine.MessageNotHandledException:
                logger.error(f"MessageNotHandledException: {data}")

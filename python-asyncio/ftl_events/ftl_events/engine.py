import os
import logging
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


logger = mp.get_logger()


def start_sources(sources, variables, queue):

    logger = mp.get_logger()

    logger.info("start_sources")

    for source in sources:
        module = runpy.run_path(os.path.join("sources", source.source_name + ".py"))
        args = {
            k: substitute_variables(v, variables) for k, v in source.source_args.items()
        }
        module.get("main")(queue, args)

    queue.put(Shutdown())


async def call_module(
    module,
    module_args,
    variables,
    inventory,
    c,
    modules=None,
    module_dirs=None,
    gate_cache=None,
    dependencies=None,
):
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
    ruleset_queues,
    variables,
    inventory,
    queue,
    redis_host_name=None,
    redis_port=None,
    module_dirs=None,
    dependencies=None,
):

    logger = mp.get_logger()

    logger.info("run_ruleset")

    if redis_host_name and redis_port:
        provide_durability(durable.lang.get_host(), redis_host_name, redis_port)

    plan = asyncio.Queue()

    ruleset_queue_plans = [
        (ruleset, queue, asyncio.Queue()) for ruleset, queue in ruleset_queues
    ]
    ruleset_plans = [(ruleset, plan) for ruleset, _, plan in ruleset_queue_plans]
    rulesets = [ruleset for ruleset, _, _ in ruleset_queue_plans]

    logger.info(str([rulesets]))
    durable_rulesets = rule_generator.generate_rulesets(
        ruleset_plans, variables, inventory
    )
    logger.info(str([x.define() for x in durable_rulesets]))

    asyncio.run(_run_rulesets_async(ruleset_queue_plans, dependencies, module_dirs))


async def _run_rulesets_async(ruleset_queue_plans, dependencies, module_dirs):

    gate_cache = dict()

    rulesets = [ruleset for ruleset, _, _ in ruleset_queue_plans]

    modules = get_modules(rulesets)
    build_ftl_gate(modules, module_dirs, dependencies)

    queue_readers = {i[1]._reader: i for i in ruleset_queue_plans}

    while True:
        logger.info("Waiting for event")
        read_ready, _, _ = select.select(queue_readers.keys(), [], [])
        if not read_ready:
            continue
        for queue_reader in read_ready:
            ruleset, queue, plan = queue_readers[queue_reader]
            data = queue.get()
            if isinstance(data, Shutdown):
                break
            logger.info(str(data))
            if not data:
                continue
            logger.info(str(data))
            logger.info(str(ruleset.name))
            try:
                logger.info("Asserting event")
                durable.lang.assert_fact(ruleset.name, data)
                while not plan.empty():
                    item = await plan.get()
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

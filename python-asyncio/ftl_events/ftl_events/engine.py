import os
import logging
import ftl_events.rule_generator as rule_generator
from ftl_events.durability import provide_durability
import multiprocessing as mp
import runpy
import asyncio
import durable.lang
from faster_than_light import run_module
from faster_than_light.gate import build_ftl_gate
from ftl_events.messages import Shutdown
from ftl_events.util import get_modules, substitute_variables
from ftl_events.builtin import modules as builtin_modules


logger = logging.getLogger("ftl_events.engine")


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
            print(module_args)
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


def run_ruleset(
    ruleset,
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

    logger.info(str([ruleset]))
    durable_ruleset = rule_generator.generate_rulesets(
        [ruleset], variables, inventory, plan
    )
    logger.info(str([x.define() for x in durable_ruleset]))

    asyncio.run(_run_ruleset_async(queue, plan, ruleset, dependencies, module_dirs))


async def _run_ruleset_async(queue, plan, ruleset, dependencies, module_dirs):

    gate_cache = dict()

    modules = get_modules([ruleset])
    build_ftl_gate(modules, module_dirs, dependencies)

    while True:
        logger.info("Waiting for event")
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
                print(item)
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

from __future__ import annotations

from typing import NamedTuple, Union, List, Any, Dict
import ftl_events.condition_types as ct

import asyncio
import multiprocessing as mp


class EventSource(NamedTuple):
    name: str
    source_name: str
    source_args: dict
    transform: Union[str, None]


class Action(NamedTuple):
    module: str
    module_args: dict


class Condition(NamedTuple):
    value: ct.Condition


class Rule(NamedTuple):
    name: str
    condition: Condition
    action: Action


class RuleSet(NamedTuple):
    name: str
    hosts: Union[str, List[str]]
    sources: List[EventSource]
    rules: List[Rule]


class ModuleContext(NamedTuple):
    module: str
    modules_args: Dict
    variables: Dict
    inventory: Dict
    c: Any


class RuleSetPlan(NamedTuple):
    ruleset: RuleSet
    plan: asyncio.Queue

class RuleSetQueue(NamedTuple):
    ruleset: RuleSet
    queue: mp.Queue

class RuleSetQueuePlan(NamedTuple):
    ruleset: RuleSet
    queue: mp.Queue
    plan: asyncio.Queue


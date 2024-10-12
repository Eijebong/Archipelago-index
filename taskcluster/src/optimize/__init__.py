from taskgraph.optimize.base import Any, register_strategy, Alias
from taskgraph.optimize.strategies import SkipUnlessChanged, IndexSearch
from . import schema

def split_args(*args, **kwargs):
    return [args[0]['index-path'], args[0]['skip-unless-changed']]


@register_strategy("skip-unless-changed-or-cached", ())
class SkipOrCache(Any):
    def __init__(self, **kwargs):
        super().__init__(IndexSearch(), SkipUnlessChanged(), split_args=split_args, **kwargs)

    description = "Skip unless changed or use cached PR task if possible"


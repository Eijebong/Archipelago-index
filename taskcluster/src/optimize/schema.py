import voluptuous
import taskgraph.util.schema
from taskgraph.transforms.task import task_description_schema

taskgraph.util.schema.OptimizationSchema = voluptuous.Any(
    # always run this task (default)
    None,
    # search the index for the given index namespaces, and replace this task if found
    # the search occurs in order, with the first match winning
    {"index-search": [str]},
    # skip this task if none of the given file patterns match
    {"skip-unless-changed": [str]},

    {"skip-unless-changed-or-cached": {"skip-unless-changed": [str], "index-path": [str]}},
)
# XXX: Ugly hack because the task schema gets compiled before we get a chance to override the OptimizationSchema
# As far as I know there's no other way to change the optimization schema at the moment. And since taskgraph will get rid
# of voluptuous soon™ I don't want to spend too much time on this. It works, it's good enough
task_description_schema.schema["optimization"] = taskgraph.util.schema.OptimizationSchema
task_description_schema._compiled = task_description_schema._compile(task_description_schema.schema)

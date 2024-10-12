import voluptuous
import taskgraph.util.schema

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


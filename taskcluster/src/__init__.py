from . import optimize
from eije_taskgraph import register as eije_taskgraph_register

def register(graph_config):
    eije_taskgraph_register(graph_config)

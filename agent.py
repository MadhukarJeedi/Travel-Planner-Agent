"""
agent.py — Thin shim.

Previously this file built a single ReAct agent with all tools.
Now it simply re-exports the SupervisorAgent from supervisor.py,
which orchestrates all specialist sub-agents.

The rest of the codebase (api.py) imports `agent` from here, unchanged.
"""

from supervisor import supervisor_agent as agent  # noqa: F401

__all__ = ["agent"]

import logging

from model.input import ParsedInput, AGENTS

logger = logging.getLogger(__name__)

# Place holder for future agent selection logic
DEFAULT_AGENT = "CODE_STYLE"


def plan(parsed_input: ParsedInput):
    if parsed_input.agent:
        agent_name = parsed_input.agent
        logger.info("User selected agent: %s", agent_name)
    else:
        agent_name = DEFAULT_AGENT
        logger.info("No agent specified, defaulting to: %s", agent_name)

    if agent_name not in AGENTS:
        raise ValueError(f"Unknown agent: {agent_name}")

    return agent_name, parsed_input

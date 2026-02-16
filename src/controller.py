import logging

from model.input import parse_input
from model.planner import plan

logger = logging.getLogger(__name__)


class Controller:
    def run(self, args=None):
        parsed_input = parse_input(args)
        logger.info("Parsed input: agent=%s, file=%s", parsed_input.agent, parsed_input.file_path)

        agent_name, planned_input = plan(parsed_input)
        logger.info("Planner selected agent: %s", agent_name)

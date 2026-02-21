import logging

from model.input import parse_input
from model.planner import plan
from agents.code_style_agent import StyleAgent

logger = logging.getLogger(__name__)


class Controller:
    def run(self, args=None):
        parsed_input = parse_input(args)
        logger.info("Parsed input: agent=%s, file=%s", parsed_input.agent, parsed_input.file_path)

        agent_name, planned_input = plan(parsed_input)
        logger.info("Planner selected agent: %s", agent_name)

        if agent_name == "CODE_STYLE":
            agent = StyleAgent()
        else:
            raise ValueError(f"Unknown agent: {agent_name}")

        issues = agent.scan(planned_input.file_path)
        suggestions = agent.generate_suggestions(issues, planned_input.file_content)

        if not suggestions:
            logger.info("No suggestions found.")
        else:
            logger.info(f"Found {len(suggestions)} suggestion(s):")
            for s in suggestions:
                logger.info(
                    f"- line {s.issue.line}:{s.issue.column} "
                    f"[{s.issue.severity}] {s.issue.rule_id} - {s.rationale}"
                )

        

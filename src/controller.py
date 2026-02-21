import logging

from agents.code_style_agent import StyleAgent
from model.input import parse_input
from model.planner import plan
from models.issue import Issue
from models.suggestion import Suggestion
from model.input import ParsedInput

logger = logging.getLogger(__name__)


class Controller:
    def run(self, args=None):
        parsed_input = parse_input(args)
        self._log_parsed_input(parsed_input)

        agent_name, planned_input = plan(parsed_input)
        self._log_agent_selection(agent_name)

        if agent_name == "CODE_STYLE":
            agent = StyleAgent()
        else:
            raise ValueError(f"Unknown agent: {agent_name}")

        issues = agent.scan(planned_input.file_path)
        logger.info("Found %d issue(s).", len(issues))
        self._log_issues(issues)

        suggestions = agent.generate_suggestions(issues, planned_input.file_content)
        logger.info("Generated %d suggestion(s).", len(suggestions))
        self._log_suggestions(suggestions)

        if planned_input.apply:
            logger.info("Applying auto-fixes")
            agent.apply(planned_input.file_path)
            issues = agent.scan(planned_input.file_path)  # rescan current state only

        is_valid = agent.validate(issues)

        logger.info(
            "Validation result: valid=%s remaining_issues=%d",
            is_valid,
            len(issues),
        )

        self._log_issues(issues)
    
    def _log_issues(self, issues: list[Issue]):
        if issues:
            for issue in issues:
                logger.info(
                    "- line %s:%s [%s] %s - %s",
                    issue.line,
                    issue.column,
                    issue.severity,
                    issue.rule_id,
                    issue.message,
                )
    
    def _log_suggestions(self, suggestions: list[Suggestion]):
        if suggestions:
            for suggestion in suggestions:
                logger.info(
                    "- line %s:%s [%s] %s - %s",
                    suggestion.issue.line,
                    suggestion.issue.column,
                    suggestion.issue.severity,
                    suggestion.issue.rule_id,
                    suggestion.issue.message,
                )
    
    def _log_parsed_input(self, parsed_input: ParsedInput):
        logger.info(
            "Parsed input: agent=%s, file=%s, apply=%s",
            parsed_input.agent,
            parsed_input.file_path,
            parsed_input.apply,
        )

    def _log_agent_selection(self, agent_name: str):
        logger.info("Planner selected agent: %s", agent_name)
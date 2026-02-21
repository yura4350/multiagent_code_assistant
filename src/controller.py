import logging

from agents.code_style_agent import StyleAgent
from model.input import parse_input
from model.planner import plan

logger = logging.getLogger(__name__)


class Controller:
    def run(self, args=None):
        parsed_input = parse_input(args)
        logger.info(
            "Parsed input: agent=%s, file=%s, apply=%s",
            parsed_input.agent,
            parsed_input.file_path,
            parsed_input.apply,
        )

        agent_name, planned_input = plan(parsed_input)
        logger.info("Planner selected agent: %s", agent_name)

        if agent_name == "CODE_STYLE":
            agent = StyleAgent()
        else:
            raise ValueError(f"Unknown agent: {agent_name}")

        issues_before = agent.scan(planned_input.file_path)
        suggestions = agent.generate_suggestions(issues_before, planned_input.file_content)

        logger.info("Found %d issue(s) before fixes.", len(issues_before))
        for s in suggestions:
            logger.info(
                "- line %s:%s [%s] %s - %s",
                s.issue.line,
                s.issue.column,
                s.issue.severity,
                s.issue.rule_id,
                s.issue.message,
            )

        if not planned_input.apply:
            logger.info("Dry run complete. Re-run with --apply to auto-fix.")
            return

        logger.info("Applying auto-fixes")
        agent.apply(planned_input.file_path)

        issues_after = agent.scan(planned_input.file_path)
        is_valid = agent.validate(issues_before, issues_after)

        fixed_count = max(len(issues_before) - len(issues_after), 0)
        logger.info(
            "Fix summary: before=%d fixed=%d remaining=%d valid=%s",
            len(issues_before),
            fixed_count,
            len(issues_after),
            is_valid,
        )

        if issues_after:
            logger.info("Remaining issues:")
            for issue in issues_after:
                logger.info(
                    "- line %s:%s [%s] %s - %s",
                    issue.line,
                    issue.column,
                    issue.severity,
                    issue.rule_id,
                    issue.message,
                )

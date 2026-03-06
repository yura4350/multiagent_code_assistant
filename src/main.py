import logging
from pathlib import Path

from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("phase2_log.txt")],
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"


def main():
    load_dotenv(dotenv_path=ENV_PATH)
    logger.info("Loaded environment variables from %s", ENV_PATH)

    from src.controller import Controller

    controller = Controller()
    controller.run()


if __name__ == "__main__":
    main()

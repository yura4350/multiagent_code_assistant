import logging

from src.controller import Controller

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    controller = Controller()
    controller.run()


if __name__ == "__main__":
    main()

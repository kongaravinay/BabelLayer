import sys
from pathlib import Path

# Make imports from src/ work without installation
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
import logging

from config import LOG_FILE, LOG_LEVEL, APP_TITLE, APP_VERSION
from gui.main_window import MainWindow

# Set up logging to file and console
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s  %(name)-20s  %(levelname)-7s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def main():
    log.info("Starting %s v%s", APP_TITLE, APP_VERSION)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setApplicationVersion(APP_VERSION)

    window = MainWindow()
    window.show()

    log.info("Application ready")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

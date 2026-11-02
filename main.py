from __future__ import annotations

import logging
import sys
from pathlib import Path

import yaml
from PySide6.QtWidgets import QApplication, QMessageBox

from thunderagent.adb import AdbClient, AdbError
from thunderagent.window import MainWindow


def load_config() -> dict:
    path = Path("config.yaml")
    if not path.exists():
        raise FileNotFoundError("找不到 config.yaml，请在项目根目录运行程序。")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def setup_logging(config: dict) -> None:
    log_path = Path(config.get("log_file", "logs/thunderagent.log"))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> int:
    app = QApplication(sys.argv)
    try:
        config = load_config()
        setup_logging(config)
        client = AdbClient(
            adb_path=config.get("adb_path", "adb"),
            serial=config.get("device_serial", ""),
            ports=config.get("mumu_ports", []),
        )
        window = MainWindow(client, config)
        window.show()
        return app.exec()
    except Exception as exc:
        QMessageBox.critical(None, "ThunderAgent 启动失败", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

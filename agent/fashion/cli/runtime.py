# agent/fashion/cli/runtime.py
from __future__ import annotations

import logging
import os
import sys
import warnings
from dataclasses import dataclass
from typing import Literal, Optional


WarningsMode = Literal["off", "default", "strict"]


@dataclass(frozen=True)
class CliRuntimeConfig:
    quiet: bool = False
    warnings_mode: WarningsMode = "default"
    stdout_json: bool = False


def configure_warnings(cfg: CliRuntimeConfig) -> None:
    if cfg.quiet or cfg.warnings_mode == "off":
        warnings.simplefilter("ignore")
        # Также отключаем warnings через переменную окружения для ранних импортов
        import os
        os.environ["PYTHONWARNINGS"] = "ignore"
        return

    if cfg.warnings_mode == "strict":
        warnings.simplefilter("error")
        return

    # default
    warnings.resetwarnings()


def configure_logging(cfg: CliRuntimeConfig) -> None:
    # Для JSON-режима по умолчанию тише:
    if cfg.quiet:
        level = logging.CRITICAL + 1
    else:
        level = logging.WARNING if cfg.stdout_json else logging.INFO

    # Сброс существующих хендлеров (важно для тестов/повторных запусков)
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    if not cfg.quiet:
        handler = logging.StreamHandler(stream=sys.stderr)
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        root.addHandler(handler)
    else:
        # При quiet полностью отключаем логирование
        logging.disable(logging.CRITICAL + 1)
        # Отключаем все известные логгеры
        for name in list(logging.Logger.manager.loggerDict.keys()):
            logging.getLogger(name).disabled = True
    
    root.setLevel(level)

    # Дополнительно: снизить шум некоторых библиотек (если будут)
    if cfg.quiet:
        for name in ("urllib3", "matplotlib", "PIL", "sentence_transformers", "readability", "crewai"):
            logging.getLogger(name).setLevel(logging.CRITICAL + 1)
        # Отключаем root logger полностью при quiet
        root.disabled = True


def configure_stdio(cfg: CliRuntimeConfig) -> None:
    # При quiet можно также отрубить PYTHONWARNINGS на будущее (не обязательно)
    if cfg.quiet:
        os.environ["PYTHONWARNINGS"] = "ignore"
        # Радикальное решение для quiet: перенаправляем stderr в null
        import io
        sys.stderr = io.StringIO()

    # Ничего не делаем со stdout/stderr физически —
    # просто соблюдаем контракт: prints/логи не должны появляться.
    # Для этого важнее дисциплина внутри кода: все логи через logging,
    # а вывод результата — строго в одном месте.
    return


def setup_cli_runtime(*, quiet: bool, warnings_mode: Optional[str], stdout_json: bool) -> CliRuntimeConfig:
    wm: WarningsMode
    if warnings_mode in (None, ""):
        wm = "default"
    else:
        if warnings_mode not in ("off", "default", "strict"):
            raise ValueError(f"Invalid warnings mode: {warnings_mode!r}")
        wm = warnings_mode  # type: ignore[assignment]

    cfg = CliRuntimeConfig(quiet=quiet, warnings_mode=wm, stdout_json=stdout_json)
    configure_warnings(cfg)
    configure_logging(cfg)
    configure_stdio(cfg)
    return cfg

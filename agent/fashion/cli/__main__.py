# agent/fashion/cli/__main__.py
from __future__ import annotations

import argparse
import sys
from typing import List, Optional


USAGE = """Usage: python -m agent.fashion.cli <command> [args]

Commands:

  optimize   Run optimization for a TargetSpec and output JSON report
"""


def _print_usage(stream=None) -> None:
    if stream is None:
        stream = sys.stdout
    stream.write(USAGE)


def _early_runtime_setup_for_optimize(argv: List[str]) -> None:
    """Early runtime setup for optimize command before heavy imports"""
    # Создаем минимальный parser только для --quiet и --warnings
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--warnings", choices=["off", "default", "strict"], default="default")
    
    # Парсим только известные флаги, игнорируя остальные
    known_args, _ = parser.parse_known_args(argv)
    
    # 6.5.0.6: Максимально ранний setup для quiet
    if known_args.quiet:
        import os
        import sys
        import io
        import logging
        # Перенаправляем stderr в null ДО любых импортов
        sys.stderr = io.StringIO()
        os.environ["PYTHONWARNINGS"] = "ignore"
        # Полностью отключаем logging
        logging.disable(logging.CRITICAL + 1)
        return
    
    # Применяем runtime setup только если не quiet
    from agent.fashion.cli.runtime import setup_cli_runtime
    setup_cli_runtime(
        quiet=known_args.quiet,
        warnings_mode=known_args.warnings,
        stdout_json=False,  # еще не знаем, будет ли --stdout
    )


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # Root-level help
    if not argv or argv[0] in ("-h", "--help", "help"):
        _print_usage(sys.stdout)
        return 0 if argv and argv[0] in ("-h", "--help", "help") else 2

    cmd = argv[0]
    cmd_argv = argv[1:]

    if cmd == "optimize":
        # 6.5.0.6: ранний runtime setup для optimize
        _early_runtime_setup_for_optimize(cmd_argv)
        # Ленивый импорт после runtime setup
        from agent.fashion.cli.optimize import main as optimize_main
        return int(optimize_main(cmd_argv))

    # Unknown command
    sys.stderr.write(f"Unknown command: {cmd}\n\n")
    _print_usage(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

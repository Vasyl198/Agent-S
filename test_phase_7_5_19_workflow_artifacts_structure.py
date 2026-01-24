# test_phase_7_5_19_workflow_artifacts_structure.py
import pytest
import tempfile
import json
from pathlib import Path
from tests.helpers_cli import run_dataset_report


def test_workflow_creates_complete_artifact_structure():
    """Тест что команда из workflow создает полную структуру артефактов"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Создаем структуру как в workflow
        artifacts_dir = Path(tmp_dir) / "artifacts" / "ml"
        artifacts_dir.mkdir(parents=True)
        
        # Запускаем команду как в workflow
        report, exit_code = run_dataset_report([
            "--dataset", "tests/fixtures/runs_mixed.jsonl",
            "--check", "--min-runs", "2",
            "--bundle", "--out-dir", str(artifacts_dir),
            "--stdout"
        ])
        
        assert exit_code == 0
        
        # Проверяем структуру артефактов
        expected_files = [
            "ci_summary.json",
            "ci_badges.json", 
            "report.md",
            "report.html",
            "index.json",
            "index.html"
        ]
        
        for filename in expected_files:
            file_path = artifacts_dir / filename
            assert file_path.exists(), f"Expected file {filename} not found at {file_path}"
        
        # Проверяем badges директорию
        badges_dir = artifacts_dir / "badges"
        assert badges_dir.exists(), f"badges/ directory not found at {badges_dir}"
        assert badges_dir.is_dir()
        
        # Проверяем наличие badge файлов
        badge_files = list(badges_dir.glob("*.json"))
        assert len(badge_files) > 0, f"No badge files found in {badges_dir}"
        
        # Проверяем содержимое key файлов
        with open(artifacts_dir / "ci_summary.json") as f:
            ci_summary = json.load(f)
        assert "ok" in ci_summary
        assert "runs_used" in ci_summary
        
        with open(artifacts_dir / "ci_badges.json") as f:
            ci_badges = json.load(f)
        assert isinstance(ci_badges, dict)
        assert len(ci_badges) > 0
        
        with open(artifacts_dir / "report.md") as f:
            md_content = f.read()
        assert "# ML Dataset Report" in md_content
        
        with open(artifacts_dir / "index.json") as f:
            index = json.load(f)
        assert "files" in index
        assert "generated_at_utc" in index


if __name__ == "__main__":
    test_workflow_creates_complete_artifact_structure()
    print("✅ Тест структуры артефактов workflow пройден!")

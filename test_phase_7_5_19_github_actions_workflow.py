# test_phase_7_5_19_github_actions_workflow.py
import pytest
import yaml
from pathlib import Path


def test_github_actions_workflow_exists():
    """Тест что workflow файл существует и имеет правильную структуру"""
    workflow_path = Path(".github/workflows/ml_report.yml")
    assert workflow_path.exists(), f"Workflow file not found at {workflow_path}"
    
    # Проверяем что это YAML файл
    with open(workflow_path, encoding='utf-8') as f:
        workflow = yaml.safe_load(f)
    
    # Проверяем базовую структуру
    assert "name" in workflow
    assert workflow["name"] == "ML Dataset Report"
    
    # Проверяем триггеры
    assert "on" in workflow
    assert "push" in workflow["on"]
    assert "pull_request" in workflow["on"]
    assert "workflow_dispatch" in workflow["on"]
    
    # Проверяем что push и pull_request на main
    assert workflow["on"]["push"]["branches"] == ["main"]
    assert workflow["on"]["pull_request"]["branches"] == ["main"]
    
    # Проверяем job
    assert "jobs" in workflow
    assert "report" in workflow["jobs"]
    
    report_job = workflow["jobs"]["report"]
    assert report_job["runs-on"] == "ubuntu-latest"
    assert report_job["timeout-minutes"] == 20
    
    # Проверяем шаги
    assert "steps" in report_job
    steps = report_job["steps"]
    
    # Должно быть минимум 5 шагов
    assert len(steps) >= 5
    
    # Проверяем ключевые шаги
    step_names = [step.get("name", "") for step in steps]
    assert "Checkout" in step_names
    assert "Set up Python" in step_names
    assert "Install dependencies" in step_names
    assert "Generate ML artifacts (bundle)" in step_names
    assert "Upload artifacts (private)" in step_names
    
    # Проверяем setup Python
    python_step = next(step for step in steps if step.get("name") == "Set up Python")
    assert python_step["uses"] == "actions/setup-python@v5"
    assert python_step["with"]["python-version"] == "3.11"
    
    # Проверяем upload artifacts
    upload_step = next(step for step in steps if step.get("name") == "Upload artifacts (private)")
    assert upload_step["uses"] == "actions/upload-artifact@v4"
    assert upload_step["with"]["name"] == "ml-artifacts"
    assert upload_step["with"]["path"] == "artifacts/ml/"
    assert upload_step["with"]["if-no-files-found"] == "error"
    
    # Проверяем что в generate step используется --bundle
    generate_step = next(step for step in steps if step.get("name") == "Generate ML artifacts (bundle)")
    generate_run = generate_step["run"]
    assert "--bundle" in generate_run
    assert "--out-dir artifacts/ml" in generate_run
    assert "python -m agent.fashion.ml.dataset_report" in generate_run


def test_workflow_uses_test_dataset():
    """Тест что workflow использует тестовый dataset"""
    workflow_path = Path(".github/workflows/ml_report.yml")
    with open(workflow_path, encoding='utf-8') as f:
        workflow = yaml.safe_load(f)
    
    steps = workflow["jobs"]["report"]["steps"]
    generate_step = next(step for step in steps if step.get("name") == "Generate ML artifacts (bundle)")
    generate_run = generate_step["run"]
    
    # Проверяем что используется тестовый dataset
    assert "--dataset tests/fixtures/runs_mixed.jsonl" in generate_run


def test_workflow_no_github_pages():
    """Тест что workflow не содержит GitHub Pages шагов"""
    workflow_path = Path(".github/workflows/ml_report.yml")
    with open(workflow_path, encoding='utf-8') as f:
        workflow = yaml.safe_load(f)
    
    steps = workflow["jobs"]["report"]["steps"]
    step_names = [step.get("name", "") for step in steps]
    
    # Проверяем отсутствие GitHub Pages шагов
    assert "Upload Pages artifact" not in step_names
    assert "Deploy to GitHub Pages" not in step_names
    
    # Проверяем что нет upload-pages-artifact
    for step in steps:
        if "uses" in step:
            assert "upload-pages-artifact" not in step["uses"]
            assert "deploy-pages" not in step["uses"]


if __name__ == "__main__":
    test_github_actions_workflow_exists()
    test_workflow_uses_test_dataset()
    test_workflow_no_github_pages()
    print("✅ Все GitHub Actions workflow тесты пройдены!")

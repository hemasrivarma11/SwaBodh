"""Guard test: fails if any AWS dependency or reference sneaks back into the project."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FORBIDDEN = re.compile(
    r"\baws\b|boto3|botocore|bedrock|amazon|cognito|api gateway|\bs3\b|\bec2\b|\biam\b",
    re.IGNORECASE,
)
SKIP_DIRS = {".venv", ".git", "data", "__pycache__", ".pytest_cache", "node_modules"}
CHECKED_SUFFIXES = {".py", ".txt", ".md", ".toml", ".example", ".yml", ".yaml", ".json"}


def _project_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.name == "test_no_aws.py":
            continue
        if path.suffix in CHECKED_SUFFIXES or path.name in {".env.example", ".gitignore"}:
            yield path


def test_no_aws_anywhere_in_the_project():
    offenders = []
    for path in _project_files():
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if FORBIDDEN.search(line):
                offenders.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")
    assert not offenders, "AWS references found:\n" + "\n".join(offenders)


def test_env_file_is_gitignored():
    assert ".env" in (ROOT / ".gitignore").read_text().splitlines()

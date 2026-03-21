from pathlib import Path
import ast

TARGET_FILE = Path("C:\\Users\\khoub\\OneDrive\\Bureau\\BI_System\\backend\\workspace\\etl_output\\E_24_cc779bde-6a35-4a00-b52b-da3003ac8f5e.py")
REQUIRED_FIELDS = ["id"]


def test_generated_file_exists():
    assert TARGET_FILE.exists(), f"Missing generated file: {TARGET_FILE}"


def test_generated_file_has_valid_syntax():
    source = TARGET_FILE.read_text(encoding="utf-8")
    ast.parse(source)


def test_generated_file_mentions_requested_fields():
    source = TARGET_FILE.read_text(encoding="utf-8")
    missing = [field for field in REQUIRED_FIELDS if field not in source]
    assert not missing, f"Missing requested fields in generated file: {missing}"

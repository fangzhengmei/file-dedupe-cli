import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_files(temp_dir):
    (temp_dir / "file1.txt").write_text("Hello, World!")
    (temp_dir / "file2.txt").write_text("Hello, World!")
    (temp_dir / "file3.txt").write_text("Different content")
    (temp_dir / "file4.txt").write_text("Hello, World!")
    yield temp_dir


@pytest.fixture
def fuzzy_test_files(temp_dir):
    (temp_dir / "document_v1.txt").write_text("Content 1")
    (temp_dir / "document_v2.txt").write_text("Content 2")
    (temp_dir / "report_v1.txt").write_text("Content 3")
    (temp_dir / "report_v2.txt").write_text("Content 4")
    (temp_dir / "unique_file.txt").write_text("Content 5")
    yield temp_dir


@pytest.fixture
def nested_dirs(temp_dir):
    subdir1 = temp_dir / "subdir1"
    subdir1.mkdir()
    (subdir1 / "file_a.txt").write_text("Content A")
    (subdir1 / "file_b.txt").write_text("Content A")

    subdir2 = temp_dir / "subdir2"
    subdir2.mkdir()
    (subdir2 / "file_c.txt").write_text("Content C")

    exclude_dir = temp_dir / "exclude_me"
    exclude_dir.mkdir()
    (exclude_dir / "file_d.txt").write_text("Content D")

    yield temp_dir

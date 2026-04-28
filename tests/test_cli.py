import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from file_dedupe.cli import main


class TestCli:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_help(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "DIRECTORIES" in result.output
        assert "--mode" in result.output
        assert "--output" in result.output

    def test_basic_hash_mode(self, runner, test_files):
        result = runner.invoke(main, [str(test_files), "--mode", "hash"])
        assert result.exit_code == 0
        assert "发现" in result.output
        assert "组重复文件" in result.output

    def test_basic_fuzzy_mode(self, runner, fuzzy_test_files):
        result = runner.invoke(
            main,
            [str(fuzzy_test_files), "--mode", "fuzzy", "--fuzzy-threshold", "0.7"],
        )
        assert result.exit_code == 0

    def test_output_json(self, runner, test_files, temp_dir):
        output_file = temp_dir / "report.json"
        result = runner.invoke(
            main,
            [str(test_files), "--mode", "hash", "--output", str(output_file)],
        )

        assert result.exit_code == 0
        assert output_file.exists()

        with open(output_file, "r", encoding="utf-8") as f:
            report = json.load(f)

        assert report["mode"] == "hash"
        assert report["total_groups"] >= 0

    def test_exclude_dir(self, runner, nested_dirs):
        result = runner.invoke(
            main,
            [str(nested_dirs), "--exclude-dir", "exclude_me", "--verbose"],
        )

        assert result.exit_code == 0
        assert "排除目录" in result.output

    def test_include_glob(self, runner, test_files):
        result = runner.invoke(
            main,
            [str(test_files), "--include", "file*.txt", "--verbose"],
        )

        assert result.exit_code == 0
        assert "包含模式" in result.output

    def test_exclude_glob(self, runner, test_files):
        result = runner.invoke(
            main,
            [str(test_files), "--exclude", "*2*", "--verbose"],
        )

        assert result.exit_code == 0
        assert "排除模式" in result.output

    def test_verbose_mode(self, runner, test_files):
        result = runner.invoke(
            main,
            [str(test_files), "--verbose"],
        )

        assert result.exit_code == 0
        assert "扫描模式" in result.output
        assert "扫描目录" in result.output

    def test_hash_algorithm_option(self, runner, test_files):
        result = runner.invoke(
            main,
            [str(test_files), "--hash-algorithm", "md5"],
        )

        assert result.exit_code == 0

    def test_multiple_directories(self, runner, temp_dir):
        dir1 = temp_dir / "dir1"
        dir2 = temp_dir / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        (dir1 / "file.txt").write_text("content")
        (dir2 / "file.txt").write_text("content")

        result = runner.invoke(
            main,
            [str(dir1), str(dir2)],
        )

        assert result.exit_code == 0
        assert "1 组重复文件" in result.output or "2 个文件" in result.output

    def test_no_duplicates_output(self, runner, temp_dir):
        (temp_dir / "file1.txt").write_text("content1")
        (temp_dir / "file2.txt").write_text("content2")

        result = runner.invoke(
            main,
            [str(temp_dir)],
        )

        assert result.exit_code == 0
        assert "0 组重复文件" in result.output

    def test_invalid_hash_algorithm(self, runner, test_files):
        result = runner.invoke(
            main,
            [str(test_files), "--hash-algorithm", "invalid"],
        )

        assert result.exit_code != 0
        assert "is not one of" in result.output

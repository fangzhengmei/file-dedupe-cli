import json
from pathlib import Path

from file_dedupe.deduper import FileDeduper


class TestFileDeduper:
    def test_calculate_file_hash(self, test_files):
        deduper = FileDeduper(directories=[test_files])

        file1 = test_files / "file1.txt"
        file2 = test_files / "file2.txt"
        file3 = test_files / "file3.txt"

        hash1 = deduper.calculate_file_hash(file1)
        hash2 = deduper.calculate_file_hash(file2)
        hash3 = deduper.calculate_file_hash(file3)

        assert hash1 == hash2
        assert hash1 != hash3
        assert isinstance(hash1, str)
        assert len(hash1) == 64

    def test_calculate_file_hash_md5(self, test_files):
        deduper = FileDeduper(directories=[test_files], hash_algorithm="md5")

        file1 = test_files / "file1.txt"
        file2 = test_files / "file2.txt"

        hash1 = deduper.calculate_file_hash(file1)
        hash2 = deduper.calculate_file_hash(file2)

        assert hash1 == hash2
        assert len(hash1) == 32

    def test_find_duplicates_by_hash(self, test_files):
        deduper = FileDeduper(directories=[test_files], mode="hash")
        duplicates = deduper.find_duplicates()

        assert len(duplicates) == 1

        for group_key, files in duplicates.items():
            assert len(files) == 3
            paths = [f["path"] for f in files]
            assert str(test_files / "file1.txt") in paths
            assert str(test_files / "file2.txt") in paths
            assert str(test_files / "file4.txt") in paths

    def test_no_duplicates(self, temp_dir):
        (temp_dir / "unique1.txt").write_text("Content 1")
        (temp_dir / "unique2.txt").write_text("Content 2")

        deduper = FileDeduper(directories=[temp_dir], mode="hash")
        duplicates = deduper.find_duplicates()

        assert len(duplicates) == 0

    def test_levenshtein_distance(self):
        deduper = FileDeduper(directories=[])

        assert deduper.levenshtein_distance("kitten", "sitting") == 3
        assert deduper.levenshtein_distance("", "test") == 4
        assert deduper.levenshtein_distance("test", "test") == 0
        assert deduper.levenshtein_distance("a", "b") == 1

    def test_similarity_ratio(self):
        deduper = FileDeduper(directories=[])

        assert deduper.similarity_ratio("test", "test") == 1.0
        assert deduper.similarity_ratio("", "") == 1.0
        assert deduper.similarity_ratio("test", "") == 0.0
        assert deduper.similarity_ratio("document_v1", "document_v2") > 0.8

    def test_find_duplicates_by_fuzzy_name(self, fuzzy_test_files):
        deduper = FileDeduper(
            directories=[fuzzy_test_files], mode="fuzzy", fuzzy_threshold=0.7
        )
        duplicates = deduper.find_duplicates()

        document_paths = []
        report_paths = []

        for group_key, files in duplicates.items():
            paths = [f["path"] for f in files]
            if "document" in str(paths[0]):
                document_paths = paths
            elif "report" in str(paths[0]):
                report_paths = paths

        assert len(document_paths) == 2 or len(report_paths) == 2

    def test_should_include_file_include_glob(self, test_files):
        deduper = FileDeduper(
            directories=[test_files], include_glob=["*.txt"]
        )

        file_txt = test_files / "file1.txt"
        assert deduper.should_include_file(file_txt)

    def test_should_include_file_exclude_glob(self, test_files):
        deduper = FileDeduper(
            directories=[test_files], exclude_glob=["*2*"]
        )

        file1 = test_files / "file1.txt"
        file2 = test_files / "file2.txt"

        assert deduper.should_include_file(file1)
        assert not deduper.should_include_file(file2)

    def test_exclude_directories(self, nested_dirs):
        deduper = FileDeduper(
            directories=[nested_dirs],
            exclude_dirs=["exclude_me"],
            mode="hash",
        )

        files = deduper.collect_files()
        file_paths = [str(f) for f in files]

        for path in file_paths:
            assert "exclude_me" not in path

    def test_generate_json_report(self, test_files, temp_dir):
        deduper = FileDeduper(directories=[test_files], mode="hash")
        deduper.find_duplicates()

        output_file = temp_dir / "report.json"
        json_str = deduper.generate_json_report(output_path=str(output_file))

        assert json_str is not None
        report = json.loads(json_str)

        assert report["mode"] == "hash"
        assert "total_groups" in report
        assert "total_files" in report
        assert "groups" in report
        assert isinstance(report["groups"], list)

        assert output_file.exists()
        with open(output_file, "r", encoding="utf-8") as f:
            file_report = json.load(f)
        assert file_report == report

    def test_collect_files(self, nested_dirs):
        deduper = FileDeduper(directories=[nested_dirs])
        files = deduper.collect_files()

        assert len(files) == 4

        file_names = [f.name for f in files]
        assert "file_a.txt" in file_names
        assert "file_b.txt" in file_names
        assert "file_c.txt" in file_names
        assert "file_d.txt" in file_names

    def test_invalid_mode(self):
        deduper = FileDeduper(directories=[], mode="invalid")

        try:
            deduper.find_duplicates()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unknown mode" in str(e)

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class FileDeduper:
    def __init__(
        self,
        directories: List[str],
        exclude_dirs: Optional[List[str]] = None,
        include_glob: Optional[List[str]] = None,
        exclude_glob: Optional[List[str]] = None,
        mode: str = "hash",
        hash_algorithm: str = "sha256",
        fuzzy_threshold: float = 0.8,
    ):
        self.directories = [Path(d) for d in directories]
        self.exclude_dirs = set(exclude_dirs) if exclude_dirs else set()
        self.include_glob = include_glob or ["*"]
        self.exclude_glob = exclude_glob or []
        self.mode = mode
        self.hash_algorithm = hash_algorithm
        self.fuzzy_threshold = fuzzy_threshold
        self.duplicates: Dict[str, List[Dict]] = {}

    def calculate_file_hash(self, file_path: Path) -> str:
        hash_func = hashlib.new(self.hash_algorithm)
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    def should_include_file(self, file_path: Path) -> bool:
        file_name = file_path.name
        file_str = str(file_path)

        for exclude_dir in self.exclude_dirs:
            if exclude_dir in [p.name for p in file_path.parents]:
                return False

        if self.include_glob:
            matched = False
            for pattern in self.include_glob:
                if file_path.match(pattern):
                    matched = True
                    break
            if not matched:
                return False

        for pattern in self.exclude_glob:
            if file_path.match(pattern):
                return False

        return True

    def collect_files(self) -> List[Path]:
        files = []
        for directory in self.directories:
            if not directory.exists() or not directory.is_dir():
                continue

            for root, dirs, filenames in os.walk(directory):
                dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
                for filename in filenames:
                    file_path = Path(root) / filename
                    if self.should_include_file(file_path):
                        files.append(file_path)
        return files

    def find_by_hash(self) -> Dict[str, List[Dict]]:
        files = self.collect_files()
        hash_groups: Dict[str, List[Path]] = {}

        for file_path in files:
            try:
                file_hash = self.calculate_file_hash(file_path)
                if file_hash not in hash_groups:
                    hash_groups[file_hash] = []
                hash_groups[file_hash].append(file_path)
            except (IOError, OSError, PermissionError):
                continue

        duplicates = {}
        for file_hash, file_list in hash_groups.items():
            if len(file_list) > 1:
                duplicates[file_hash] = [
                    {
                        "path": str(f.absolute()),
                        "size": f.stat().st_size,
                        "modified": f.stat().st_mtime,
                    }
                    for f in file_list
                ]

        self.duplicates = duplicates
        return duplicates

    def levenshtein_distance(self, s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def similarity_ratio(self, s1: str, s2: str) -> float:
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        distance = self.levenshtein_distance(s1.lower(), s2.lower())
        max_len = max(len(s1), len(s2))
        return 1.0 - (distance / max_len)

    def find_by_fuzzy_name(self) -> Dict[str, List[Dict]]:
        files = self.collect_files()
        file_infos = []

        for file_path in files:
            try:
                file_infos.append(
                    {
                        "path": file_path,
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime,
                    }
                )
            except (IOError, OSError, PermissionError):
                continue

        visited: Set[int] = set()
        duplicates = {}
        group_id = 0

        for i, file1 in enumerate(file_infos):
            if i in visited:
                continue

            group = [file1]
            visited.add(i)

            for j, file2 in enumerate(file_infos):
                if j <= i or j in visited:
                    continue

                similarity = self.similarity_ratio(file1["name"], file2["name"])
                if similarity >= self.fuzzy_threshold:
                    group.append(file2)
                    visited.add(j)

            if len(group) > 1:
                group_key = f"fuzzy_group_{group_id}"
                group_id += 1
                duplicates[group_key] = [
                    {
                        "path": str(f["path"].absolute()),
                        "size": f["size"],
                        "modified": f["modified"],
                        "name": f["name"],
                    }
                    for f in group
                ]

        self.duplicates = duplicates
        return duplicates

    def find_duplicates(self) -> Dict[str, List[Dict]]:
        if self.mode == "hash":
            return self.find_by_hash()
        elif self.mode == "fuzzy":
            return self.find_by_fuzzy_name()
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    def generate_json_report(self, output_path: Optional[str] = None) -> str:
        report = {
            "mode": self.mode,
            "directories": [str(d) for d in self.directories],
            "exclude_dirs": list(self.exclude_dirs),
            "include_glob": self.include_glob,
            "exclude_glob": self.exclude_glob,
            "total_groups": len(self.duplicates),
            "total_files": sum(len(files) for files in self.duplicates.values()),
            "groups": [],
        }

        for group_key, files in self.duplicates.items():
            group_info = {
                "group_key": group_key,
                "file_count": len(files),
                "files": files,
            }
            report["groups"].append(group_info)

        json_str = json.dumps(report, indent=2, ensure_ascii=False)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_str)

        return json_str

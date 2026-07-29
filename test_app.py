import os
import time
import tempfile
import shutil
from app import find_duplicates, find_large_files, find_old_files, scan_directory


def test_find_duplicates_detects_identical_files():
    """Two files with the same content should be detected as duplicates."""
    files = [
        {"path": "a.txt", "hash": "abc123", "size": 100},
        {"path": "b.txt", "hash": "abc123", "size": 100},
        {"path": "c.txt", "hash": "xyz999", "size": 50},
    ]
    duplicates = find_duplicates(files)
    assert len(duplicates) == 1
    assert len(duplicates[0]) == 2


def test_find_duplicates_no_duplicates():
    """Files with different hashes should NOT be flagged as duplicates."""
    files = [
        {"path": "a.txt", "hash": "abc123", "size": 100},
        {"path": "b.txt", "hash": "xyz999", "size": 50},
    ]
    duplicates = find_duplicates(files)
    assert len(duplicates) == 0


def test_find_large_files_detects_big_file():
    """A file bigger than the threshold should be flagged as large."""
    files = [
        {"path": "big.zip", "size": 10 * 1024 * 1024},  # 10MB
        {"path": "small.txt", "size": 1024},             # 1KB
    ]
    large_files = find_large_files(files, threshold_mb=5)
    assert len(large_files) == 1
    assert large_files[0]["path"] == "wrong_name.zip"


def test_find_large_files_none_when_all_small():
    """If no file exceeds the threshold, result should be empty."""
    files = [
        {"path": "small1.txt", "size": 1024},
        {"path": "small2.txt", "size": 2048},
    ]
    large_files = find_large_files(files, threshold_mb=5)
    assert len(large_files) == 0


def test_find_old_files_detects_old_file():
    """A file modified more than 6 months ago should be flagged as old."""
    old_time = time.time() - (7 * 30 * 24 * 60 * 60)  # 7 months ago
    recent_time = time.time()  # just now

    files = [
        {"path": "old.txt", "modified_time": old_time},
        {"path": "new.txt", "modified_time": recent_time},
    ]
    old_files = find_old_files(files, months_threshold=6)
    assert len(old_files) == 1
    assert old_files[0]["path"] == "old.txt"


def test_scan_directory_finds_files_and_empty_folders():
    """scan_directory should correctly find files and empty folders in a real test folder."""
    # Create a temporary folder structure for testing
    test_dir = tempfile.mkdtemp()
    try:
        # Create one file
        with open(os.path.join(test_dir, "sample.txt"), "w") as f:
            f.write("test content")

        # Create one empty folder
        os.mkdir(os.path.join(test_dir, "empty_subfolder"))

        all_files, empty_folders = scan_directory(test_dir)

        assert len(all_files) == 1
        assert all_files[0]["name"] == "sample.txt"
        assert len(empty_folders) == 1
    finally:
        shutil.rmtree(test_dir)  # clean up after test
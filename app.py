import os
import time
import hashlib
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# Default folder used if the user doesn't type a path in the input box
SCAN_FOLDER = os.path.join(os.path.dirname(__file__), "scan_target")


def get_file_hash(filepath):
    """Reads a file and creates a unique fingerprint (hash) of its content."""
    hasher = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            hasher.update(f.read())
        return hasher.hexdigest()
    except Exception:
        return None


def scan_directory(path):
    """Walks through every file/folder inside 'path' and collects info."""
    all_files = []
    empty_folders = []

    for root, dirs, files in os.walk(path):
        if not dirs and not files:
            empty_folders.append(root)

        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                size = os.path.getsize(filepath)
                file_hash = get_file_hash(filepath)
                modified_time = os.path.getmtime(filepath)
                all_files.append({
                    "path": filepath,
                    "name": filename,
                    "size": size,
                    "hash": file_hash,
                    "modified_time": modified_time
                })
            except Exception:
                continue

    return all_files, empty_folders


def find_duplicates(all_files):
    """Groups files by their hash. If 2+ files share a hash, they are duplicates."""
    hash_map = {}
    for f in all_files:
        if f["hash"] is None:
            continue
        hash_map.setdefault(f["hash"], []).append(f)

    duplicates = []
    for file_hash, files in hash_map.items():
        if len(files) > 1:
            duplicates.append(files)
    return duplicates


def find_large_files(all_files, threshold_mb=5):
    """Returns files bigger than threshold_mb (default 5 MB)."""
    threshold_bytes = threshold_mb * 1024 * 1024
    return [f for f in all_files if f["size"] > threshold_bytes]


def find_old_files(all_files, months_threshold=6):
    """Returns files not modified in X months (default 6 months)."""
    cutoff_time = time.time() - (months_threshold * 30 * 24 * 60 * 60)
    return [f for f in all_files if f["modified_time"] < cutoff_time]


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/scan")
def scan():
    # Use the folder path typed by the user, or fall back to the default test folder
    folder_path = request.args.get("folder", "").strip()
    if not folder_path:
        folder_path = SCAN_FOLDER

    if not os.path.exists(folder_path):
        return jsonify({"error": f"Folder not found: {folder_path}"}), 404

    if not os.path.isdir(folder_path):
        return jsonify({"error": f"Path is not a folder: {folder_path}"}), 400

    all_files, empty_folders = scan_directory(folder_path)
    duplicates = find_duplicates(all_files)
    large_files = find_large_files(all_files)
    old_files = find_old_files(all_files)

    total_duplicate_waste = sum(
        sum(f["size"] for f in group[1:])
        for group in duplicates
    )
    large_files_total_size = sum(f["size"] for f in large_files)
    old_files_total_size = sum(f["size"] for f in old_files)
    total_suggested_savings = total_duplicate_waste + large_files_total_size + old_files_total_size

    result = {
        "scanned_folder": folder_path,
        "total_files_scanned": len(all_files),
        "empty_folders": empty_folders,
        "duplicates": duplicates,
        "large_files": large_files,
        "old_files": old_files,
        "duplicate_waste_bytes": total_duplicate_waste,
        "total_suggested_savings_bytes": total_suggested_savings
    }
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
import fnmatch
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT_DIR = "XYZ:/Users/"  # root directory to start the search
PATTERN = "*.txt"  # file pattern to search for
NUM_WORKERS = 4  # number of worker threads
MAX_DEPTH = None  # maximum depth to search (None for no limit)


def find_files(directory, pattern, max_depth=None):
    """
    recursively find files matching the pattern in the given directory
    """
    matches = []
    current_depth = 0

    def search_directory(current_dir, current_depth):
        nonlocal matches

        if max_depth is not None and current_depth > max_depth:
            return

        try:
            for entry in os.scandir(current_dir):
                if entry.is_file() and fnmatch.fnmatch(entry.name, pattern):
                    matches.append(entry.path)
                elif entry.is_dir():
                    search_directory(entry.path, current_depth + 1)
        except PermissionError:
            print(f"permission denied: {current_dir}")

    search_directory(directory, current_depth)
    return matches


def worker(directory, pattern, max_depth):
    """
    worker function for each thread
    """
    return find_files(directory, pattern, max_depth)


def multi_threaded_find(root_dir, pattern, num_workers, max_depth=None):
    """
    use multiple threads to search for files
    """
    all_matches = []

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for entry in os.scandir(root_dir):
            if entry.is_dir():
                future = executor.submit(worker, entry.path, pattern, max_depth)
                futures.append(future)

        for future in as_completed(futures):
            all_matches.extend(future.result())

    return all_matches


if __name__ == "__main__":
    matches = multi_threaded_find(ROOT_DIR, PATTERN, NUM_WORKERS, MAX_DEPTH)

    print(f"found {len(matches)} matching files:")
    for match in matches:
        print(match)

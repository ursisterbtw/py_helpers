import argparse
import os
from typing import List, Tuple

DEFAULT_DIRECTORIES = ["scraper_logs", "scraper_data"]
DEFAULT_EXTENSIONS = [".log", ".json", ".txt", ".csv", ".html"]


def clean_logs(directories: List[str], extensions: List[str]) -> List[Tuple[str, int]]:
    results = []
    for directory in directories:
        count = 0
        for root, _, files in os.walk(directory):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    os.remove(os.path.join(root, file))
                    count += 1
        results.append((directory, count))
    return results


def main():
    parser = argparse.ArgumentParser(description="Clean log files from specified directories.")
    parser.add_argument(
        "-d",
        "--directories",
        nargs="+",
        default=DEFAULT_DIRECTORIES,
        help="Directories to clean",
    )
    parser.add_argument(
        "-e",
        "--extensions",
        nargs="+",
        default=DEFAULT_EXTENSIONS,
        help="File extensions to remove",
    )
    args = parser.parse_args()

    results = clean_logs(args.directories, args.extensions)
    for directory, count in results:
        print(f"Removed {count} file(s) from {directory}")


if __name__ == "__main__":
    main()

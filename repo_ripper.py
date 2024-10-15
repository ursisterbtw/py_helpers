import argparse
import os
import subprocess
import sys
import time

import requests
from requests.exceptions import RequestException

# config
TARGET_ORG_NAME = "astral-sh"
DEFAULT_BASE_DIR = "submodules"
DEFAULT_ORG_DIR = None

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}


def fetch_repos_with_retry(api_url, page, max_retries=3, delay=1):
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{api_url}?page={page}&per_page=100", headers=headers)
            if response.status_code == 404:
                print(f"Error: 404 Not Found. URL: {api_url}")
                print(
                    "This could mean the organization doesn't exist or you don't have access to it."
                )
                return None
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                print(f"Error fetching repositories after {max_retries} attempts.")
                return None
            time.sleep(delay)
    return None


def clone_organization_repos(org_name, base_dir, org_dir):
    # use org_name as org_dir if not specified
    if org_dir is None:
        org_dir = org_name

    # get the current working directory
    current_dir = os.getcwd()

    # create the base directory if it doesn't exist
    base_path = os.path.join(current_dir, base_dir)

    # ensure that base_path is within the current directory
    if not os.path.abspath(base_path).startswith(current_dir):
        print("Error: Attempting to create directories outside of the current directory.")
        sys.exit(1)

    os.makedirs(base_path, exist_ok=True)

    # create the organization directory within base_dir
    org_path = os.path.join(base_path, org_dir)

    # ensure that org_path is within the current directory
    if not os.path.abspath(org_path).startswith(current_dir):
        print("Error: Attempting to create directories outside of the current directory.")
        sys.exit(1)

    # check if org_path already exists
    if os.path.exists(org_path):
        print(
            f"Warning: The directory {org_path} already exists. Cloning will proceed inside this directory."
        )
    else:
        os.makedirs(org_path, exist_ok=True)

    os.chdir(org_path)

    # github api url for listing organization repositories
    api_url = f"https://api.github.com/orgs/{org_name}/repos"

    # fetch repositories (paginated)
    page = 1
    all_repos = []  # store all repositories for user selection
    while True:
        repos = fetch_repos_with_retry(api_url, page)
        if repos is None:
            print(f"Failed to fetch repositories for organization: {org_name}")
            return
        if not repos:
            break  # no more repositories to fetch
        all_repos.extend(repos)
        page += 1

    if not all_repos:
        print(f"No repositories found for organization: {org_name}")
        return

    # ask user if they want to clone all repositories or select specific ones
    clone_all = (
        input("Press Enter to clone all repositories or type 'select' to choose specific ones: ")
        .strip()
        .lower()
    )

    if clone_all == "":  # user pressed Enter
        selected_indices = range(len(all_repos))  # select all repositories
    elif clone_all == "select":
        print("Available repositories:")
        for i, repo in enumerate(all_repos):
            print(f"{i + 1}: {repo['name']}")

        selected_indices = input(
            "Enter the numbers of the repositories you want to clone (comma-separated): "
        )
        selected_indices = [int(i) - 1 for i in selected_indices.split(",")]
    else:
        print("Invalid input. Exiting.")
        return

    for index in selected_indices:
        repo = all_repos[index]
        repo_name = repo["name"]
        repo_url = repo["clone_url"]
        print(f"Cloning {repo_name}...")

        # clone the repository
        subprocess.run(["git", "clone", repo_url])

    print(f"Selected repositories for {org_name} have been cloned into {org_path}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Clone all repositories from a GitHub organization."
    )
    parser.add_argument("--org", default=TARGET_ORG_NAME, help="GitHub organization name")
    parser.add_argument("--base-dir", default=DEFAULT_BASE_DIR, help="Base directory for cloning")
    parser.add_argument(
        "--org-dir",
        default=DEFAULT_ORG_DIR,
        help="Name of the organization directory (defaults to org name)",
    )
    args = parser.parse_args()

    clone_organization_repos(args.org, args.base_dir, args.org_dir)

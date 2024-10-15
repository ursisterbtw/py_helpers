import argparse
import os
import shutil
import subprocess
import sys

import requests

# Config
TARGET_ORG_NAME = "paradigmxyz"
DEFAULT_BASE_DIR = "submodules"
DEFAULT_ORG_DIR = None


def find_readme(repo_path):
    """
    Searches for a README file in the given repository path, case-insensitive.
    Returns the path to the README file if found, otherwise None.
    """
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if file.lower() == "readme.md":
                return os.path.join(root, file)
    return None


def clone_organization_repos(org_name, base_dir, org_dir):
    # Use org_name as org_dir if not specified
    if org_dir is None:
        org_dir = org_name

    # Get the current working directory
    current_dir = os.getcwd()

    # Create the base directory if it doesn't exist
    base_path = os.path.join(current_dir, base_dir)

    # Ensure that base_path is within the current directory
    if not os.path.abspath(base_path).startswith(current_dir):
        print("Error: Attempting to create directories outside of the current directory.")
        sys.exit(1)

    os.makedirs(base_path, exist_ok=True)

    # Create the organization directory within base_dir
    org_path = os.path.join(base_path, org_dir)

    # Ensure that org_path is within the current directory
    if not os.path.abspath(org_path).startswith(current_dir):
        print("Error: Attempting to create directories outside of the current directory.")
        sys.exit(1)

    # Check if org_path already exists
    if os.path.exists(org_path):
        print(
            f"Warning: The directory {org_path} already exists. Cloning will proceed inside this directory."
        )
    else:
        os.makedirs(org_path, exist_ok=True)

    os.chdir(org_path)

    # GitHub API URL for listing organization repositories
    api_url = f"https://api.github.com/orgs/{org_name}/repos"

    # Fetch repositories (paginated)
    page = 1
    all_repos = []  # Store all repositories for user selection
    while True:
        response = requests.get(f"{api_url}?page={page}&per_page=100")
        if response.status_code != 200:
            print(f"Error fetching repositories: {response.status_code}")
            sys.exit(1)

        repos = response.json()
        if not repos:
            break  # No more repositories to fetch

        all_repos.extend(repos)  # Add fetched repos to the list
        page += 1

    # Ask user if they want to clone all repositories or select specific ones
    clone_all = (
        input("Press Enter to clone all repositories or type 'select' to choose specific ones: ")
        .strip()
        .lower()
    )

    if clone_all == "":  # User pressed Enter
        selected_indices = range(len(all_repos))  # Select all repositories
    elif clone_all == "select":
        print("Available repositories:")
        for i, repo in enumerate(all_repos):
            print(f"{i + 1}: {repo['name']}")

        selected_indices_input = input(
            "Enter the numbers of the repositories you want to clone (comma-separated): "
        )
        try:
            selected_indices = [int(i) - 1 for i in selected_indices_input.split(",")]
        except ValueError:
            print("Invalid input. Please enter comma-separated numbers.")
            return
    else:
        print("Invalid input. Exiting.")
        return

    # Ensure 'docs' directory exists
    docs_dir = os.path.join(current_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)

    for index in selected_indices:
        if index < 0 or index >= len(all_repos):
            print(f"Index {index + 1} is out of range. Skipping.")
            continue

        repo = all_repos[index]
        repo_name = repo["name"]
        repo_url = repo["clone_url"]
        print(f"Cloning {repo_name}...")

        # Clone the repository
        subprocess.run(["git", "clone", repo_url])

        # Path to the cloned repo
        repo_path = os.path.join(org_path, repo_name)

        # Find the README.md file
        readme_src = find_readme(repo_path)

        if readme_src:
            # Create a unique filename for the README
            repo_readme_name = f"{repo_name}_README.md"
            readme_dest = os.path.join(docs_dir, repo_readme_name)
            shutil.copy(readme_src, readme_dest)
            print(f"README.md from {repo_name} copied to docs/{repo_readme_name}")
        else:
            print(f"No README.md found for {repo_name}.")

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

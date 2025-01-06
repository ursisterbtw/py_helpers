"""
GitHub Repository Cloning Tool

This module provides functionality to clone repositories from GitHub organizations,
either all repositories or a selected subset, with README file management.
"""

import argparse
import os
import shutil
import subprocess
import sys

import requests

# config
TARGET_ORG_NAME = "paradigmxyz"
DEFAULT_BASE_DIR = "paradigmxyz"
DEFAULT_ORG_DIR = None


def find_readme(repo_path):
    """
    searches for a README file in the given repository path, case-insensitive.
    returns the path to the README file if found, otherwise None.
    """
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.lower() == "readme.md":
                return os.path.join(root, file)
    return None


def setup_directories(base_dir, org_dir, current_dir):
    """Set up and validate the required directories."""
    base_path = os.path.join(current_dir, base_dir)
    if not os.path.abspath(base_path).startswith(current_dir):
        print("Error: Attempting to create directories outside of the current directory.")
        sys.exit(1)
    os.makedirs(base_path, exist_ok=True)

    org_path = os.path.join(base_path, org_dir)
    if not os.path.abspath(org_path).startswith(current_dir):
        print("Error: Attempting to create directories outside of the current directory.")
        sys.exit(1)

    if os.path.exists(org_path):
        print(f"Warning: The directory {
              org_path} already exists. Cloning will proceed inside this directory.")
    else:
        os.makedirs(org_path, exist_ok=True)
    return org_path


def fetch_repositories(organization_name):
    """Fetch all repositories from the GitHub organization."""
    api_url = f"https://api.github.com/orgs/{organization_name}/repos"
    repositories = []
    page_number = 1

    while True:
        response = requests.get(
            f"{api_url}?page={page_number}&per_page=100", timeout=30)
        if response.status_code != 200:
            raise requests.RequestException(
                f"Failed to fetch repositories: HTTP {response.status_code}")

        repo_data = response.json()
        if not repo_data:
            break

        repositories.extend(repo_data)
        page_number += 1

    return repositories


def get_user_input_for_repos():
    """Get user input for repository selection."""
    prompt = ("Press Enter to clone all repositories or "
             "type 'select' to choose specific ones: ")
    return input(prompt).strip().lower()


def get_selected_repos(all_repos):
    """Get user selection of repositories to clone."""
    clone_all = get_user_input_for_repos()
    if clone_all == "":
        return range(len(all_repos))
    if clone_all != "select":
        print("Invalid input. Exiting.")
        return []

    print("Available repositories:")
    for i, repo in enumerate(all_repos):
        print(f"{i + 1}: {repo['name']}")

    try:
        indices_input = input(
            "Enter the numbers of repositories to clone (comma-separated): ")
        return [int(i) - 1 for i in indices_input.split(",")]
    except ValueError:
        print("Invalid input. Please enter comma-separated numbers.")
        return []


def clone_and_process_repo(repo_name, repo_url, org_path, docs_dir):
    """Clone a repository and process its README file."""
    subprocess.run(["git", "clone", repo_url], check=True)
    repo_path = os.path.join(org_path, repo_name)

    if readme_src := find_readme(repo_path):
        repo_readme_name = f"{repo_name}_README.md"
        readme_dest = os.path.join(docs_dir, repo_readme_name)
        shutil.copy(readme_src, readme_dest)
        print(f"README.md from {repo_name} "
              f"copied to docs/{repo_readme_name}")
    else:
        print(f"No README.md found for {repo_name}.")


def clone_repos_from_file(repos_file, org_path):
    """Clone repositories listed in a file."""
    with open(repos_file, "r", encoding="utf-8") as file:
        for line in file:
            repo_ref = line.strip().split()[-1]

            if repo_ref.startswith("https://github.com/"):
                repo_ref = repo_ref.replace("https://github.com/", "")
                if repo_ref.endswith(".git"):
                    repo_ref = repo_ref[:-4]

            if repo_ref.startswith("@"):
                repo_ref = repo_ref[1:]

            command = ["gh", "repo", "clone", repo_ref]
            repo_name = repo_ref.split("/")[-1]
            print(f"cloning {repo_name}...")

            subprocess.run(command, cwd=org_path, check=True)

            repo_path = os.path.join(org_path, repo_name)
            if readme_src := find_readme(repo_path):
                docs_dir = os.path.join(os.getcwd(), "docs")
                os.makedirs(docs_dir, exist_ok=True)
                repo_readme_name = f"{repo_name}_README.md"
                readme_dest = os.path.join(docs_dir, repo_readme_name)
                shutil.copy(readme_src, readme_dest)
                print(f"README.md from {repo_name} "
                      f"copied to docs/{repo_readme_name}")
            else:
                print(f"no README.md found for {repo_name}. bummer!")


def clone_organization_repos(org_name, base_dir, org_dir, repos_file=None):
    """Clone repositories from a GitHub organization.

    Args:
        org_name: Name of the GitHub organization
        base_dir: Base directory for cloning
        org_dir: Directory to clone into (defaults to org_name)
        repos_file: Optional path to file containing repo URLs
    """
    org_dir = org_dir or org_name
    current_dir = os.getcwd()
    org_path = setup_directories(base_dir, org_dir, current_dir)
    os.chdir(org_path)

    if repos_file:
        clone_repos_from_file(repos_file, org_path)
        return

    all_repos = fetch_repositories(org_name)
    selected_indices = get_selected_repos(all_repos)

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

        clone_and_process_repo(repo_name, repo_url, org_path, docs_dir)

    print(f"Selected repositories have been cloned into {org_path}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Clone all repositories from a GitHub organization or from a specified file."
    )
    parser.add_argument("--org", default=TARGET_ORG_NAME,
                        help="GitHub organization name")
    parser.add_argument("--base-dir", default=DEFAULT_BASE_DIR,
                        help="Base directory for cloning")
    parser.add_argument(
        "--org-dir",
        default=DEFAULT_ORG_DIR,
        help="Name of the organization directory (defaults to org name)",
    )
    parser.add_argument(
        "--repos-file",
        help="Path to a file containing specific gh repo clone commands",
    )
    args = parser.parse_args()

    print(args)
    clone_organization_repos(args.org, args.base_dir,
                             args.org_dir, args.repos_file)

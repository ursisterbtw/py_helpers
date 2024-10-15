import argparse
import os
import shutil
import subprocess
import sys

import requests

# config
TARGET_ORG_NAME = "paradigmxyz"
DEFAULT_BASE_DIR = "submodules"
DEFAULT_ORG_DIR = None


def find_readme(repo_path):
    """
    searches for a README file in the given repository path, case-insensitive.
    returns the path to the README file if found, otherwise None.
    """
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if file.lower() == "readme.md":
                return os.path.join(root, file)
    return None


def clone_organization_repos(org_name, base_dir, org_dir, repos_file=None):
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

    if repos_file:
        # clone repos from the provided file
        clone_repos_from_file(repos_file, org_path)
    else:
        # gitHub API URL for listing organization repositories
        api_url = f"https://api.github.com/orgs/{org_name}/repos"

        # fetch repositories (paginated)
        page = 1
        all_repos = []  # store all repositories for user selection
        while True:
            response = requests.get(f"{api_url}?page={page}&per_page=100")
            if response.status_code != 200:
                print(f"Error fetching repositories: {response.status_code}")
                sys.exit(1)

            repos = response.json()
            if not repos:
                break  # mo more repositories to fetch

            all_repos.extend(repos)  # add fetched repos to the list
            page += 1

        # ask user if they want to clone all repositories or select specific ones
        clone_all = (
            input(
                "Press Enter to clone all repositories or type 'select' to choose specific ones: "
            )
            .strip()
            .lower()
        )

        if clone_all == "":  # user pressed Enter
            selected_indices = range(len(all_repos))  # select all repositories
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

        # ensure 'docs' directory exists
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

            # clone the repository
            subprocess.run(["git", "clone", repo_url])

            # path to the cloned repo
            repo_path = os.path.join(org_path, repo_name)

            # find the README.md file
            readme_src = find_readme(repo_path)

            if readme_src:
                # create a unique filename for the README
                repo_readme_name = f"{repo_name}_README.md"
                readme_dest = os.path.join(docs_dir, repo_readme_name)
                shutil.copy(readme_src, readme_dest)
                print(f"README.md from {repo_name} copied to docs/{repo_readme_name}")
            else:
                print(f"No README.md found for {repo_name}.")

    print(f"Selected repositories have been cloned into {org_path}/")


def clone_repos_from_file(repos_file, org_path):
    with open(repos_file, "r") as file:
        for line in file:
            # strip and split the line to get the repo reference
            repo_ref = line.strip().split()[-1]

            # convert full URLs to GitHub CLI format
            if repo_ref.startswith("https://github.com/"):
                repo_ref = repo_ref.replace("https://github.com/", "")
                if repo_ref.endswith(".git"):
                    repo_ref = repo_ref[:-4]

            # remove @ symbol if present
            if repo_ref.startswith("@"):
                repo_ref = repo_ref[1:]

            # construct the gh cli command
            command = ["gh", "repo", "clone", repo_ref]

            repo_name = repo_ref.split("/")[-1]
            print(f"cloning {repo_name}...")

            # execute the gh cli command
            subprocess.run(command, cwd=org_path)

            # find and copy README
            repo_path = os.path.join(org_path, repo_name)
            readme_src = find_readme(repo_path)
            if readme_src:
                docs_dir = os.path.join(os.getcwd(), "docs")
                os.makedirs(docs_dir, exist_ok=True)
                repo_readme_name = f"{repo_name}_README.md"
                readme_dest = os.path.join(docs_dir, repo_readme_name)
                shutil.copy(readme_src, readme_dest)
                print(f"README.md from {repo_name} copied to docs/{repo_readme_name}")
            else:
                print(f"no README.md found for {repo_name}. bummer!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Clone all repositories from a GitHub organization or from a specified file."
    )
    parser.add_argument("--org", default=TARGET_ORG_NAME, help="GitHub organization name")
    parser.add_argument("--base-dir", default=DEFAULT_BASE_DIR, help="Base directory for cloning")
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

    clone_organization_repos(args.org, args.base_dir, args.org_dir, args.repos_file)

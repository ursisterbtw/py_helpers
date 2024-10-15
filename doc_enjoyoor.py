import os
from urllib.parse import urlparse

import requests


def get_package_names(requirements_path):
    with open(requirements_path, "r") as file:
        lines = file.readlines()
    packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            # remove version specifiers
            package = line.split("==")[0].split(">=")[0].split(">")[0].split("<")[0].strip()
            packages.append(package)
    return packages


def get_github_repo(package):
    url = f"https://pypi.org/pypi/{package}/json"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch data for package: {package}")
        return None
    data = response.json()
    project_urls = data.get("info", {}).get("project_urls")

    # ensure project_urls is a dictionary
    if not isinstance(project_urls, dict):
        project_urls = {}

    # common keys that might contain the repository URL
    possible_keys = ["Source", "Homepage", "Source Code", "Repository"]
    for key in possible_keys:
        repo_url = project_urls.get(key)
        if repo_url and "github.com" in repo_url:
            return repo_url
    # fallback to home_page
    home_page = data.get("info", {}).get("home_page")
    if isinstance(home_page, str) and "github.com" in home_page:
        return home_page
    return None


def fetch_readme(repo_url):
    parsed_url = urlparse(repo_url)
    path_parts = parsed_url.path.strip("/").split("/")
    if len(path_parts) < 2:
        return None
    owner, repo = path_parts[:2]
    api_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
    response = requests.get(api_url)
    if response.status_code == 404:
        # try master branch
        api_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
        response = requests.get(api_url)
    if response.status_code == 200:
        return response.text
    print(f"README.md not found for repository: {repo_url}")
    return None


def save_readme(package, content, docs_dir):
    filename = f"{package}_README.md"
    filepath = os.path.join(docs_dir, filename)
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(content)
    print(f"Saved README for {package} to {filepath}")


def main():
    repo_root = os.getcwd()
    requirements_path = os.path.join(repo_root, "requirements.txt")
    if not os.path.exists(requirements_path):
        print("requirements.txt not found in the current directory.")
        return

    docs_dir = os.path.join(repo_root, "docs")
    os.makedirs(docs_dir, exist_ok=True)

    packages = get_package_names(requirements_path)
    print(f"Found {len(packages)} packages in requirements.txt.")

    for package in packages:
        print(f"Processing package: {package}")
        repo_url = get_github_repo(package)
        if not repo_url:
            print(f"GitHub repository not found for package: {package}")
            continue
        readme_content = fetch_readme(repo_url)
        if readme_content:
            save_readme(package, readme_content, docs_dir)


if __name__ == "__main__":
    main()

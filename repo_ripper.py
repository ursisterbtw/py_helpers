"""
repo_ripper.py

a tool that provides functionality to clone repositories from GitHub organizations 
via a TUI/CLI.
"""

import argparse
import os
import shutil
import subprocess
import sys
from typing import List, Optional

import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich import print as rprint

# config
TARGET_ORG_NAME = "thorlabsDev"
DEFAULT_BASE_DIR = "thorlabsDev"
DEFAULT_ORG_DIR = None

# Initialize rich console
console = Console()

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
        console.print("[red]Error: Attempting to create directories outside of the current directory.[/red]")
        sys.exit(1)
    os.makedirs(base_path, exist_ok=True)

    org_path = os.path.join(base_path, org_dir)
    if not os.path.abspath(org_path).startswith(current_dir):
        console.print("[red]Error: Attempting to create directories outside of the current directory.[/red]")
        sys.exit(1)

    if os.path.exists(org_path):
        console.print(f"[yellow]Warning: The directory {org_path} already exists. Cloning will proceed inside this directory.[/yellow]")
    else:
        os.makedirs(org_path, exist_ok=True)
    return org_path


def fetch_repositories(organization_name):
    """Fetch all repositories from the GitHub organization."""
    api_url = f"https://api.github.com/orgs/{organization_name}/repos"
    repositories = []
    page_number = 1

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Fetching repositories...", total=None)

        while True:
            try:
                response = requests.get(
                    f"{api_url}?page={page_number}&per_page=100", timeout=30)
                response.raise_for_status()
            except requests.RequestException as e:
                console.print(f"[red]Failed to fetch repositories: {str(e)}[/red]")
                sys.exit(1)

            repo_data = response.json()
            if not repo_data:
                break

            repositories.extend(repo_data)
            page_number += 1

    return repositories


def get_user_input_for_repos():
    """Get user input for repository selection."""
    return Confirm.ask("Would you like to select specific repositories?", default=False)


def get_selected_repos(all_repos):
    """Get user selection of repositories to clone."""
    select_specific = get_user_input_for_repos()

    if not select_specific:
        return range(len(all_repos))

    # Create and display the repository table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim")
    table.add_column("Repository", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Stars", justify="right", style="yellow")

    for i, repo in enumerate(all_repos, 1):
        table.add_row(
            str(i),
            repo['name'],
            (repo.get('description') or "")[:50] + "..." if repo.get('description') and len(repo.get('description')) > 50 else (repo.get('description') or "No description"),
            str(repo.get('stargazers_count', 0))
        )

    console.print(table)

    while True:
        try:
            indices_input = Prompt.ask(
                "\nEnter repository numbers to clone (comma-separated, e.g., '1,3,5')"
            )
            selected = [int(i.strip()) - 1 for i in indices_input.split(",")]
            if all(0 <= i < len(all_repos) for i in selected):
                return selected
            console.print("[red]Some numbers are out of range. Please try again.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter comma-separated numbers.[/red]")


def clone_and_process_repo(repo_name: str, repo_url: str, org_path: str, docs_dir: str) -> bool:
    """Clone a repository and process its README file."""
    try:
        with console.status(f"[bold blue]Cloning {repo_name}...[/bold blue]"):
            subprocess.run(["git", "clone", repo_url], check=True, capture_output=True)

        repo_path = os.path.join(org_path, repo_name)

        if readme_src := find_readme(repo_path):
            repo_readme_name = f"{repo_name}_README.md"
            readme_dest = os.path.join(docs_dir, repo_readme_name)
            shutil.copy(readme_src, readme_dest)
            console.print(f"[green]✓[/green] Copied README from {repo_name} to docs/{repo_readme_name}")
            return True
        else:
            console.print(f"[yellow]⚠[/yellow] No README.md found for {repo_name}")
            return False
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗[/red] Failed to clone {repo_name}: {e}")
        return False


def clone_repos_from_file(repos_file: str, org_path: str):
    """Clone repositories listed in a file."""
    successful_clones = 0
    failed_clones = 0
    processed_readmes = 0

    with open(repos_file, "r", encoding="utf-8") as file:
        repos = [line.strip() for line in file if line.strip()]

    with Progress() as progress:
        clone_task = progress.add_task("[cyan]Cloning repositories...", total=len(repos))

        for line in repos:
            repo_ref = line.split()[-1]

            if repo_ref.startswith("https://github.com/"):
                repo_ref = repo_ref.replace("https://github.com/", "")
                if repo_ref.endswith(".git"):
                    repo_ref = repo_ref[:-4]

            if repo_ref.startswith("@"):
                repo_ref = repo_ref[1:]

            command = ["gh", "repo", "clone", repo_ref]
            repo_name = repo_ref.split("/")[-1]

            try:
                subprocess.run(command, cwd=org_path, check=True, capture_output=True)
                successful_clones += 1

                repo_path = os.path.join(org_path, repo_name)
                if readme_src := find_readme(repo_path):
                    docs_dir = os.path.join(os.getcwd(), "docs")
                    os.makedirs(docs_dir, exist_ok=True)
                    repo_readme_name = f"{repo_name}_README.md"
                    readme_dest = os.path.join(docs_dir, repo_readme_name)
                    shutil.copy(readme_src, readme_dest)
                    processed_readmes += 1
                    console.print(f"[green]✓[/green] Processed {repo_name}")
                else:
                    console.print(f"[yellow]⚠[/yellow] No README.md found for {repo_name}")
            except subprocess.CalledProcessError as e:
                console.print(f"[red]✗[/red] Failed to clone {repo_name}: {e}")
                failed_clones += 1

            progress.update(clone_task, advance=1)

    # Print summary
    console.print("\n[bold]Clone Operation Summary:[/bold]")
    console.print(f"Successfully cloned: [green]{successful_clones}[/green] repositories")
    console.print(f"Failed to clone: [red]{failed_clones}[/red] repositories")
    console.print(f"Processed READMEs: [blue]{processed_readmes}[/blue]")


def clone_organization_repos(org_name: str, base_dir: str, org_dir: Optional[str], repos_file: Optional[str] = None):
    """Clone repositories from a GitHub organization."""
    console.print("[bold blue]🚀 Starting Repository Ripper[/bold blue]")

    org_dir = org_dir or org_name
    current_dir = os.getcwd()
    org_path = setup_directories(base_dir, org_dir, current_dir)
    os.chdir(org_path)

    if repos_file:
        console.print(f"\n[bold]Cloning repositories from file: {repos_file}[/bold]")
        clone_repos_from_file(repos_file, org_path)
        return

    console.print(f"\n[bold]Fetching repositories from {org_name}...[/bold]")
    all_repos = fetch_repositories(org_name)
    console.print(f"[green]Found {len(all_repos)} repositories[/green]")

    selected_indices = get_selected_repos(all_repos)

    docs_dir = os.path.join(current_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)

    successful_clones = 0
    failed_clones = 0
    processed_readmes = 0

    with Progress() as progress:
        clone_task = progress.add_task("[cyan]Cloning repositories...", total=len(selected_indices))

        for index in selected_indices:
            if index < 0 or index >= len(all_repos):
                console.print(f"[yellow]⚠ Index {index + 1} is out of range. Skipping.[/yellow]")
                continue

            repo = all_repos[index]
            repo_name = repo["name"]
            repo_url = repo["clone_url"]

            if clone_and_process_repo(repo_name, repo_url, org_path, docs_dir):
                successful_clones += 1
                processed_readmes += 1
            else:
                failed_clones += 1

            progress.update(clone_task, advance=1)

    # Print final summary
    console.print("\n[bold]Operation Summary:[/bold]")
    console.print(f"Successfully cloned: [green]{successful_clones}[/green] repositories")
    console.print(f"Failed to clone: [red]{failed_clones}[/red] repositories")
    console.print(f"Processed READMEs: [blue]{processed_readmes}[/blue]")
    console.print(f"\n[bold green]✨ All selected repositories have been processed in {org_path}/[/bold green]")


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

    try:
        clone_organization_repos(args.org, args.base_dir,
                               args.org_dir, args.repos_file)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]An error occurred: {str(e)}[/red]")
        sys.exit(1)

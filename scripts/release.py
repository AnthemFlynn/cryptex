#!/usr/bin/env python3
"""
Release script for Codename library.

This script handles version bumping, changelog generation, and release preparation.
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class ReleaseError(Exception):
    """Custom exception for release failures."""
    pass


class CodenameReleaseTool:
    """Release tool for Codename library."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.version_file = self.project_root / "src" / "codename" / "__init__.py"
        self.changelog_file = self.project_root / "CHANGELOG.md"
        self.pyproject_file = self.project_root / "pyproject.toml"

    def run_command(self, command: list[str], description: str = "", capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run a command and handle errors."""
        print(f"🔄 {description or ' '.join(command)}")

        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                check=True,
                capture_output=capture_output,
                text=True
            )
            return result

        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {' '.join(command)}")
            if e.stdout and capture_output:
                print("STDOUT:", e.stdout)
            if e.stderr and capture_output:
                print("STDERR:", e.stderr)
            raise ReleaseError(f"Command failed: {' '.join(command)}")

    def get_current_version(self) -> str:
        """Get the current version from __init__.py."""
        if not self.version_file.exists():
            raise ReleaseError(f"Version file not found: {self.version_file}")

        content = self.version_file.read_text()
        version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)

        if not version_match:
            raise ReleaseError("Could not find version in __init__.py")

        return version_match.group(1)

    def bump_version(self, bump_type: str = "patch") -> str:
        """Bump the version number."""
        current_version = self.get_current_version()
        print(f"📋 Current version: {current_version}")

        # Parse semantic version
        version_parts = current_version.split(".")
        if len(version_parts) != 3:
            raise ReleaseError(f"Invalid version format: {current_version}")

        major, minor, patch = map(int, version_parts)

        # Bump version based on type
        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1
        else:
            raise ReleaseError(f"Invalid bump type: {bump_type}")

        new_version = f"{major}.{minor}.{patch}"
        print(f"🔄 Bumping version to: {new_version}")

        # Update __init__.py
        content = self.version_file.read_text()
        new_content = re.sub(
            r'__version__\s*=\s*["\'][^"\']+["\']',
            f'__version__ = "{new_version}"',
            content
        )
        self.version_file.write_text(new_content)

        print(f"✅ Version bumped to {new_version}")
        return new_version

    def get_git_commits_since_tag(self, tag: str = None) -> list[str]:
        """Get commit messages since the last tag."""
        if tag is None:
            # Get the latest tag
            try:
                result = self.run_command(
                    ["git", "describe", "--tags", "--abbrev=0"],
                    "Getting latest tag"
                )
                tag = result.stdout.strip()
            except ReleaseError:
                # No tags found, get all commits
                tag = None

        if tag:
            command = ["git", "log", f"{tag}..HEAD", "--oneline", "--no-merges"]
        else:
            command = ["git", "log", "--oneline", "--no-merges"]

        try:
            result = self.run_command(command, f"Getting commits since {tag or 'beginning'}")
            commits = result.stdout.strip().split('\n') if result.stdout.strip() else []
            return [commit for commit in commits if commit.strip()]
        except ReleaseError:
            return []

    def categorize_commits(self, commits: list[str]) -> dict[str, list[str]]:
        """Categorize commits by type."""
        categories = {
            "Added": [],
            "Changed": [],
            "Fixed": [],
            "Security": [],
            "Deprecated": [],
            "Removed": []
        }

        # Patterns for categorizing commits
        patterns = {
            "Added": [r"^[a-f0-9]+\s+(feat|add|new):", r"^[a-f0-9]+\s+.*\b(add|new|implement|create)\b"],
            "Changed": [r"^[a-f0-9]+\s+(change|update|modify):", r"^[a-f0-9]+\s+.*\b(change|update|modify|improve)\b"],
            "Fixed": [r"^[a-f0-9]+\s+(fix|bug):", r"^[a-f0-9]+\s+.*\b(fix|bug|resolve|correct)\b"],
            "Security": [r"^[a-f0-9]+\s+security:", r"^[a-f0-9]+\s+.*\b(security|vulnerability|cve)\b"],
            "Deprecated": [r"^[a-f0-9]+\s+deprecate:", r"^[a-f0-9]+\s+.*\b(deprecate|obsolete)\b"],
            "Removed": [r"^[a-f0-9]+\s+(remove|delete):", r"^[a-f0-9]+\s+.*\b(remove|delete|drop)\b"]
        }

        uncategorized = []

        for commit in commits:
            categorized = False

            for category, category_patterns in patterns.items():
                for pattern in category_patterns:
                    if re.search(pattern, commit, re.IGNORECASE):
                        # Clean up commit message
                        clean_commit = re.sub(r'^[a-f0-9]+\s+', '', commit)
                        categories[category].append(clean_commit)
                        categorized = True
                        break

                if categorized:
                    break

            if not categorized:
                clean_commit = re.sub(r'^[a-f0-9]+\s+', '', commit)
                uncategorized.append(clean_commit)

        # Add uncategorized to "Changed"
        categories["Changed"].extend(uncategorized)

        return categories

    def update_changelog(self, version: str, categories: dict[str, list[str]]) -> bool:
        """Update the changelog with new version."""
        if not self.changelog_file.exists():
            raise ReleaseError(f"Changelog file not found: {self.changelog_file}")

        print(f"📝 Updating changelog for version {version}")

        # Read current changelog
        content = self.changelog_file.read_text()

        # Generate new changelog entry
        date_str = datetime.now().strftime("%Y-%m-%d")
        new_entry = f"\n## [{version}] - {date_str}\n\n"

        # Add categories with content
        for category, items in categories.items():
            if items:
                new_entry += f"### {category}\n"
                for item in items:
                    new_entry += f"- {item}\n"
                new_entry += "\n"

        # Insert new entry after "## [Unreleased]" section
        unreleased_pattern = r"(## \[Unreleased\].*?)(\n## \[)"
        if re.search(unreleased_pattern, content, re.DOTALL):
            # Clear unreleased section and add new version
            new_content = re.sub(
                unreleased_pattern,
                r"\1\n" + new_entry + r"\2",
                content,
                flags=re.DOTALL
            )

            # Clear unreleased sections
            new_content = re.sub(
                r"(## \[Unreleased\].*?)(### Added.*?)(\n## \[)",
                r"\1\n### Added\n- N/A\n\n### Changed\n- N/A\n\n### Deprecated\n- N/A\n\n### Removed\n- N/A\n\n### Fixed\n- N/A\n\n### Security\n- N/A\n\3",
                new_content,
                flags=re.DOTALL
            )
        else:
            # Insert after first line if no unreleased section
            lines = content.split('\n')
            lines.insert(3, new_entry.rstrip())
            new_content = '\n'.join(lines)

        # Write updated changelog
        self.changelog_file.write_text(new_content)
        print("✅ Changelog updated")
        return True

    def validate_release_readiness(self) -> bool:
        """Validate that the project is ready for release."""
        print("🔍 Validating release readiness...")

        # Check git status
        try:
            result = self.run_command(["git", "status", "--porcelain"], "Checking git status")
            if result.stdout.strip():
                print("❌ Working directory is not clean:")
                print(result.stdout)
                return False
        except ReleaseError:
            print("❌ Not a git repository or git not available")
            return False

        # Check current branch
        try:
            result = self.run_command(["git", "branch", "--show-current"], "Checking current branch")
            current_branch = result.stdout.strip()
            if current_branch not in ["main", "master"]:
                print(f"⚠️  Not on main/master branch (current: {current_branch})")
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    return False
        except ReleaseError:
            pass

        # Check if tests pass
        try:
            self.run_command(["pytest", "tests/", "-x"], "Running tests", capture_output=False)
        except ReleaseError:
            print("❌ Tests are failing")
            return False

        print("✅ Release validation passed")
        return True

    def create_git_tag(self, version: str) -> bool:
        """Create a git tag for the release."""
        tag_name = f"v{version}"

        try:
            # Create annotated tag
            self.run_command(
                ["git", "tag", "-a", tag_name, "-m", f"Release {version}"],
                f"Creating tag {tag_name}"
            )

            print(f"✅ Created tag: {tag_name}")
            return True

        except ReleaseError:
            print(f"❌ Failed to create tag: {tag_name}")
            return False

    def commit_changes(self, version: str) -> bool:
        """Commit version bump and changelog changes."""
        try:
            # Add files
            self.run_command(
                ["git", "add", str(self.version_file), str(self.changelog_file)],
                "Staging release files"
            )

            # Commit
            self.run_command(
                ["git", "commit", "-m", f"chore: bump version to {version}"],
                f"Committing version {version}"
            )

            print(f"✅ Committed version {version}")
            return True

        except ReleaseError:
            print("❌ Failed to commit changes")
            return False

    def prepare_release(self, bump_type: str = "patch", dry_run: bool = False) -> str:
        """Prepare a new release."""
        print(f"🚀 Preparing {bump_type} release...")

        if not dry_run:
            # Validate release readiness
            if not self.validate_release_readiness():
                raise ReleaseError("Release validation failed")

        # Get current version and commits
        current_version = self.get_current_version()
        commits = self.get_git_commits_since_tag()

        if not commits:
            print("⚠️  No commits found since last release")
            if not dry_run:
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    raise ReleaseError("No changes to release")

        print(f"📋 Found {len(commits)} commits since last release")

        # Categorize commits
        categories = self.categorize_commits(commits)

        # Show what will be included
        print("\n📝 Changes to be included:")
        for category, items in categories.items():
            if items:
                print(f"\n{category}:")
                for item in items[:5]:  # Show first 5
                    print(f"  - {item}")
                if len(items) > 5:
                    print(f"  ... and {len(items) - 5} more")

        if dry_run:
            print(f"\n🔍 DRY RUN: Would bump version from {current_version}")
            new_version = self.calculate_new_version(current_version, bump_type)
            print(f"🔍 DRY RUN: New version would be {new_version}")
            return new_version

        # Confirm release
        response = input(f"\nProceed with {bump_type} release? (y/N): ")
        if response.lower() != 'y':
            raise ReleaseError("Release cancelled by user")

        # Bump version
        new_version = self.bump_version(bump_type)

        # Update changelog
        self.update_changelog(new_version, categories)

        # Commit changes
        if not self.commit_changes(new_version):
            raise ReleaseError("Failed to commit changes")

        # Create tag
        if not self.create_git_tag(new_version):
            raise ReleaseError("Failed to create tag")

        print(f"\n🎉 Release {new_version} prepared successfully!")
        print("\nNext steps:")
        print("  1. Push changes: git push origin main")
        print(f"  2. Push tag: git push origin v{new_version}")
        print("  3. GitHub Actions will automatically publish to PyPI")

        return new_version

    def calculate_new_version(self, current_version: str, bump_type: str) -> str:
        """Calculate what the new version would be."""
        version_parts = current_version.split(".")
        major, minor, patch = map(int, version_parts)

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1

        return f"{major}.{minor}.{patch}"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Release script for Codename library")
    parser.add_argument(
        "command",
        nargs="?",
        default="prepare",
        choices=["prepare", "version", "changelog", "commits"],
        help="Command to run"
    )
    parser.add_argument(
        "--bump",
        default="patch",
        choices=["major", "minor", "patch"],
        help="Version bump type"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )

    args = parser.parse_args()

    # Create release tool instance
    releaser = CodenameReleaseTool()

    try:
        if args.command == "version":
            version = releaser.get_current_version()
            print(f"Current version: {version}")

        elif args.command == "commits":
            commits = releaser.get_git_commits_since_tag()
            if commits:
                print(f"Commits since last release ({len(commits)}):")
                for commit in commits:
                    print(f"  {commit}")
            else:
                print("No commits since last release")

        elif args.command == "changelog":
            commits = releaser.get_git_commits_since_tag()
            categories = releaser.categorize_commits(commits)

            print("Categorized changes:")
            for category, items in categories.items():
                if items:
                    print(f"\n{category}:")
                    for item in items:
                        print(f"  - {item}")

        elif args.command == "prepare":
            new_version = releaser.prepare_release(
                bump_type=args.bump,
                dry_run=args.dry_run
            )
            print(f"Release preparation complete: {new_version}")

        else:
            print(f"❌ Unknown command: {args.command}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n❌ Release preparation interrupted by user")
        sys.exit(1)
    except ReleaseError as e:
        print(f"❌ Release failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

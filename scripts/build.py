#!/usr/bin/env python3
"""
Build script for Codename library.

This script handles the complete build process including validation,
testing, and package creation.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


class BuildError(Exception):
    """Custom exception for build failures."""
    pass


class CodenameBuildTool:
    """Build tool for Codename library."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"

    def run_command(self, command: list[str], description: str = "") -> bool:
        """Run a command and handle errors."""
        print(f"🔄 {description or ' '.join(command)}")

        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                print(result.stdout)
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {' '.join(command)}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            return False

    def clean(self) -> bool:
        """Clean build artifacts."""
        print("🧹 Cleaning build artifacts...")

        # Remove build directories
        for dir_path in [self.dist_dir, self.build_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"  Removed {dir_path}")

        # Remove egg-info directories
        for egg_info in self.project_root.glob("*.egg-info"):
            if egg_info.is_dir():
                shutil.rmtree(egg_info)
                print(f"  Removed {egg_info}")

        # Remove cache directories
        cache_dirs = [
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "__pycache__"
        ]

        for cache_dir in cache_dirs:
            for path in self.project_root.rglob(cache_dir):
                if path.is_dir():
                    shutil.rmtree(path)
                    print(f"  Removed {path}")

        # Remove coverage files
        for cov_file in self.project_root.glob(".coverage*"):
            cov_file.unlink()
            print(f"  Removed {cov_file}")

        htmlcov = self.project_root / "htmlcov"
        if htmlcov.exists():
            shutil.rmtree(htmlcov)
            print(f"  Removed {htmlcov}")

        print("✅ Clean completed")
        return True

    def validate_environment(self) -> bool:
        """Validate the build environment."""
        print("🔍 Validating build environment...")

        # Check Python version
        print(f"✅ Python version: {sys.version}")

        # Check required files
        required_files = [
            "pyproject.toml",
            "src/codename/__init__.py",
            "src/codename/py.typed",
            "README.md",
            "CHANGELOG.md"
        ]

        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                print(f"❌ Required file missing: {file_path}")
                return False
            print(f"✅ Found: {file_path}")

        # Check for git repository
        if not (self.project_root / ".git").exists():
            print("⚠️  Not a git repository - version detection may fail")

        print("✅ Environment validation passed")
        return True

    def run_tests(self, test_type: str = "all") -> bool:
        """Run tests."""
        test_commands = {
            "unit": ["pytest", "tests/unit", "-v"],
            "integration": ["pytest", "tests/integration", "-v"],
            "security": ["pytest", "tests/security", "-v", "-m", "security"],
            "performance": ["pytest", "tests/performance", "-v", "-m", "performance"],
            "all": ["pytest", "tests/", "-v"]
        }

        if test_type not in test_commands:
            print(f"❌ Unknown test type: {test_type}")
            return False

        return self.run_command(
            test_commands[test_type],
            f"Running {test_type} tests"
        )

    def run_linting(self) -> bool:
        """Run code linting."""
        print("🔍 Running code quality checks...")

        # Run ruff
        if not self.run_command(
            ["ruff", "check", "src/", "tests/"],
            "Running Ruff linting"
        ):
            return False

        # Run mypy
        if not self.run_command(
            ["mypy", "src/", "--strict"],
            "Running MyPy type checking"
        ):
            return False

        # Check formatting
        if not self.run_command(
            ["black", "--check", "src/", "tests/"],
            "Checking code formatting"
        ):
            return False

        print("✅ All linting checks passed")
        return True

    def run_security_checks(self) -> bool:
        """Run security checks."""
        print("🔒 Running security checks...")

        # Run bandit
        if not self.run_command(
            ["bandit", "-r", "src/"],
            "Running Bandit security scan"
        ):
            return False

        # Run safety
        if not self.run_command(
            ["safety", "check"],
            "Checking dependencies for vulnerabilities"
        ):
            return False

        print("✅ Security checks passed")
        return True

    def build_package(self) -> bool:
        """Build the package."""
        print("📦 Building package...")

        # Create dist directory
        self.dist_dir.mkdir(exist_ok=True)

        # Build with python -m build
        if not self.run_command(
            [sys.executable, "-m", "build"],
            "Building wheel and source distribution"
        ):
            return False

        # Verify build artifacts
        wheel_files = list(self.dist_dir.glob("*.whl"))
        tarball_files = list(self.dist_dir.glob("*.tar.gz"))

        if not wheel_files:
            print("❌ No wheel file created")
            return False

        if not tarball_files:
            print("❌ No source distribution created")
            return False

        print(f"✅ Built wheel: {wheel_files[0].name}")
        print(f"✅ Built source dist: {tarball_files[0].name}")

        return True

    def verify_package(self) -> bool:
        """Verify the built package."""
        print("🔍 Verifying package...")

        # Check with twine
        if not self.run_command(
            ["twine", "check", "dist/*"],
            "Verifying package with twine"
        ):
            return False

        print("✅ Package verification passed")
        return True

    def full_build(self, skip_tests: bool = False, skip_security: bool = False) -> bool:
        """Run the complete build process."""
        print("🚀 Starting full build process...")

        steps = [
            ("Environment validation", self.validate_environment),
            ("Clean", self.clean),
            ("Linting", self.run_linting),
        ]

        if not skip_tests:
            steps.append(("Tests", lambda: self.run_tests("all")))

        if not skip_security:
            steps.append(("Security checks", self.run_security_checks))

        steps.extend([
            ("Package build", self.build_package),
            ("Package verification", self.verify_package),
        ])

        for step_name, step_func in steps:
            print(f"\n{'='*50}")
            print(f"📋 Step: {step_name}")
            print('='*50)

            if not step_func():
                print(f"❌ Build failed at step: {step_name}")
                return False

        print(f"\n{'='*50}")
        print("🎉 Build completed successfully!")
        print('='*50)

        # Show build artifacts
        print("\n📦 Build artifacts:")
        for artifact in self.dist_dir.glob("*"):
            print(f"  {artifact.name}")

        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build script for Codename library")
    parser.add_argument(
        "command",
        nargs="?",
        default="build",
        choices=["clean", "test", "lint", "security", "build", "verify", "full"],
        help="Command to run"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip tests during full build"
    )
    parser.add_argument(
        "--skip-security",
        action="store_true",
        help="Skip security checks during full build"
    )
    parser.add_argument(
        "--test-type",
        default="all",
        choices=["unit", "integration", "security", "performance", "all"],
        help="Type of tests to run"
    )

    args = parser.parse_args()

    # Create build tool instance
    builder = CodenameBuildTool()

    # Execute command
    try:
        if args.command == "clean":
            success = builder.clean()
        elif args.command == "test":
            success = builder.run_tests(args.test_type)
        elif args.command == "lint":
            success = builder.run_linting()
        elif args.command == "security":
            success = builder.run_security_checks()
        elif args.command == "build":
            success = builder.build_package()
        elif args.command == "verify":
            success = builder.verify_package()
        elif args.command == "full":
            success = builder.full_build(
                skip_tests=args.skip_tests,
                skip_security=args.skip_security
            )
        else:
            print(f"❌ Unknown command: {args.command}")
            success = False

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n❌ Build interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Build failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

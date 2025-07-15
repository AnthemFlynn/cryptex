#!/usr/bin/env python3
"""
Validation script for Codename library.

This script validates project structure, configuration, and code quality.
"""

import subprocess
import sys
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import argparse
import json
import tomli


class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass


class CodenameValidationTool:
    """Validation tool for Codename library."""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.issues = []
        self.warnings = []
        
    def add_issue(self, severity: str, category: str, message: str, file_path: Optional[str] = None):
        """Add a validation issue."""
        issue = {
            "severity": severity,
            "category": category,
            "message": message,
            "file": file_path
        }
        
        if severity in ["error", "critical"]:
            self.issues.append(issue)
        else:
            self.warnings.append(issue)
    
    def run_command(self, command: List[str], description: str = "") -> Optional[subprocess.CompletedProcess]:
        """Run a command and return result."""
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True
            )
            return result
        except subprocess.CalledProcessError:
            return None
    
    def validate_project_structure(self) -> bool:
        """Validate project structure and required files."""
        print("🏗️  Validating project structure...")
        
        # Required files
        required_files = {
            "pyproject.toml": "Project configuration",
            "README.md": "Project documentation",
            "CHANGELOG.md": "Version history",
            "CONTRIBUTING.md": "Contribution guidelines",
            "SECURITY.md": "Security policy",
            "CODE_OF_CONDUCT.md": "Community guidelines",
            "AUTHORS.md": "Contributors list",
            ".gitignore": "Git ignore rules",
            ".editorconfig": "Editor configuration",
            ".pre-commit-config.yaml": "Pre-commit hooks",
            "src/codename/__init__.py": "Package initialization",
            "src/codename/py.typed": "Type hints marker",
        }
        
        for file_path, description in required_files.items():
            full_path = self.project_root / file_path
            if not full_path.exists():
                self.add_issue("error", "structure", f"Missing {description}: {file_path}")
            elif full_path.stat().st_size == 0:
                self.add_issue("warning", "structure", f"Empty file: {file_path}")
        
        # Required directories
        required_dirs = {
            "src/codename": "Main package directory",
            "tests": "Test directory", 
            "docs": "Documentation directory",
            "examples": "Example code directory",
            ".github/workflows": "CI/CD workflows",
            ".zed": "Zed editor configuration",
        }
        
        for dir_path, description in required_dirs.items():
            full_path = self.project_root / dir_path
            if not full_path.exists():
                self.add_issue("error", "structure", f"Missing {description}: {dir_path}")
            elif not full_path.is_dir():
                self.add_issue("error", "structure", f"Not a directory: {dir_path}")
        
        # Test structure validation
        test_dirs = ["unit", "integration", "security", "performance"]
        for test_dir in test_dirs:
            test_path = self.project_root / "tests" / test_dir
            if not test_path.exists():
                self.add_issue("warning", "tests", f"Missing test directory: tests/{test_dir}")
        
        return len([i for i in self.issues if i["category"] == "structure"]) == 0
    
    def validate_pyproject_toml(self) -> bool:
        """Validate pyproject.toml configuration."""
        print("📋 Validating pyproject.toml...")
        
        pyproject_path = self.project_root / "pyproject.toml"
        if not pyproject_path.exists():
            self.add_issue("critical", "config", "Missing pyproject.toml")
            return False
        
        try:
            with open(pyproject_path, "rb") as f:
                config = tomli.load(f)
        except Exception as e:
            self.add_issue("critical", "config", f"Invalid pyproject.toml: {e}")
            return False
        
        # Required sections
        required_sections = ["build-system", "project", "tool"]
        for section in required_sections:
            if section not in config:
                self.add_issue("error", "config", f"Missing section in pyproject.toml: {section}")
        
        # Project metadata validation
        if "project" in config:
            project = config["project"]
            
            required_fields = ["name", "description", "authors", "requires-python"]
            for field in required_fields:
                if field not in project:
                    self.add_issue("error", "config", f"Missing project field: {field}")
            
            # Version validation
            if "dynamic" in project and "version" in project["dynamic"]:
                # Check if version is in __init__.py
                init_file = self.project_root / "src" / "codename" / "__init__.py"
                if init_file.exists():
                    content = init_file.read_text()
                    if not re.search(r'__version__\s*=', content):
                        self.add_issue("error", "config", "Dynamic version specified but no __version__ in __init__.py")
            elif "version" not in project:
                self.add_issue("error", "config", "No version specified (static or dynamic)")
            
            # Dependencies validation
            if "dependencies" in project:
                deps = project["dependencies"]
                if not isinstance(deps, list):
                    self.add_issue("error", "config", "Dependencies must be a list")
                
                # Check for security dependencies
                security_deps = ["bandit", "safety"]
                dev_deps = project.get("optional-dependencies", {}).get("dev", [])
                for dep in security_deps:
                    if not any(dep in d for d in dev_deps):
                        self.add_issue("warning", "security", f"Missing security dependency: {dep}")
        
        # Tool configuration validation
        if "tool" in config:
            tools = config["tool"]
            
            # Check for required tools
            required_tools = ["pytest", "black", "ruff", "mypy", "bandit"]
            for tool in required_tools:
                if tool not in tools:
                    self.add_issue("warning", "config", f"Missing tool configuration: {tool}")
        
        return len([i for i in self.issues if i["category"] == "config"]) == 0
    
    def validate_package_imports(self) -> bool:
        """Validate that package imports work correctly."""
        print("📦 Validating package imports...")
        
        # Check main package import
        try:
            sys.path.insert(0, str(self.project_root / "src"))
            import codename
            
            # Check required exports
            required_exports = ["protect_secrets", "secure_session", "SecretManager"]
            for export in required_exports:
                if not hasattr(codename, export):
                    self.add_issue("error", "imports", f"Missing export: {export}")
            
            # Check version
            if not hasattr(codename, "__version__"):
                self.add_issue("error", "imports", "Missing __version__ attribute")
            elif not re.match(r'\d+\.\d+\.\d+', codename.__version__):
                self.add_issue("error", "imports", f"Invalid version format: {codename.__version__}")
                
        except ImportError as e:
            self.add_issue("critical", "imports", f"Failed to import main package: {e}")
            return False
        except Exception as e:
            self.add_issue("error", "imports", f"Import error: {e}")
            return False
        finally:
            if str(self.project_root / "src") in sys.path:
                sys.path.remove(str(self.project_root / "src"))
        
        return len([i for i in self.issues if i["category"] == "imports"]) == 0
    
    def validate_code_quality(self) -> bool:
        """Validate code quality with linting tools."""
        print("🔍 Validating code quality...")
        
        # Run ruff
        result = self.run_command(["ruff", "check", "src/", "tests/", "--output-format=json"])
        if result is None:
            self.add_issue("warning", "quality", "Could not run ruff (not installed?)")
        elif result.stdout:
            try:
                ruff_issues = json.loads(result.stdout)
                for issue in ruff_issues:
                    severity = "error" if issue.get("fix") is None else "warning"
                    self.add_issue(
                        severity, 
                        "quality",
                        f"Ruff: {issue.get('message', 'Unknown issue')}",
                        issue.get("filename")
                    )
            except json.JSONDecodeError:
                self.add_issue("warning", "quality", "Could not parse ruff output")
        
        # Run mypy
        result = self.run_command(["mypy", "src/", "--strict"])
        if result is None:
            self.add_issue("warning", "quality", "Could not run mypy (not installed?)")
        
        # Check formatting
        result = self.run_command(["black", "--check", "src/", "tests/"])
        if result is None:
            self.add_issue("warning", "quality", "Could not check formatting with black")
        
        return True
    
    def validate_security(self) -> bool:
        """Validate security configuration."""
        print("🔒 Validating security...")
        
        # Run bandit
        result = self.run_command(["bandit", "-r", "src/", "-f", "json"])
        if result and result.stdout:
            try:
                bandit_data = json.loads(result.stdout)
                for issue in bandit_data.get("results", []):
                    severity = issue.get("issue_severity", "medium").lower()
                    if severity in ["high", "medium"]:
                        self.add_issue(
                            "warning" if severity == "medium" else "error",
                            "security",
                            f"Bandit: {issue.get('issue_text', 'Security issue')}",
                            issue.get("filename")
                        )
            except json.JSONDecodeError:
                self.add_issue("warning", "security", "Could not parse bandit output")
        
        # Check for hardcoded secrets
        secret_patterns = [
            r'["\']sk-[a-zA-Z0-9]{20,}["\']',  # OpenAI API keys
            r'["\']sk-ant-[a-zA-Z0-9]{20,}["\']',  # Anthropic API keys
            r'password\s*=\s*["\'][^"\']+["\']',  # Password assignments
            r'secret\s*=\s*["\'][^"\']+["\']',  # Secret assignments
        ]
        
        for py_file in self.project_root.rglob("*.py"):
            if "examples" in str(py_file) or "tests" in str(py_file):
                continue  # Skip examples and tests
                
            try:
                content = py_file.read_text()
                for pattern in secret_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        self.add_issue(
                            "error",
                            "security", 
                            f"Potential hardcoded secret found",
                            str(py_file.relative_to(self.project_root))
                        )
            except Exception:
                continue
        
        return True
    
    def validate_tests(self) -> bool:
        """Validate test configuration and coverage."""
        print("🧪 Validating tests...")
        
        # Check if pytest is configured
        if not (self.project_root / "pyproject.toml").exists():
            return False
        
        # Run tests to check they pass
        result = self.run_command(["pytest", "tests/", "--collect-only", "-q"])
        if result is None:
            self.add_issue("warning", "tests", "Could not run pytest")
            return False
        
        # Count test files
        test_files = list(self.project_root.glob("tests/**/test_*.py"))
        if len(test_files) < 3:
            self.add_issue("warning", "tests", f"Only {len(test_files)} test files found")
        
        # Check for test markers
        pyproject_path = self.project_root / "pyproject.toml"
        try:
            with open(pyproject_path, "rb") as f:
                config = tomli.load(f)
            
            pytest_config = config.get("tool", {}).get("pytest", {}).get("ini_options", {})
            markers = pytest_config.get("markers", [])
            
            required_markers = ["security", "performance", "integration"]
            for marker in required_markers:
                if not any(marker in m for m in markers):
                    self.add_issue("warning", "tests", f"Missing test marker: {marker}")
                    
        except Exception:
            pass
        
        return True
    
    def validate_documentation(self) -> bool:
        """Validate documentation."""
        print("📚 Validating documentation...")
        
        # Check README content
        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            content = readme_path.read_text()
            
            required_sections = ["installation", "usage", "example"]
            for section in required_sections:
                if section.lower() not in content.lower():
                    self.add_issue("warning", "docs", f"README missing {section} section")
        
        # Check docs directory
        docs_dir = self.project_root / "docs"
        if docs_dir.exists():
            # Check for Sphinx config
            if not (docs_dir / "conf.py").exists():
                self.add_issue("warning", "docs", "Missing Sphinx configuration")
            
            # Check for index file
            index_files = list(docs_dir.glob("index.*"))
            if not index_files:
                self.add_issue("warning", "docs", "Missing documentation index file")
        
        return True
    
    def validate_ci_cd(self) -> bool:
        """Validate CI/CD configuration."""
        print("🔄 Validating CI/CD...")
        
        workflows_dir = self.project_root / ".github" / "workflows"
        if not workflows_dir.exists():
            self.add_issue("error", "ci", "Missing .github/workflows directory")
            return False
        
        # Check for required workflows
        required_workflows = ["ci.yml", "release.yml"]
        for workflow in required_workflows:
            workflow_path = workflows_dir / workflow
            if not workflow_path.exists():
                self.add_issue("error", "ci", f"Missing workflow: {workflow}")
        
        # Check workflow content
        ci_workflow = workflows_dir / "ci.yml"
        if ci_workflow.exists():
            content = ci_workflow.read_text()
            
            required_jobs = ["test", "lint", "security"]
            for job in required_jobs:
                if job not in content:
                    self.add_issue("warning", "ci", f"CI workflow missing {job} job")
        
        return True
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate validation report."""
        total_issues = len(self.issues)
        total_warnings = len(self.warnings)
        
        # Categorize issues
        categories = {}
        for issue in self.issues + self.warnings:
            category = issue["category"]
            if category not in categories:
                categories[category] = {"errors": 0, "warnings": 0, "items": []}
            
            if issue["severity"] in ["error", "critical"]:
                categories[category]["errors"] += 1
            else:
                categories[category]["warnings"] += 1
            
            categories[category]["items"].append(issue)
        
        return {
            "summary": {
                "total_issues": total_issues,
                "total_warnings": total_warnings,
                "categories_with_issues": len(categories),
                "validation_passed": total_issues == 0
            },
            "categories": categories,
            "issues": self.issues,
            "warnings": self.warnings
        }
    
    def run_full_validation(self) -> bool:
        """Run complete validation suite."""
        print("🔍 Running full project validation...")
        print("=" * 50)
        
        validators = [
            ("Project Structure", self.validate_project_structure),
            ("Configuration", self.validate_pyproject_toml),
            ("Package Imports", self.validate_package_imports),
            ("Code Quality", self.validate_code_quality),
            ("Security", self.validate_security),
            ("Tests", self.validate_tests),
            ("Documentation", self.validate_documentation),
            ("CI/CD", self.validate_ci_cd),
        ]
        
        for name, validator in validators:
            print(f"\n📋 {name}...")
            try:
                validator()
            except Exception as e:
                self.add_issue("error", name.lower().replace(" ", ""), f"Validation failed: {e}")
        
        return len(self.issues) == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validation script for Codename library")
    parser.add_argument(
        "command",
        nargs="?",
        default="all",
        choices=["all", "structure", "config", "imports", "quality", "security", "tests", "docs", "ci"],
        help="Validation to run"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Fail if warnings are found"
    )
    
    args = parser.parse_args()
    
    # Create validator instance
    validator = CodenameValidationTool()
    
    try:
        # Run validation
        if args.command == "all":
            success = validator.run_full_validation()
        elif args.command == "structure":
            success = validator.validate_project_structure()
        elif args.command == "config":
            success = validator.validate_pyproject_toml()
        elif args.command == "imports":
            success = validator.validate_package_imports()
        elif args.command == "quality":
            success = validator.validate_code_quality()
        elif args.command == "security":
            success = validator.validate_security()
        elif args.command == "tests":
            success = validator.validate_tests()
        elif args.command == "docs":
            success = validator.validate_documentation()
        elif args.command == "ci":
            success = validator.validate_ci_cd()
        else:
            print(f"❌ Unknown command: {args.command}")
            sys.exit(1)
        
        # Generate report
        report = validator.generate_report()
        
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            # Print summary
            print("\n" + "=" * 50)
            print("📊 VALIDATION SUMMARY")
            print("=" * 50)
            
            summary = report["summary"]
            print(f"Issues: {summary['total_issues']}")
            print(f"Warnings: {summary['total_warnings']}")
            print(f"Categories: {summary['categories_with_issues']}")
            
            # Print issues by category
            for category, data in report["categories"].items():
                if data["errors"] > 0 or data["warnings"] > 0:
                    print(f"\n📋 {category.upper()}:")
                    for item in data["items"]:
                        severity_icon = "❌" if item["severity"] in ["error", "critical"] else "⚠️"
                        file_info = f" ({item['file']})" if item.get("file") else ""
                        print(f"  {severity_icon} {item['message']}{file_info}")
            
            # Final result
            if summary["validation_passed"]:
                if summary["total_warnings"] == 0:
                    print(f"\n✅ Validation passed with no issues!")
                else:
                    print(f"\n✅ Validation passed with {summary['total_warnings']} warnings")
            else:
                print(f"\n❌ Validation failed with {summary['total_issues']} issues")
        
        # Exit code
        if not success:
            sys.exit(1)
        elif args.fail_on_warnings and report["summary"]["total_warnings"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n❌ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
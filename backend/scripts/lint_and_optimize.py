#!/usr/bin/env python3
"""
Code linting and optimization script for therapy-assistant-agent.
Runs multiple code quality tools and provides optimization recommendations.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any
import json


class CodeAnalyzer:
    """Runs code analysis tools and generates reports."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.app_dir = self.project_root / "app"
        self.results = {}
    
    def run_command(self, cmd: List[str], description: str) -> Dict[str, Any]:
        """Run a command and capture results."""
        print(f"\n🔍 {description}")
        print("=" * 60)
        print(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=self.project_root
            )
            
            return {
                "command": " ".join(cmd),
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
        except Exception as e:
            return {
                "command": " ".join(cmd),
                "return_code": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False
            }
    
    def run_black(self, fix: bool = False) -> Dict[str, Any]:
        """Run Black code formatter."""
        cmd = ["python", "-m", "black"]
        if not fix:
            cmd.append("--check")
        cmd.extend(["app", "tests", "scripts"])
        
        result = self.run_command(cmd, "Code Formatting (Black)")
        self.results["black"] = result
        return result
    
    def run_isort(self, fix: bool = False) -> Dict[str, Any]:
        """Run isort import sorter."""
        cmd = ["python", "-m", "isort"]
        if not fix:
            cmd.append("--check-only")
        cmd.extend(["app", "tests", "scripts"])
        
        result = self.run_command(cmd, "Import Sorting (isort)")
        self.results["isort"] = result
        return result
    
    def run_autoflake(self, fix: bool = False) -> Dict[str, Any]:
        """Run autoflake to remove unused imports."""
        cmd = [
            "python", "-m", "autoflake",
            "--remove-all-unused-imports",
            "--remove-unused-variables",
            "--remove-duplicate-keys",
            "--expand-star-imports",
            "--recursive"
        ]
        if fix:
            cmd.append("--in-place")
        cmd.extend(["app", "tests", "scripts"])
        
        result = self.run_command(cmd, "Remove Unused Imports (autoflake)")
        self.results["autoflake"] = result
        return result
    
    def run_flake8(self) -> Dict[str, Any]:
        """Run flake8 linter."""
        cmd = ["python", "-m", "flake8", "app", "tests", "scripts"]
        
        result = self.run_command(cmd, "Code Linting (flake8)")
        self.results["flake8"] = result
        return result
    
    def run_mypy(self) -> Dict[str, Any]:
        """Run mypy type checker."""
        cmd = ["python", "-m", "mypy", "app"]
        
        result = self.run_command(cmd, "Type Checking (mypy)")
        self.results["mypy"] = result
        return result
    
    def run_bandit(self) -> Dict[str, Any]:
        """Run bandit security linter."""
        cmd = [
            "python", "-m", "bandit", 
            "-r", "app",
            "-f", "json",
            "-x", "*/tests/*"
        ]
        
        result = self.run_command(cmd, "Security Analysis (bandit)")
        self.results["bandit"] = result
        
        # Parse JSON output for better reporting
        if result["success"] and result["stdout"]:
            try:
                bandit_data = json.loads(result["stdout"])
                result["issues"] = bandit_data.get("results", [])
                result["metrics"] = bandit_data.get("metrics", {})
            except json.JSONDecodeError:
                pass
        
        return result
    
    def run_safety(self) -> Dict[str, Any]:
        """Run safety dependency checker."""
        cmd = ["python", "-m", "safety", "check", "--json"]
        
        result = self.run_command(cmd, "Dependency Security (safety)")
        self.results["safety"] = result
        
        # Parse JSON output
        if result["stdout"]:
            try:
                safety_data = json.loads(result["stdout"])
                result["vulnerabilities"] = safety_data
            except json.JSONDecodeError:
                pass
        
        return result
    
    def run_complexity_analysis(self) -> Dict[str, Any]:
        """Analyze code complexity."""
        cmd = [
            "python", "-m", "radon", "cc", "app",
            "--min", "B",  # Show complexity B and above
            "--json"
        ]
        
        result = self.run_command(cmd, "Complexity Analysis (radon)")
        self.results["complexity"] = result
        
        # Parse complexity results
        if result["success"] and result["stdout"]:
            try:
                complexity_data = json.loads(result["stdout"])
                result["complex_functions"] = []
                
                for file_path, functions in complexity_data.items():
                    for func in functions:
                        if func.get("complexity", 0) > 10:  # High complexity
                            result["complex_functions"].append({
                                "file": file_path,
                                "function": func.get("name"),
                                "complexity": func.get("complexity"),
                                "line": func.get("lineno")
                            })
            except json.JSONDecodeError:
                pass
        
        return result
    
    def analyze_imports(self) -> Dict[str, Any]:
        """Analyze import usage and dependencies."""
        import ast
        from collections import defaultdict
        
        imports = defaultdict(list)
        unused_imports = []
        
        for py_file in self.app_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports[alias.name].append(str(py_file))
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        for alias in node.names:
                            full_name = f"{module}.{alias.name}" if module else alias.name
                            imports[full_name].append(str(py_file))
            
            except Exception as e:
                print(f"Warning: Could not analyze {py_file}: {e}")
        
        result = {
            "total_imports": len(imports),
            "most_used_imports": sorted(
                [(name, len(files)) for name, files in imports.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "success": True
        }
        
        self.results["imports"] = result
        return result
    
    def analyze_file_sizes(self) -> Dict[str, Any]:
        """Analyze file sizes and identify large files."""
        large_files = []
        total_lines = 0
        
        for py_file in self.app_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = len(f.readlines())
                
                total_lines += lines
                
                if lines > 500:  # Large file threshold
                    large_files.append({
                        "file": str(py_file),
                        "lines": lines
                    })
            
            except Exception as e:
                print(f"Warning: Could not analyze {py_file}: {e}")
        
        result = {
            "total_lines": total_lines,
            "large_files": sorted(large_files, key=lambda x: x["lines"], reverse=True),
            "success": True
        }
        
        self.results["file_sizes"] = result
        return result
    
    def generate_report(self) -> None:
        """Generate comprehensive analysis report."""
        print("\n" + "="*80)
        print("🎯 CODE QUALITY ANALYSIS REPORT")
        print("="*80)
        
        # Summary
        print("\n📊 SUMMARY")
        print("-" * 40)
        total_tools = len(self.results)
        successful_tools = sum(1 for r in self.results.values() if r.get("success", False))
        print(f"Tools run: {total_tools}")
        print(f"Successful: {successful_tools}")
        print(f"Failed: {total_tools - successful_tools}")
        
        # Formatting results
        if "black" in self.results:
            black_result = self.results["black"]
            if black_result["success"]:
                print("✅ Code formatting: PASSED")
            else:
                print(f"❌ Code formatting: FAILED ({black_result['stderr'][:100]}...)")
        
        # Import sorting
        if "isort" in self.results:
            isort_result = self.results["isort"]
            if isort_result["success"]:
                print("✅ Import sorting: PASSED")
            else:
                print("❌ Import sorting: FAILED")
        
        # Linting
        if "flake8" in self.results:
            flake8_result = self.results["flake8"]
            if flake8_result["success"]:
                print("✅ Linting: PASSED")
            else:
                violations = len(flake8_result["stdout"].split("\n"))
                print(f"❌ Linting: {violations} violations found")
        
        # Type checking
        if "mypy" in self.results:
            mypy_result = self.results["mypy"]
            if mypy_result["success"]:
                print("✅ Type checking: PASSED")
            else:
                errors = len(mypy_result["stdout"].split("\n"))
                print(f"❌ Type checking: {errors} errors found")
        
        # Security analysis
        if "bandit" in self.results:
            bandit_result = self.results["bandit"]
            if bandit_result["success"]:
                issues = len(bandit_result.get("issues", []))
                if issues == 0:
                    print("✅ Security analysis: PASSED")
                else:
                    print(f"⚠️  Security analysis: {issues} issues found")
            else:
                print("❌ Security analysis: FAILED")
        
        # Detailed findings
        print("\n🔍 DETAILED FINDINGS")
        print("-" * 40)
        
        # Complexity analysis
        if "complexity" in self.results:
            complexity_result = self.results["complexity"]
            complex_funcs = complexity_result.get("complex_functions", [])
            if complex_funcs:
                print(f"\n⚠️  HIGH COMPLEXITY FUNCTIONS ({len(complex_funcs)}):")
                for func in complex_funcs[:5]:  # Show top 5
                    print(f"  • {func['function']} in {func['file']} (complexity: {func['complexity']})")
        
        # Large files
        if "file_sizes" in self.results:
            file_result = self.results["file_sizes"]
            large_files = file_result.get("large_files", [])
            if large_files:
                print(f"\n📄 LARGE FILES ({len(large_files)}):")
                for file_info in large_files[:3]:  # Show top 3
                    print(f"  • {file_info['file']} ({file_info['lines']} lines)")
        
        # Security issues
        if "bandit" in self.results:
            bandit_result = self.results["bandit"]
            issues = bandit_result.get("issues", [])
            if issues:
                print(f"\n🔒 SECURITY ISSUES ({len(issues)}):")
                for issue in issues[:3]:  # Show top 3
                    print(f"  • {issue.get('test_name', 'Unknown')}: {issue.get('issue_text', '')[:60]}...")
        
        # Dependencies with vulnerabilities
        if "safety" in self.results:
            safety_result = self.results["safety"]
            vulnerabilities = safety_result.get("vulnerabilities", [])
            if vulnerabilities:
                print(f"\n🛡️  VULNERABLE DEPENDENCIES ({len(vulnerabilities)}):")
                for vuln in vulnerabilities[:3]:  # Show top 3
                    print(f"  • {vuln.get('package', 'Unknown')}: {vuln.get('vulnerability', '')[:60]}...")
        
        # Recommendations
        print("\n💡 OPTIMIZATION RECOMMENDATIONS")
        print("-" * 40)
        
        recommendations = []
        
        if "flake8" in self.results and not self.results["flake8"]["success"]:
            recommendations.append("Fix linting violations with: python -m flake8 app --extend-ignore=E501")
        
        if "black" in self.results and not self.results["black"]["success"]:
            recommendations.append("Format code with: python -m black app tests scripts")
        
        if "isort" in self.results and not self.results["isort"]["success"]:
            recommendations.append("Sort imports with: python -m isort app tests scripts")
        
        if "complexity" in self.results:
            complex_funcs = self.results["complexity"].get("complex_functions", [])
            if complex_funcs:
                recommendations.append(f"Refactor {len(complex_funcs)} high complexity functions")
        
        if "file_sizes" in self.results:
            large_files = self.results["file_sizes"].get("large_files", [])
            if large_files:
                recommendations.append(f"Consider splitting {len(large_files)} large files")
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
        else:
            print("🎉 No major issues found! Code quality looks good.")
        
        print("\n" + "="*80)


def main():
    """Main function to run code analysis."""
    parser = argparse.ArgumentParser(
        description="Code quality analysis and optimization tool"
    )
    parser.add_argument(
        "--fix", 
        action="store_true", 
        help="Automatically fix issues where possible"
    )
    parser.add_argument(
        "--skip-security", 
        action="store_true", 
        help="Skip security analysis (faster execution)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        help="Output report to JSON file"
    )
    
    args = parser.parse_args()
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    analyzer = CodeAnalyzer(str(project_root))
    
    print("🔍 Starting code quality analysis...")
    print(f"Project root: {project_root}")
    
    # Run analysis tools
    analyzer.run_black(fix=args.fix)
    analyzer.run_isort(fix=args.fix)
    analyzer.run_autoflake(fix=args.fix)
    analyzer.run_flake8()
    analyzer.run_mypy()
    
    if not args.skip_security:
        analyzer.run_bandit()
        analyzer.run_safety()
    
    analyzer.run_complexity_analysis()
    analyzer.analyze_imports()
    analyzer.analyze_file_sizes()
    
    # Generate report
    analyzer.generate_report()
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(analyzer.results, f, indent=2, default=str)
        print(f"\n📄 Results saved to: {args.output}")
    
    # Return appropriate exit code
    failed_tools = [
        name for name, result in analyzer.results.items() 
        if not result.get("success", False)
    ]
    
    if failed_tools:
        print(f"\n❌ Analysis completed with issues in: {', '.join(failed_tools)}")
        return 1
    else:
        print("\n✅ Analysis completed successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
"""Verification script to ensure all components are properly installed."""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check Python version."""
    print("[*] Checking Python version...")
    required = (3, 8)
    current = sys.version_info[:2]
    if current >= required:
        print(f"  [OK] Python {current[0]}.{current[1]} (required: {required[0]}.{required[1]}+)")
        return True
    else:
        print(f"  [FAIL] Python {current[0]}.{current[1]} (required: {required[0]}.{required[1]}+)")
        return False

def check_project_structure():
    """Check that all required directories exist."""
    print("\n[*] Checking project structure...")
    required_dirs = [
        'agents',
        'core',
        'config',
        'evaluation',
        'data',
        'data/documents',
        'data/vector_store',
        'tests',
        'logs',
        'docs'
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"  [OK] {dir_name}/")
        else:
            print(f"  [FAIL] {dir_name}/ (missing)")
            all_exist = False
    
    return all_exist

def check_required_files():
    """Check that all required Python files exist."""
    print("\n[*] Checking required files...")
    required_files = [
        'main.py',
        'requirements.txt',
        'README.md',
        'agents/base_agent.py',
        'agents/orchestrator_agent.py',
        'agents/retriever_agent.py',
        'agents/analyzer_agent.py',
        'agents/verifier_agent.py',
        'agents/memory_agent.py',
        'core/types.py',
        'core/document_manager.py',
        'core/orchestration.py',
        'config/settings.py',
        'evaluation/evaluation_system.py',
        'tests/test_agents.py',
        'docs/ARCHITECTURE.md',
        'docs/EVALUATION_GUIDE.md'
    ]
    
    all_exist = True
    for file_name in required_files:
        file_path = Path(file_name)
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"  [OK] {file_name} ({size} bytes)")
        else:
            print(f"  [FAIL] {file_name} (missing)")
            all_exist = False
    
    return all_exist

def check_dependencies():
    """Check if required Python packages can be imported."""
    print("\n[*] Checking dependencies...")
    packages = [
        'dataclasses',  # Built-in
        'asyncio',      # Built-in
        'pathlib',      # Built-in
    ]
    
    all_available = True
    for package in packages:
        try:
            __import__(package)
            print(f"  [OK] {package}")
        except ImportError:
            print(f"  [FAIL] {package} (not installed)")
            all_available = False
    
    # Check optional packages
    optional = ['chromadb', 'langchain', 'pydantic']
    print("\n  Optional packages (installed with requirements.txt):")
    for package in optional:
        try:
            __import__(package)
            print(f"    [OK] {package}")
        except ImportError:
            print(f"    [WARN] {package} (not yet installed)")
    
    return all_available

def check_code_quality():
    """Quick syntax check on Python files."""
    print("\n[*] Checking Python code syntax...")
    import py_compile
    
    python_files = list(Path('.').rglob('*.py'))
    errors = []
    
    for py_file in python_files:
        try:
            py_compile.compile(str(py_file), doraise=True)
            print(f"  [OK] {py_file}")
        except py_compile.PyCompileError as e:
            print(f"  [FAIL] {py_file}")
            errors.append((py_file, str(e)))
    
    return len(errors) == 0, errors

def print_summary(results):
    """Print verification summary."""
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    all_passed = all(results.values())
    
    for check, result in results.items():
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status}: {check}")
    
    print("="*60)
    
    if all_passed:
        print("\n[SUCCESS] All checks passed! System is ready to use.")
        print("\nNext steps:")
        print("  1. Run the application: python main.py")
        print("  2. Or run demo: python main.py --demo")
    else:
        print("\n[WARNING] Some checks failed. Please address the issues above.")
    
    return all_passed

def main():
    """Run all verification checks."""
    print("\n" + "="*60)
    print("SYSTEM VERIFICATION")
    print("="*60)
    
    results = {
        'Python Version': check_python_version(),
        'Project Structure': check_project_structure(),
        'Required Files': check_required_files(),
        'Core Dependencies': check_dependencies(),
    }
    
    # Check code quality
    code_ok, errors = check_code_quality()
    results['Code Syntax'] = code_ok
    
    # Print summary
    all_passed = print_summary(results)
    
    # Print file statistics
    print("\nPROJECT STATISTICS:")
    py_files = list(Path('.').rglob('*.py'))
    md_files = list(Path('.').rglob('*.md'))
    print(f"  Python files: {len(py_files)}")
    print(f"  Documentation files: {len(md_files)}")
    
    # Count lines of code
    total_lines = 0
    for py_file in py_files:
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                total_lines += len(f.readlines())
        except:
            pass
    print(f"  Total lines of code: {total_lines}")
    
    print("\n[OK] Verification complete!")
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())

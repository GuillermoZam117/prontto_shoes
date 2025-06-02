#!/usr/bin/env python
"""
Comprehensive test runner for the Django POS system
Includes unit tests, integration tests, and performance tests
"""
import os
import sys
import subprocess
import time
import json
from datetime import datetime

def run_command(command, description, timeout=300):
    """Run a command with timeout and capture output"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        execution_time = time.time() - start_time
        
        print(f"Exit code: {result.returncode}")
        print(f"Execution time: {execution_time:.2f}s")
        
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        
        return {
            'command': command,
            'description': description,
            'returncode': result.returncode,
            'execution_time': execution_time,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
    except subprocess.TimeoutExpired:
        print(f"Command timed out after {timeout} seconds")
        return {
            'command': command,
            'description': description,
            'returncode': -1,
            'execution_time': timeout,
            'stdout': '',
            'stderr': 'Command timed out'
        }
    except Exception as e:
        print(f"Error running command: {e}")
        return {
            'command': command,
            'description': description,
            'returncode': -1,
            'execution_time': 0,
            'stdout': '',
            'stderr': str(e)
        }

def main():
    """Main test runner function"""
    print("="*80)
    print("Django POS System - Comprehensive Test Suite")
    print("="*80)
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings_test')
    
    test_results = []
    
    # 1. Django system checks
    result = run_command(
        "python manage.py check",
        "Django System Checks",
        timeout=60
    )
    test_results.append(result)
    
    # 2. Database migrations check
    result = run_command(
        "python manage.py makemigrations --dry-run --check",
        "Database Migrations Check",
        timeout=60
    )
    test_results.append(result)
    
    # 3. Unit Tests - Individual Modules
    unit_test_modules = [
        "test_productos_models.py",
        "test_clientes_models.py", 
        "test_descuentos_models.py",
        "test_administracion_models.py",
        "test_inventario_models.py",
        "test_caja_models.py",
        "test_ventas_models.py"
    ]
    
    for module in unit_test_modules:
        result = run_command(
            f"python -m pytest tests/unit/{module} -v --tb=short",
            f"Unit Tests - {module}",
            timeout=120
        )
        test_results.append(result)
    
    # 4. Integration Tests
    result = run_command(
        "python -m pytest tests/integration/ -v --tb=short",
        "Integration Tests",
        timeout=300
    )
    test_results.append(result)
    
    # 5. Performance Tests
    result = run_command(
        "python -m pytest tests/performance/ -v --tb=short -m performance",
        "Performance Tests",
        timeout=600
    )
    test_results.append(result)
    
    # 6. Test Coverage Analysis
    result = run_command(
        "coverage run -m pytest tests/unit/ tests/integration/",
        "Coverage Analysis - Test Execution",
        timeout=600
    )
    test_results.append(result)
    
    result = run_command(
        "coverage report",
        "Coverage Report - Console",
        timeout=60
    )
    test_results.append(result)
    
    result = run_command(
        "coverage html",
        "Coverage Report - HTML Generation",
        timeout=60
    )
    test_results.append(result)
    
    # 7. Code Quality Checks (if available)
    try:
        result = run_command(
            "python -m flake8 --max-line-length=120 --exclude=migrations,venv,env .",
            "Code Quality - Flake8",
            timeout=120
        )
        test_results.append(result)
    except:
        print("Flake8 not available, skipping code quality check")
    
    # Generate test summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r['returncode'] == 0)
    failed_tests = total_tests - passed_tests
    
    print(f"Total test suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    # Detail failed tests
    if failed_tests > 0:
        print(f"\nFAILED TESTS:")
        for result in test_results:
            if result['returncode'] != 0:
                print(f"- {result['description']}")
                if result['stderr']:
                    print(f"  Error: {result['stderr'][:200]}...")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'summary': {
                'total': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': (passed_tests/total_tests)*100
            },
            'results': test_results
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: {results_file}")
    
    if failed_tests == 0:
        print("\n🎉 All tests passed successfully!")
        return 0
    else:
        print(f"\n❌ {failed_tests} test suite(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())

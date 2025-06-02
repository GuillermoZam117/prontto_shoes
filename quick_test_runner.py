#!/usr/bin/env python
"""
Quick test runner to identify working vs problematic tests
"""
import os
import sys
import subprocess
import time

def run_quick_test(module_name, timeout=30):
    """Run a single test module with timeout"""
    command = f"python -m pytest tests/unit/{module_name} -x --tb=line"
    
    print(f"Testing {module_name}...")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            # Count tests from output
            lines = result.stdout.split('\n')
            test_count = 0
            for line in lines:
                if ' passed' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'passed':
                            test_count = int(parts[i-1])
                            break
            
            print(f"  ✅ PASSED - {test_count} tests")
            return True, test_count
        else:
            print(f"  ❌ FAILED")
            if result.stderr:
                print(f"     Error: {result.stderr[:100]}...")
            return False, 0
            
    except subprocess.TimeoutExpired:
        print(f"  ⏱️ TIMEOUT (>{timeout}s)")
        return False, 0
    except Exception as e:
        print(f"  💥 ERROR: {e}")
        return False, 0

def main():
    """Run quick tests on all modules"""
    print("Django POS System - Quick Test Analysis")
    print("="*50)
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings_test')
    
    test_modules = [
        "test_productos_models.py",
        "test_clientes_models.py", 
        "test_descuentos_models.py",
        "test_administracion_models.py",
        "test_inventario_models.py",
        "test_caja_models.py",
        "test_ventas_models.py",
        "test_devoluciones_models.py",
        "test_proveedores_models.py",
        "test_tiendas_models.py"
    ]
    
    working_modules = []
    problem_modules = []
    total_test_count = 0
    
    for module in test_modules:
        success, count = run_quick_test(module)
        if success:
            working_modules.append((module, count))
            total_test_count += count
        else:
            problem_modules.append(module)
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    
    print(f"Working modules: {len(working_modules)}")
    for module, count in working_modules:
        print(f"  ✅ {module} ({count} tests)")
    
    print(f"\nProblem modules: {len(problem_modules)}")
    for module in problem_modules:
        print(f"  ❌ {module}")
    
    print(f"\nTotal working tests: {total_test_count}")
    
    # Run integration tests if unit tests are mostly working
    if len(working_modules) >= len(problem_modules):
        print("\nTesting integration tests...")
        success, count = run_quick_test("../integration/test_business_flows.py", timeout=60)
        if success:
            print(f"  ✅ Business flows integration tests ({count} tests)")
            total_test_count += count
        
        success, count = run_quick_test("../integration/test_api_endpoints.py", timeout=60)
        if success:
            print(f"  ✅ API endpoints integration tests ({count} tests)")
            total_test_count += count
    
    print(f"\nFinal total: {total_test_count} working tests")
    
    return len(problem_modules)

if __name__ == '__main__':
    sys.exit(main())

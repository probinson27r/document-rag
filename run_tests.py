#!/usr/bin/env python3
"""
Script to run tests from the tests directory
"""

import os
import sys
import subprocess

def run_test(test_name):
    """Run a specific test from the tests directory"""
    # Add the current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    # Change to tests directory and run the test
    tests_dir = os.path.join(current_dir, 'tests')
    test_file = os.path.join(tests_dir, test_name)
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"🧪 Running test: {test_name}")
    print("=" * 50)
    
    # Run the test
    result = subprocess.run([sys.executable, test_file], cwd=tests_dir)
    return result.returncode == 0

def list_tests():
    """List all available tests"""
    tests_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests')
    test_files = [f for f in os.listdir(tests_dir) if f.startswith('test_') and f.endswith('.py')]
    return sorted(test_files)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if not test_name.endswith('.py'):
            test_name += '.py'
        success = run_test(test_name)
        sys.exit(0 if success else 1)
    else:
        print("Available tests:")
        for test in list_tests():
            print(f"  {test}")
        print("\nUsage: python run_tests.py <test_name>")
        print("Example: python run_tests.py test_parallel_processing") 
#!/usr/bin/env python3
"""
Test Developer Agent with LLM Integration
Tests code fixing capabilities with 7 ESP32 error cases
"""

import asyncio
import time
import json
from typing import Dict, List, Any
from agent.code_fixer import create_code_fixer, ESP32CodeFixer
from agent.test_cases import ALL_TEST_CASES
from agent.llm_provider import LLMProvider


class DeveloperAgentTester:
    """Tests Developer Agent code fixing with LLM"""
    
    def __init__(self, provider: str = "ollama", model: str = None):
        """
        Initialize tester
        
        Args:
            provider: LLM provider (ollama, openai, anthropic)
            model: Specific model name (None = use recommended)
        """
        self.provider = provider
        self.model = model
        self.fixer = None
        self.results = []
        self.stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "low_confidence": 0,
            "total_duration": 0
        }
    
    def initialize(self):
        """Initialize code fixer"""
        print(f"\n🚀 Initializing Developer Agent")
        print(f"   Provider: {self.provider}")
        if self.model:
            print(f"   Model: {self.model}")
        
        try:
            self.fixer = create_code_fixer(self.provider, self.model)
            print("✅ Agent initialized successfully\n")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize: {e}\n")
            return False
    
    def test_single_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test a single error case
        
        Returns:
            Test result dictionary
        """
        print(f"{'='*70}")
        print(f"TEST: {test_case['name']}")
        print(f"{'='*70}")
        print(f"Description: {test_case['description']}")
        print(f"Difficulty: {test_case['difficulty']}")
        print(f"Error Type: {test_case['error_type']}")
        
        start_time = time.time()
        
        # Run fix
        fix_result = self.fixer.fix_code(
            buggy_code=test_case['buggy_code'],
            error_message=test_case.get('expected_error', 'Unknown error'),
            error_type=test_case.get('error_type', 'compilation_error'),
            filename=f"{test_case['name']}.c"
        )
        
        duration = time.time() - start_time
        
        # Validate fix
        validation = self.fixer.validate_fix(
            fix_result.original_code,
            fix_result.fixed_code if fix_result.fixed_code else "",
            test_case.get('correct_code')
        )
        
        # Determine if test passed
        passed = (
            fix_result.success and
            validation['code_changed'] and
            validation['has_includes'] and
            validation['similarity_score'] > 0.6  # At least 60% match
        )
        
        result = {
            "test_name": test_case['name'],
            "difficulty": test_case['difficulty'],
            "error_type": test_case['error_type'],
            "passed": passed,
            "success": fix_result.success,
            "confidence": fix_result.confidence,
            "diagnosis": fix_result.diagnosis,
            "changes_made": fix_result.changes_made,
            "validation": validation,
            "duration": duration,
            "error": fix_result.error
        }
        
        # Print result
        print(f"\n{'='*70}")
        if passed:
            print(f"✅ TEST PASSED")
            print(f"   Confidence: {fix_result.confidence}")
            print(f"   Similarity: {validation['similarity_score']*100:.1f}%")
        else:
            print(f"❌ TEST FAILED")
            if fix_result.error:
                print(f"   Error: {fix_result.error}")
            elif not validation['code_changed']:
                print(f"   Reason: Code not changed")
            else:
                print(f"   Reason: Low similarity ({validation['similarity_score']*100:.1f}%)")
        
        print(f"   Duration: {duration:.2f}s")
        print(f"{'='*70}\n")
        
        return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all test cases
        
        Returns:
            Complete test results
        """
        print(f"\n{'#'*70}")
        print(f"# DEVELOPER AGENT TEST SUITE")
        print(f"# Testing {len(ALL_TEST_CASES)} ESP32 error cases")
        print(f"{'#'*70}\n")
        
        start_time = time.time()
        
        # Run each test
        for i, test_case in enumerate(ALL_TEST_CASES, 1):
            print(f"\n[{i}/{len(ALL_TEST_CASES)}] Running test: {test_case['name']}")
            result = self.test_single_case(test_case)
            self.results.append(result)
            
            # Update stats
            self.stats['total'] += 1
            if result['passed']:
                self.stats['passed'] += 1
            else:
                self.stats['failed'] += 1
            
            # Count confidence levels
            if result['confidence'] == 'high':
                self.stats['high_confidence'] += 1
            elif result['confidence'] == 'medium':
                self.stats['medium_confidence'] += 1
            elif result['confidence'] == 'low':
                self.stats['low_confidence'] += 1
        
        self.stats['total_duration'] = time.time() - start_time
        
        return self.get_summary()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test summary"""
        success_rate = (self.stats['passed'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0
        
        summary = {
            "provider": self.provider,
            "model": self.model,
            "stats": self.stats,
            "success_rate": success_rate,
            "results": self.results
        }
        
        return summary
    
    def print_summary(self):
        """Print formatted test summary"""
        print(f"\n{'='*70}")
        print(f"TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Provider: {self.provider}")
        if self.model:
            print(f"Model: {self.model}")
        print(f"\nResults:")
        print(f"  Total Tests: {self.stats['total']}")
        print(f"  Passed: {self.stats['passed']} ✅")
        print(f"  Failed: {self.stats['failed']} ❌")
        print(f"  Success Rate: {self.stats['passed']/self.stats['total']*100:.1f}%")
        print(f"\nConfidence Levels:")
        print(f"  High: {self.stats['high_confidence']}")
        print(f"  Medium: {self.stats['medium_confidence']}")
        print(f"  Low: {self.stats['low_confidence']}")
        print(f"\nPerformance:")
        print(f"  Total Duration: {self.stats['total_duration']:.2f}s")
        print(f"  Avg per Test: {self.stats['total_duration']/self.stats['total']:.2f}s")
        print(f"{'='*70}\n")
        
        # Print results by difficulty
        print("Results by Difficulty:")
        for difficulty in ['easy', 'medium', 'hard']:
            results_by_diff = [r for r in self.results if r['difficulty'] == difficulty]
            if results_by_diff:
                passed = sum(1 for r in results_by_diff if r['passed'])
                total = len(results_by_diff)
                print(f"  {difficulty.capitalize()}: {passed}/{total} ({passed/total*100:.0f}%)")
        print()
        
        # Print results by error type
        print("Results by Error Type:")
        error_types = set(r['error_type'] for r in self.results)
        for error_type in error_types:
            results_by_type = [r for r in self.results if r['error_type'] == error_type]
            passed = sum(1 for r in results_by_type if r['passed'])
            total = len(results_by_type)
            print(f"  {error_type}: {passed}/{total} ({passed/total*100:.0f}%)")
        print()
    
    def save_results(self, filename: str = "developer_agent_test_results.json"):
        """Save results to JSON file"""
        summary = self.get_summary()
        
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"📊 Results saved to: {filename}")


def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Developer Agent with LLM")
    parser.add_argument(
        '--provider',
        choices=['ollama', 'openai', 'anthropic'],
        default='ollama',
        help='LLM provider to use'
    )
    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Specific model name (optional)'
    )
    parser.add_argument(
        '--case',
        type=str,
        default=None,
        help='Run specific test case only'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save results to JSON file'
    )
    
    args = parser.parse_args()
    
    # Create tester
    tester = DeveloperAgentTester(args.provider, args.model)
    
    # Initialize
    if not tester.initialize():
        return 1
    
    # Run tests
    if args.case:
        # Run specific case
        test_case = next((tc for tc in ALL_TEST_CASES if tc['name'] == args.case), None)
        if not test_case:
            print(f"❌ Test case '{args.case}' not found")
            print(f"Available: {', '.join(tc['name'] for tc in ALL_TEST_CASES)}")
            return 1
        
        result = tester.test_single_case(test_case)
        tester.results.append(result)
        tester.stats['total'] = 1
        tester.stats['passed'] = 1 if result['passed'] else 0
        tester.stats['failed'] = 0 if result['passed'] else 1
    else:
        # Run all tests
        tester.run_all_tests()
    
    # Print summary
    tester.print_summary()
    
    # Save results if requested
    if args.save:
        tester.save_results()
    
    # Return exit code based on success rate
    success_rate = (tester.stats['passed'] / tester.stats['total'] * 100)
    return 0 if success_rate >= 70 else 1


if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
Test LangExtract JSON parsing fix
"""

import os
import sys
import json
import re

def test_json_extraction():
    """Test the JSON extraction function with various response formats"""
    
    print("🧪 Testing LangExtract JSON Extraction")
    print("=" * 50)
    
    # Import the LangExtractChunker
    try:
        from langextract_chunking import LangExtractChunker
        chunker = LangExtractChunker()
        print("✅ LangExtractChunker initialized")
    except Exception as e:
        print(f"❌ Failed to initialize LangExtractChunker: {e}")
        return False
    
    # Test cases with different JSON response formats
    test_cases = [
        {
            "name": "Valid JSON object",
            "response": '{"extracted_components": [{"content": "test", "type": "section"}]}',
            "expected": True
        },
        {
            "name": "JSON with markdown code block",
            "response": 'Here is the analysis:\n```json\n{"extracted_components": [{"content": "test"}]}\n```',
            "expected": True
        },
        {
            "name": "JSON with single quotes",
            "response": "{'extracted_components': [{'content': 'test', 'type': 'section'}]}",
            "expected": True
        },
        {
            "name": "JSON with trailing comma",
            "response": '{"extracted_components": [{"content": "test", "type": "section",}]}',
            "expected": True
        },
        {
            "name": "JSON array only",
            "response": '[{"content": "test", "type": "section"}]',
            "expected": True
        },
        {
            "name": "Malformed JSON with extra text",
            "response": 'Here is the analysis: {"extracted_components": [{"content": "test"}]} and more text',
            "expected": True
        },
        {
            "name": "Invalid JSON",
            "response": 'This is not JSON at all',
            "expected": False
        }
    ]
    
    results = []
    for test_case in test_cases:
        try:
            result = chunker._extract_json_from_response(test_case["response"])
            success = result is not None
            results.append({
                "name": test_case["name"],
                "success": success,
                "expected": test_case["expected"],
                "passed": success == test_case["expected"]
            })
            
            status = "✅ PASS" if success == test_case["expected"] else "❌ FAIL"
            print(f"{status} {test_case['name']}: {'Extracted' if success else 'Failed to extract'}")
            
        except Exception as e:
            results.append({
                "name": test_case["name"],
                "success": False,
                "expected": test_case["expected"],
                "passed": False,
                "error": str(e)
            })
            print(f"❌ ERROR {test_case['name']}: {e}")
    
    # Summary
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    print(f"\n🎯 Test Results:")
    print("=" * 50)
    print(f"  Passed: {passed}/{total}")
    print(f"  Failed: {total - passed}/{total}")
    
    return passed == total

def test_clean_json_response():
    """Test the JSON cleaning function"""
    
    print(f"\n🧪 Testing JSON Response Cleaning")
    print("=" * 50)
    
    try:
        from langextract_chunking import LangExtractChunker
        chunker = LangExtractChunker()
        
        # Test cases
        test_cases = [
            {
                "name": "Remove extra text",
                "input": 'Here is the JSON: {"key": "value"} and more text',
                "expected": '{"key": "value"}'
            },
            {
                "name": "Fix single quotes",
                "input": "{'key': 'value'}",
                "expected": '{"key": "value"}'
            },
            {
                "name": "Fix trailing comma",
                "input": '{"key": "value",}',
                "expected": '{"key": "value"}'
            },
            {
                "name": "Fix unquoted keys",
                "input": '{key: "value"}',
                "expected": '{"key": "value"}'
            }
        ]
        
        results = []
        for test_case in test_cases:
            try:
                cleaned = chunker._clean_json_response(test_case["input"])
                # Try to parse the cleaned JSON
                json.loads(cleaned)
                results.append({
                    "name": test_case["name"],
                    "success": True
                })
                print(f"✅ PASS {test_case['name']}: Cleaned successfully")
            except Exception as e:
                results.append({
                    "name": test_case["name"],
                    "success": False,
                    "error": str(e)
                })
                print(f"❌ FAIL {test_case['name']}: {e}")
        
        passed = sum(1 for r in results if r["success"])
        total = len(results)
        
        print(f"\n🎯 Cleaning Results:")
        print("=" * 50)
        print(f"  Passed: {passed}/{total}")
        print(f"  Failed: {total - passed}/{total}")
        
        return passed == total
        
    except Exception as e:
        print(f"❌ Cleaning test failed: {e}")
        return False

def test_langextract_api_availability():
    """Test LangExtract API availability"""
    
    print(f"\n🧪 Testing LangExtract API Availability")
    print("=" * 50)
    
    try:
        from langextract_chunking import LangExtractChunker
        
        # Test with API enabled
        chunker = LangExtractChunker(use_langextract_api=True)
        print(f"✅ LangExtract API enabled: {chunker.langextract_available}")
        
        # Test dependencies
        try:
            import langchain_google_genai
            print("✅ langchain_google_genai available")
        except ImportError:
            print("❌ langchain_google_genai not available")
        
        try:
            from langchain_google_genai import GoogleGenerativeAI
            print("✅ GoogleGenerativeAI available")
        except ImportError:
            print("❌ GoogleGenerativeAI not available")
        
        return chunker.langextract_available
        
    except Exception as e:
        print(f"❌ API availability test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 LangExtract JSON Parsing Test")
    print("=" * 50)
    
    json_ok = test_json_extraction()
    cleaning_ok = test_clean_json_response()
    api_ok = test_langextract_api_availability()
    
    print(f"\n🎯 Overall Test Results:")
    print("=" * 50)
    print(f"  JSON Extraction: {'✅ OK' if json_ok else '❌ Issues'}")
    print(f"  JSON Cleaning: {'✅ OK' if cleaning_ok else '❌ Issues'}")
    print(f"  API Availability: {'✅ OK' if api_ok else '❌ Issues'}")
    
    if json_ok and cleaning_ok and api_ok:
        print(f"\n✅ LangExtract JSON parsing is working!")
        print(f"   The JSON parsing error should be resolved")
        print(f"   LangExtract should now handle malformed JSON responses")
    else:
        print(f"\n❌ Some LangExtract issues need to be resolved")
        print(f"   Check the error messages above")

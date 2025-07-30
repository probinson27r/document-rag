#!/usr/bin/env python3
"""
Test script for GPT-4 Enhanced Data Extraction

This script demonstrates the GPT-4 extraction capabilities by:
1. Testing text enhancement
2. Testing structured data extraction
3. Testing contract data extraction
4. Testing document summarization
"""

import os
import json
import requests
from gpt4_extraction import GPT4Extractor

def test_gpt4_extraction():
    """Test GPT-4 extraction capabilities"""
    
    print("🧪 Testing GPT-4 Enhanced Data Extraction")
    print("=" * 60)
    
    # Initialize GPT-4 extractor
    extractor = GPT4Extractor(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
        private_gpt4_url=os.getenv('PRIVATE_GPT4_URL'),
        private_gpt4_key=os.getenv('PRIVATE_GPT4_API_KEY')
    )
    
    # Sample document text
    sample_text = """
    CONTRACT AGREEMENT
    
    This agreement is made between ABC Company and XYZ Corporation.
    
    Effective Date: January 1, 2024
    Contract Value: $500,000
    
    Section 1: Services
    The vendor shall provide IT consulting services.
    
    Section 2: Payment Terms
    Payment shall be made within 30 days of invoice.
    
    Section 3: Deliverables
    - Monthly progress reports
    - Quarterly reviews
    - Annual assessments
    
    Contact: John Smith (john.smith@abc.com)
    Phone: (555) 123-4567
    """
    
    print(f"📄 Sample text length: {len(sample_text)} characters")
    print()
    
    # Test 1: Text Enhancement
    print("🔧 Test 1: Text Enhancement")
    print("-" * 30)
    try:
        result = extractor.enhance_text_extraction(sample_text, '.txt')
        if result.get("success"):
            enhanced_data = result.get("extracted_data", {})
            print(f"✅ Enhanced text length: {len(enhanced_data.get('enhanced_text', ''))}")
            print(f"✅ Quality score: {enhanced_data.get('quality_score', 0)}")
            print(f"✅ Document type: {enhanced_data.get('metadata', {}).get('document_type', 'Unknown')}")
        else:
            print(f"❌ Enhancement failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Enhancement error: {e}")
    print()
    
    # Test 2: Structured Data Extraction
    print("📊 Test 2: Structured Data Extraction")
    print("-" * 30)
    try:
        result = extractor.extract_structured_data(sample_text, ["dates", "names", "amounts", "contact_info"])
        if result.get("success"):
            data = result.get("extracted_data", {})
            print(f"✅ Dates found: {len(data.get('dates', []))}")
            print(f"✅ Names found: {len(data.get('names', []))}")
            print(f"✅ Amounts found: {len(data.get('amounts', []))}")
            print(f"✅ Contact info found: {len(data.get('contact_info', []))}")
        else:
            print(f"❌ Structured extraction failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Structured extraction error: {e}")
    print()
    
    # Test 3: Contract Data Extraction
    print("📋 Test 3: Contract Data Extraction")
    print("-" * 30)
    try:
        result = extractor.extract_legal_contract_data(sample_text)
        if result.get("success"):
            contract_data = result.get("extracted_data", {})
            contract_info = contract_data.get("contract_info", {})
            print(f"✅ Contract title: {contract_info.get('contract_title', 'Not found')}")
            print(f"✅ Parties: {len(contract_info.get('parties', []))}")
            print(f"✅ Effective date: {contract_info.get('effective_date', 'Not found')}")
            print(f"✅ Contract value: {contract_info.get('contract_value', 'Not found')}")
        else:
            print(f"❌ Contract extraction failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Contract extraction error: {e}")
    print()
    
    # Test 4: Document Summary
    print("📝 Test 4: Document Summary")
    print("-" * 30)
    try:
        result = extractor.generate_document_summary(sample_text, "key_points")
        if result.get("success"):
            summary_data = result.get("extracted_data", {})
            print(f"✅ Summary: {summary_data.get('summary', 'Not generated')[:100]}...")
            print(f"✅ Key points: {len(summary_data.get('key_points', []))}")
            print(f"✅ Main topics: {len(summary_data.get('main_topics', []))}")
        else:
            print(f"❌ Summary generation failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Summary generation error: {e}")
    print()
    
    # Test 5: Text Cleaning
    print("🧹 Test 5: Text Cleaning")
    print("-" * 30)
    try:
        result = extractor.clean_and_format_text(sample_text, preserve_structure=True)
        if result.get("success"):
            cleaned_data = result.get("extracted_data", {})
            print(f"✅ Cleaned text length: {len(cleaned_data.get('cleaned_text', ''))}")
            print(f"✅ Structure preserved: {cleaned_data.get('structure_preserved', False)}")
            print(f"✅ Quality improvement: {cleaned_data.get('quality_improvement', 0)}")
        else:
            print(f"❌ Text cleaning failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Text cleaning error: {e}")
    print()
    
    print("🎉 GPT-4 extraction testing completed!")

def test_api_endpoints():
    """Test the API endpoints for GPT-4 extraction"""
    
    print("\n🌐 Testing API Endpoints")
    print("=" * 60)
    
    base_url = "http://localhost:5001"
    
    # Test the test endpoint
    print("🔧 Testing /api/extract/test endpoint...")
    try:
        response = requests.post(f"{base_url}/api/extract/test")
        if response.status_code == 200:
            result = response.json()
            print("✅ Test endpoint working")
            print(f"✅ Results: {len(result.get('results', {}))} extraction types tested")
        else:
            print(f"❌ Test endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Test endpoint error: {e}")
    
    # Test custom extraction
    print("\n🔧 Testing /api/extract/gpt4 endpoint...")
    try:
        test_data = {
            "text": "Contract between ABC Corp and XYZ Ltd. Value: $100,000. Date: 2024-01-15.",
            "type": "structured",
            "data_types": ["dates", "names", "amounts"]
        }
        
        response = requests.post(f"{base_url}/api/extract/gpt4", json=test_data)
        if response.status_code == 200:
            result = response.json()
            print("✅ Custom extraction working")
            print(f"✅ Extraction type: {result.get('extraction_type')}")
            print(f"✅ Model used: {result.get('model')}")
        else:
            print(f"❌ Custom extraction failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Custom extraction error: {e}")

if __name__ == "__main__":
    # Test local extraction
    test_gpt4_extraction()
    
    # Test API endpoints
    test_api_endpoints() 
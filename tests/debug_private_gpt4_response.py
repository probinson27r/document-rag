#!/usr/bin/env python3
"""
Debug script to see the actual response format from Private GPT-4
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def debug_private_gpt4_chunking_response():
    """Debug the actual response from Private GPT-4 chunking"""
    
    print("🔍 Debugging Private GPT-4 Chunking Response")
    print("=" * 60)
    
    private_gpt4_url = os.getenv('PRIVATE_GPT4_URL', 'https://doe-srt-sensai-nprd-apim.azure-api.net/doe-srt-sensai-nprd-oai/openai/deployments/gpt-4o/chat/completions?api-version=2025-03-01-preview')
    private_gpt4_key = os.getenv('PRIVATE_GPT4_API_KEY')
    
    if not private_gpt4_key:
        print("❌ Private GPT-4 API key not found")
        return
    
    print(f"✅ Using Private GPT-4 URL: {private_gpt4_url[:50]}...")
    print(f"✅ Using Private GPT-4 Key: {private_gpt4_key[:10]}...")
    
    # Test text
    test_text = """
    CONTRACT AGREEMENT
    
    This agreement is made between ABC Company and XYZ Corporation on January 15, 2024.
    
    Section 1: Definitions
    1.1 "Vendor" means ABC Company
    1.2 "Client" means XYZ Corporation
    
    Section 2: Services
    2.1 The Vendor shall provide IT consulting services
    2.2 Services shall commence on January 1, 2024
    """
    
    # Create the chunking prompt (same as in gpt4_chunking.py)
    chunking_prompt = f"""
    You are an expert document chunking specialist. Split the following document into optimal chunks for RAG systems while preserving semantic meaning and document structure.

    Document to chunk:
    {test_text}

    Please split this document into chunks and return the result in the following JSON format:
    {{
        "chunks": [
            {{
                "chunk_id": "chunk_1",
                "content": "chunk content here",
                "start_position": 0,
                "end_position": 100,
                "chunk_type": "header",
                "section_number": "1",
                "section_title": "Definitions",
                "semantic_theme": "contract definitions",
                "quality_score": 0.9
            }}
        ],
        "summary": {{
            "total_chunks": 1,
            "average_chunk_size": 500,
            "semantic_coherence_score": 0.85,
            "structure_preservation_score": 0.88
        }}
    }}

    IMPORTANT: Return ONLY valid JSON. Do not include any additional text, explanations, or markdown formatting.
    """
    
    headers = {
        'Content-Type': 'application/json',
        'api-key': private_gpt4_key
    }
    
    data = {
        "messages": [
            {"role": "system", "content": "You are an expert document chunking specialist. Split documents into optimal chunks for RAG systems while preserving semantic meaning and document structure."},
            {"role": "user", "content": chunking_prompt}
        ],
        "max_tokens": 4000,
        "temperature": 0.1
    }
    
    print("\n📤 Sending chunking request to Private GPT-4...")
    print(f"📝 Prompt length: {len(chunking_prompt)} characters")
    
    try:
        response = requests.post(private_gpt4_url, headers=headers, json=data, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print(f"\n📥 Raw Response from Private GPT-4:")
            print("=" * 60)
            print(content)
            print("=" * 60)
            
            # Try to parse as JSON
            print(f"\n🔍 Attempting to parse as JSON...")
            try:
                parsed_json = json.loads(content)
                print("✅ JSON parsing successful!")
                print(f"📊 Parsed structure: {json.dumps(parsed_json, indent=2)}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                print(f"🔍 Response starts with: {content[:100]}...")
                print(f"🔍 Response ends with: ...{content[-100:]}")
                
                # Try to extract JSON from the response
                print(f"\n🔍 Attempting to extract JSON from response...")
                import re
                
                # Look for JSON-like content
                json_pattern = r'\{.*\}'
                matches = re.findall(json_pattern, content, re.DOTALL)
                
                if matches:
                    print(f"✅ Found {len(matches)} potential JSON blocks:")
                    for i, match in enumerate(matches):
                        print(f"\n--- JSON Block {i+1} ---")
                        print(match)
                        try:
                            parsed = json.loads(match)
                            print(f"✅ Block {i+1} is valid JSON!")
                        except:
                            print(f"❌ Block {i+1} is not valid JSON")
                else:
                    print("❌ No JSON-like content found in response")
                    
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_simplified_chunking_prompt():
    """Test with a simplified chunking prompt"""
    
    print("\n🔍 Testing Simplified Chunking Prompt")
    print("=" * 60)
    
    private_gpt4_url = os.getenv('PRIVATE_GPT4_URL', 'https://doe-srt-sensai-nprd-apim.azure-api.net/doe-srt-sensai-nprd-oai/openai/deployments/gpt-4o/chat/completions?api-version=2025-03-01-preview')
    private_gpt4_key = os.getenv('PRIVATE_GPT4_API_KEY')
    
    # Simplified prompt
    simplified_prompt = """
    Split this text into 2-3 chunks and return as JSON:
    
    "CONTRACT AGREEMENT
    
    This agreement is made between ABC Company and XYZ Corporation on January 15, 2024.
    
    Section 1: Definitions
    1.1 "Vendor" means ABC Company
    1.2 "Client" means XYZ Corporation
    
    Section 2: Services
    2.1 The Vendor shall provide IT consulting services
    2.2 Services shall commence on January 1, 2024"
    
    Return ONLY valid JSON in this format:
    {
        "chunks": [
            {
                "chunk_id": "chunk_1",
                "content": "chunk content",
                "chunk_type": "header"
            }
        ]
    }
    """
    
    headers = {
        'Content-Type': 'application/json',
        'api-key': private_gpt4_key
    }
    
    data = {
        "messages": [
            {"role": "system", "content": "You are a document chunking specialist. Return only valid JSON."},
            {"role": "user", "content": simplified_prompt}
        ],
        "max_tokens": 1000,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(private_gpt4_url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print(f"📥 Simplified Response:")
            print("=" * 60)
            print(content)
            print("=" * 60)
            
            try:
                parsed_json = json.loads(content)
                print("✅ Simplified prompt JSON parsing successful!")
            except json.JSONDecodeError as e:
                print(f"❌ Simplified prompt JSON parsing failed: {e}")
                
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    debug_private_gpt4_chunking_response()
    test_simplified_chunking_prompt() 
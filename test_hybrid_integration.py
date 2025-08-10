#!/usr/bin/env python3
"""
Test script to verify hybrid search integration with Flask app
"""

import requests
import json
import time

def test_hybrid_search():
    """Test the hybrid search functionality"""
    
    # Test data
    test_queries = [
        "What is Section 11.4 about?",
        "Section 11.4",
        "11.4",
        "No commitment",
        "Tell me about the no commitment section"
    ]
    
    print("Testing Hybrid Search Integration")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        
        # Test the query endpoint
        try:
            response = requests.post(
                'http://localhost:5001/query',
                json={'question': query},
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('answer', 'No answer')
                sources = result.get('sources', [])
                
                print(f"✅ Success!")
                print(f"Answer: {answer[:200]}...")
                print(f"Sources: {sources}")
                
                # Check if the answer mentions 11.4
                if '11.4' in answer or 'commitment' in answer.lower():
                    print("✅ Answer appears relevant!")
                else:
                    print("⚠️ Answer may not be relevant")
                    
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to Flask app (not running)")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(1)  # Small delay between requests

def test_chat_endpoint():
    """Test the chat endpoint with hybrid search"""
    
    print("\n\nTesting Chat Endpoint with Hybrid Search")
    print("=" * 50)
    
    test_message = "What is Section 11.4 about?"
    
    try:
        response = requests.post(
            'http://localhost:5001/chat',
            json={
                'message': test_message,
                'model': 'OpenAI GPT-5',
                'temperature': 0.7
            },
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('response', 'No response')
            sources = result.get('sources', [])
            
            print(f"✅ Chat Success!")
            print(f"Message: '{test_message}'")
            print(f"Response: {answer[:200]}...")
            print(f"Sources: {sources}")
            
            # Check if the answer mentions 11.4
            if '11.4' in answer or 'commitment' in answer.lower():
                print("✅ Response appears relevant!")
            else:
                print("⚠️ Response may not be relevant")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask app (not running)")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Hybrid Search Integration Test")
    print("Make sure your Flask app is running on localhost:5001")
    print("=" * 50)
    
    # Test query endpoint
    test_hybrid_search()
    
    # Test chat endpoint
    test_chat_endpoint()
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("\nTo run your Flask app:")
    print("python3 app.py")
    print("\nThen run this test again to verify the integration works.")

#!/usr/bin/env python3
"""
Test script to verify chat history API functionality
"""

import requests
import json
import time

def test_chat_history_api():
    """Test the chat history API to ensure user messages are being saved"""
    
    base_url = "http://localhost:5001"  # Change this to your server URL
    
    print("🧪 Testing Chat History API...")
    
    # Test 1: Clear existing history
    print("\n1. Clearing existing chat history...")
    try:
        response = requests.delete(f"{base_url}/api/chat/history")
        if response.status_code == 200:
            print("✅ Chat history cleared")
        else:
            print(f"❌ Failed to clear history: {response.status_code}")
    except Exception as e:
        print(f"❌ Error clearing history: {e}")
        return
    
    # Test 2: Get empty history
    print("\n2. Getting empty chat history...")
    try:
        response = requests.get(f"{base_url}/api/chat/history")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved {data['total_messages']} messages")
            if data['total_messages'] == 0:
                print("✅ History is empty as expected")
            else:
                print(f"⚠️ Unexpected: {data['total_messages']} messages found")
        else:
            print(f"❌ Failed to get history: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting history: {e}")
        return
    
    # Test 3: Save a user message
    print("\n3. Saving a user message...")
    user_message = {
        "id": "test_user_1",
        "sender": "user",
        "content": "This is a test user question",
        "sources": [],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/chat/history",
            headers={"Content-Type": "application/json"},
            data=json.dumps(user_message)
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ User message saved. Total messages: {data['total_messages']}")
        else:
            print(f"❌ Failed to save user message: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error saving user message: {e}")
        return
    
    # Test 4: Save an assistant message
    print("\n4. Saving an assistant message...")
    assistant_message = {
        "id": "test_assistant_1",
        "sender": "assistant",
        "content": "This is a test assistant response",
        "sources": ["test_source_1", "test_source_2"],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/chat/history",
            headers={"Content-Type": "application/json"},
            data=json.dumps(assistant_message)
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Assistant message saved. Total messages: {data['total_messages']}")
        else:
            print(f"❌ Failed to save assistant message: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error saving assistant message: {e}")
        return
    
    # Test 5: Get history and verify both messages
    print("\n5. Getting chat history to verify messages...")
    try:
        response = requests.get(f"{base_url}/api/chat/history")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved {data['total_messages']} messages")
            
            if data['total_messages'] == 2:
                print("✅ Correct number of messages found")
                
                # Check for user message
                user_messages = [msg for msg in data['history'] if msg['sender'] == 'user']
                if user_messages:
                    print(f"✅ Found {len(user_messages)} user message(s)")
                    for msg in user_messages:
                        print(f"   - User: {msg['content']}")
                else:
                    print("❌ No user messages found!")
                
                # Check for assistant message
                assistant_messages = [msg for msg in data['history'] if msg['sender'] == 'assistant']
                if assistant_messages:
                    print(f"✅ Found {len(assistant_messages)} assistant message(s)")
                    for msg in assistant_messages:
                        print(f"   - Assistant: {msg['content']}")
                else:
                    print("❌ No assistant messages found!")
                
            else:
                print(f"❌ Expected 2 messages, found {data['total_messages']}")
                print("History contents:")
                for i, msg in enumerate(data['history']):
                    print(f"   {i+1}. {msg['sender']}: {msg['content']}")
        else:
            print(f"❌ Failed to get history: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting history: {e}")
        return
    
    # Test 6: Export history
    print("\n6. Testing export functionality...")
    try:
        response = requests.get(f"{base_url}/api/chat/history/export")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Export successful. {data['total_messages']} messages exported")
            print(f"   Export timestamp: {data['exported_at']}")
        else:
            print(f"❌ Failed to export: {response.status_code}")
    except Exception as e:
        print(f"❌ Error exporting: {e}")
        return
    
    print("\n🎉 Chat History API Test Complete!")

if __name__ == "__main__":
    test_chat_history_api() 
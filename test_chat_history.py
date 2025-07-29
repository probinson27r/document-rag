#!/usr/bin/env python3
"""
Test script for chat history persistence functionality
"""

import requests
import json
import time

def test_chat_history_persistence():
    """Test the chat history persistence functionality"""
    base_url = "http://localhost:5001"
    
    print("🧪 Testing Chat History Persistence...")
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/api/status")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server is not responding properly")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start the Flask app first.")
        return False
    
    # Test 2: Get initial chat history
    try:
        response = requests.get(f"{base_url}/api/chat/history")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Initial chat history: {data['total_messages']} messages")
        else:
            print("❌ Failed to get initial chat history")
            return False
    except Exception as e:
        print(f"❌ Error getting chat history: {e}")
        return False
    
    # Test 3: Add a test message
    test_message = {
        "id": "test_msg_1",
        "sender": "user",
        "content": "This is a test message for persistence",
        "sources": [],
        "timestamp": "2024-01-01T12:00:00Z"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/chat/history",
            headers={"Content-Type": "application/json"},
            json=test_message
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Added test message. Total messages: {data['total_messages']}")
        else:
            print("❌ Failed to add test message")
            return False
    except Exception as e:
        print(f"❌ Error adding test message: {e}")
        return False
    
    # Test 4: Verify message was saved
    try:
        response = requests.get(f"{base_url}/api/chat/history")
        if response.status_code == 200:
            data = response.json()
            if data['total_messages'] > 0:
                print(f"✅ Message persisted. Total messages: {data['total_messages']}")
                print(f"   Last message: {data['history'][-1]['content']}")
            else:
                print("❌ Message was not persisted")
                return False
        else:
            print("❌ Failed to verify message persistence")
            return False
    except Exception as e:
        print(f"❌ Error verifying message persistence: {e}")
        return False
    
    # Test 5: Test export functionality
    try:
        response = requests.get(f"{base_url}/api/chat/history/export")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Export successful. Exported {data['total_messages']} messages")
        else:
            print("❌ Failed to export chat history")
            return False
    except Exception as e:
        print(f"❌ Error exporting chat history: {e}")
        return False
    
    # Test 6: Test clear functionality
    try:
        response = requests.delete(f"{base_url}/api/chat/history")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat history cleared. Total messages: {data['total_messages']}")
        else:
            print("❌ Failed to clear chat history")
            return False
    except Exception as e:
        print(f"❌ Error clearing chat history: {e}")
        return False
    
    # Test 7: Verify history is cleared
    try:
        response = requests.get(f"{base_url}/api/chat/history")
        if response.status_code == 200:
            data = response.json()
            if data['total_messages'] == 0:
                print("✅ Chat history successfully cleared")
            else:
                print("❌ Chat history was not cleared properly")
                return False
        else:
            print("❌ Failed to verify chat history clearance")
            return False
    except Exception as e:
        print(f"❌ Error verifying chat history clearance: {e}")
        return False
    
    print("\n🎉 All chat history persistence tests passed!")
    return True

if __name__ == "__main__":
    success = test_chat_history_persistence()
    if success:
        print("\n✅ Chat history persistence is working correctly!")
        print("💡 Users can now navigate between pages without losing their chat history.")
    else:
        print("\n❌ Chat history persistence tests failed!")
        print("🔧 Please check the server logs and ensure Flask-Session is properly configured.") 
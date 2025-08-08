# Chat History Persistence Feature

## Overview

The chat history persistence feature ensures that users' conversation history is maintained when they navigate between pages (e.g., from chat to configure and back). This prevents the frustrating experience of losing chat context when changing configuration settings.

## Features

### 🔄 **Persistent Storage**
- **Server-side sessions**: Chat history is stored in Flask sessions using Flask-Session
- **Local storage fallback**: Browser localStorage as backup for offline scenarios
- **Automatic sync**: History is synchronized between client and server

### 📱 **User Interface**
- **History menu**: Accessible via the "💬 History" button in the topbar
- **Export functionality**: Download chat history as JSON file
- **Import functionality**: Restore chat history from previously exported files
- **Clear history**: Remove all chat history with confirmation

### 🛡️ **Data Management**
- **Message limits**: Automatically keeps only the last 50 messages to prevent session bloat
- **Validation**: Ensures message format integrity
- **Error handling**: Graceful fallbacks when server is unavailable

## Technical Implementation

### Backend (Flask)

#### Session Configuration
```python
from flask_session import Session

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
```

#### API Endpoints
- `GET /api/chat/history` - Retrieve chat history
- `POST /api/chat/history` - Save new message
- `DELETE /api/chat/history` - Clear all history
- `GET /api/chat/history/export` - Export history as JSON
- `POST /api/chat/history/import` - Import history from JSON

#### Message Structure
```json
{
  "id": "msg_1234567890_abc123",
  "sender": "user|assistant",
  "content": "Message content",
  "sources": ["source1", "source2"],
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Frontend (JavaScript)

#### Storage Strategy
1. **Primary**: Server session storage
2. **Fallback**: Browser localStorage
3. **Sync**: Automatic synchronization between client and server

#### Key Functions
- `loadChatHistory()` - Load history from server/localStorage
- `addMessageToHistory()` - Add message to both client and server
- `renderChatHistory()` - Display all messages from history
- `exportChatHistory()` - Download history as JSON
- `importChatHistory()` - Import history from file

## Usage

### For Users

1. **Normal Usage**: Chat history is automatically saved and restored
2. **Export History**: Click "💬 History" → "📤 Export History"
3. **Import History**: Click "💬 History" → "📥 Import History"
4. **Clear History**: Click "💬 History" → "🗑️ Clear History"

### For Developers

#### Testing
```bash
# Run the test script
python test_chat_history.py
```

#### Manual Testing
1. Start the Flask app
2. Send a message in the chat
3. Navigate to configure page
4. Return to chat page
5. Verify message history is preserved

## Configuration

### Environment Variables
```bash
# Optional: Set a custom secret key for production
export SECRET_KEY="your-secure-secret-key"
```

### Dependencies
```
flask-session>=0.5.0
```

## Benefits

### ✅ **User Experience**
- No lost conversations when navigating
- Seamless configuration changes
- Persistent context across sessions

### ✅ **Developer Experience**
- Clean separation of concerns
- Robust error handling
- Easy testing and debugging

### ✅ **Data Integrity**
- Multiple storage layers
- Automatic validation
- Graceful degradation

## Troubleshooting

### Common Issues

1. **History not persisting**
   - Check if Flask-Session is installed
   - Verify session configuration
   - Check browser console for errors

2. **Import/Export not working**
   - Ensure file format is correct JSON
   - Check file permissions
   - Verify network connectivity

3. **Session storage issues**
   - Clear browser cache
   - Check server logs
   - Verify session directory permissions

### Debug Mode
Enable debug logging in the browser console to see detailed information about chat history operations.

## Future Enhancements

- [ ] Database storage for long-term persistence
- [ ] User authentication and per-user history
- [ ] Chat history search functionality
- [ ] Message threading and replies
- [ ] History analytics and insights 
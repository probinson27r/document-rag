# Private GPT-4 Setup Guide

This guide explains how to set up and use the Private GPT-4 model provider in the Legal Document RAG System.

## 🔧 Configuration

### 1. Environment Variable Setup

Set your Private GPT-4 API key as an environment variable:

```bash
export PRIVATE_GPT4_API_KEY="your-api-key-here"
```

For permanent setup, add this to your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
echo 'export PRIVATE_GPT4_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 2. API Endpoint Configuration

The system is pre-configured with your Azure OpenAI deployment endpoint:
- **URL**: `https://doe-srt-sensai-nprd-apim.azure-api.net/doe-srt-sensai-nprd-oai/openai/deployments/gpt-4o/chat/completions?api-version=2025-03-01-preview`
- **Model**: `gpt-4o`
- **Authentication**: API Key (via `api-key` header)

## 🧪 Testing the Integration

### Run the Test Script

```bash
python test_private_gpt4.py
```

This will test:
- ✅ Direct API connection
- ✅ App integration
- ✅ Authentication

### Expected Output

```
🧪 PRIVATE GPT-4 INTEGRATION TEST
==================================================
🔗 Testing Private GPT-4 connection...
✅ Private GPT-4 connection successful!
📝 Response: Private GPT-4 is working correctly!

🔧 Testing app integration...
✅ App integration successful - Private GPT-4 client initialized

==================================================
📊 TEST RESULTS:
API Connection: ✅ PASS
App Integration: ✅ PASS

🎉 All tests passed! Private GPT-4 integration is working correctly.
```

## 🚀 Using the Private GPT-4 Model

### 1. Start the Application

```bash
python app.py
```

### 2. Access the Web Interface

Open your browser and go to: `http://localhost:5000`

### 3. Select the Private GPT-4 Model

1. Navigate to the **Configure** page
2. In the **Model Selection** dropdown, you should see **"Private GPT-4"**
3. Select it and click **"Switch Model"**
4. The system will confirm the model switch

### 4. Start Querying Documents

1. Upload a legal document
2. Go to the **Chat** page
3. Ask questions about your document
4. The Private GPT-4 model will process your queries

## 🔍 Troubleshooting

### Issue: "Private GPT-4 not available"

**Solution**: Check your API key configuration
```bash
echo $PRIVATE_GPT4_API_KEY
```

### Issue: "API connection failed"

**Solutions**:
1. Verify your API key is correct
2. Check network connectivity to the Azure endpoint
3. Ensure the API key has proper permissions

### Issue: "Model not appearing in dropdown"

**Solution**: Restart the Flask application after setting the environment variable
```bash
# Stop the current app (Ctrl+C)
export PRIVATE_GPT4_API_KEY="your-key"
python app.py
```

### Issue: "Authentication error"

**Solutions**:
1. Verify the API key format
2. Check if the key has expired
3. Ensure the key has access to the specific deployment

## 📊 Model Comparison

| Feature | Private GPT-4 | OpenAI GPT-4 | Claude Sonnet 4 | Local Models |
|---------|---------------|--------------|-----------------|--------------|
| **Privacy** | ✅ Private deployment | ❌ Cloud-based | ❌ Cloud-based | ✅ Local |
| **Speed** | ⚡ Fast | ⚡ Fast | ⚡ Fast | 🐌 Slower |
| **Cost** | 💰 Variable | 💰 Per token | 💰 Per token | ✅ Free |
| **Customization** | ✅ Full control | ❌ Limited | ❌ Limited | ✅ Full control |
| **Reliability** | ✅ High | ✅ High | ✅ High | ⚠️ Variable |

## 🔒 Security Considerations

- **API Key Security**: Never commit your API key to version control
- **Environment Variables**: Use environment variables for sensitive configuration
- **Network Security**: The private deployment provides enhanced security
- **Data Privacy**: Your queries stay within your private infrastructure

## 📝 API Details

### Request Format

```json
{
  "model": "gpt-4o",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Your question here"}
  ],
  "max_tokens": 1000,
  "temperature": 0.7
}
```

### Headers

```
Content-Type: application/json
api-key: your-api-key-here
```

### Response Format

```json
{
  "choices": [
    {
      "message": {
        "content": "Response from GPT-4"
      }
    }
  ]
}
```

## 🆘 Support

If you encounter issues:

1. **Check the logs**: Look for error messages in the Flask application
2. **Run the test script**: `python test_private_gpt4.py`
3. **Verify configuration**: Ensure environment variables are set correctly
4. **Test connectivity**: Try a direct API call to verify endpoint access

## 📚 Additional Resources

- [Azure OpenAI Service Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Flask Environment Variables](https://flask.palletsprojects.com/en/2.0.x/config/) 
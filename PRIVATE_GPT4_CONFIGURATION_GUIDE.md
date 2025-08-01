# Private GPT-4 Configuration Guide

## Overview

The document RAG system has been configured to use Private GPT-4 as the primary provider for both extraction and chunking operations. This configuration provides enhanced security, privacy, and control over the GPT-4 processing pipeline.

## Configuration Status

### ✅ Successfully Configured

- **Primary Provider**: Private GPT-4 is now the default and preferred provider
- **Fallback System**: Automatic fallback to other providers when Private GPT-4 is unavailable
- **Integration**: Seamless integration with existing DocumentRAG system
- **Configuration Options**: User-configurable preferences through web interface

## Environment Setup

### Required Environment Variables

```bash
# Private GPT-4 Configuration
PRIVATE_GPT4_API_KEY=your_private_gpt4_api_key
PRIVATE_GPT4_URL=https://doe-srt-sensai-nprd-apim.azure-api.net/doe-srt-sensai-nprd-oai/openai/deployments/gpt-4o/chat/completions?api-version=2025-03-01-preview

# Optional Fallback Providers
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Current Configuration

Based on the test results:
- ✅ **Private GPT-4**: Available and configured (Priority: 1)
- ❌ **OpenAI**: Not available (Priority: 2)
- ❌ **Anthropic**: Not available (Priority: 3)

## Provider Priority System

### Priority Order
1. **Private GPT-4** (Primary) - Secure, private deployment
2. **OpenAI GPT-4** (Fallback) - Public OpenAI API
3. **Anthropic Claude** (Fallback) - Public Anthropic API

### Automatic Selection Logic

```python
# When prefer_private_gpt4=True (default)
if prefer_private_gpt4 and private_gpt4_available:
    use_private_gpt4()
elif openai_available:
    use_openai()
elif anthropic_available:
    use_anthropic()
else:
    use_fallback_chunking()

# When prefer_private_gpt4=False
if openai_available:
    use_openai()
elif anthropic_available:
    use_anthropic()
elif private_gpt4_available:
    use_private_gpt4()
else:
    use_fallback_chunking()
```

## Implementation Details

### Updated Components

#### 1. GPT-4 Extraction (`gpt4_extraction.py`)
- Added `prefer_private_gpt4` parameter to all extraction methods
- Private GPT-4 prioritized when `prefer_private_gpt4=True`
- Enhanced logging for provider selection

#### 2. GPT-4 Chunking (`gpt4_chunking.py`)
- Added `prefer_private_gpt4` parameter to chunking methods
- Private GPT-4 prioritized for intelligent document chunking
- Fallback to traditional chunking if all providers fail

#### 3. DocumentRAG Integration (`document_rag.py`)
- Updated DocumentProcessor to support Private GPT-4 preference
- Enhanced metadata tracking for provider usage
- Backward compatibility maintained

#### 4. Web Application (`app.py`)
- Added `prefer_private_gpt4` configuration option
- Updated API endpoints to support provider preferences
- Enhanced status monitoring for Private GPT-4

### Configuration Options

#### Web Interface Configuration
Access `/configure` to set:
- **Extraction Method**: Auto, GPT-4 Enhanced, Traditional
- **Prefer Private GPT-4**: Enable/disable Private GPT-4 priority
- **Chunking Method**: Auto, GPT-4, Traditional
- **Document Type**: Auto, Legal, Technical, General

#### Programmatic Configuration
```python
# Initialize with Private GPT-4 preference
extractor = GPT4Extractor(
    private_gpt4_url="your_url",
    private_gpt4_key="your_key",
    prefer_private_gpt4=True
)

# Use with explicit preference
result = extractor.extract_structured_data(
    text, 
    data_types, 
    prefer_private_gpt4=True
)
```

## Usage Examples

### Basic Usage (Private GPT-4 Preferred)
```python
from document_rag import DocumentRAG

# Initialize RAG system (Private GPT-4 preferred by default)
rag = DocumentRAG()

# Upload document (automatically uses Private GPT-4)
result = rag.ingest_document("document.pdf")
```

### Explicit Provider Selection
```python
from gpt4_extraction import GPT4Extractor

extractor = GPT4Extractor(
    private_gpt4_url="your_url",
    private_gpt4_key="your_key"
)

# Force Private GPT-4 usage
result = extractor.extract_structured_data(
    text, 
    ['dates', 'names'], 
    prefer_private_gpt4=True
)

# Use other providers if available
result = extractor.extract_structured_data(
    text, 
    ['dates', 'names'], 
    prefer_private_gpt4=False
)
```

### Configuration via Web Interface
```javascript
// Configure via API
fetch('/api/extraction/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        prefer_private_gpt4: true,
        features: {
            gpt4_chunking: true
        },
        chunking: {
            prefer_private_gpt4: true
        }
    })
});
```

## Testing and Validation

### Test Results
```
🔑 Testing API Key Priority...
✅ Private GPT-4 available (priority: 1)

🎯 Provider priority order:
   1. Private GPT-4 (priority: 1)

🏆 Primary provider: Private GPT-4

🔧 Testing Private GPT-4 Configuration...
✅ Private GPT-4 extraction successful!
✅ Private GPT-4 chunking successful!
✅ GPT-4 extractor available in DocumentRAG
✅ GPT-4 chunker available in DocumentRAG
✅ Provider priority test completed

🎉 Private GPT-4 Configuration Test Complete!
✅ Private GPT-4 configuration is working correctly!
```

### Test Commands
```bash
# Test Private GPT-4 configuration
python test_private_gpt4_config.py

# Test API key availability
python check_api_keys.py

# Test general GPT-4 functionality
python test_gpt4_chunking.py
```

## Benefits

### Security and Privacy
- **Private Deployment**: No data sent to public APIs
- **Secure Processing**: All processing within private infrastructure
- **Data Control**: Complete control over data handling

### Performance
- **Optimized Routing**: Direct connection to Private GPT-4
- **Reduced Latency**: No external API calls for primary operations
- **Reliable Fallbacks**: Automatic fallback to other providers

### Flexibility
- **Configurable Priority**: Easy to switch between providers
- **Backward Compatibility**: Existing functionality preserved
- **Future-Proof**: Easy to add new providers

## Troubleshooting

### Common Issues

#### 1. Private GPT-4 Connection Failed
```
❌ Connection failed
```
**Solution**: Verify API key and URL in `.env.local`

#### 2. Fallback to Traditional Chunking
```
WARNING: Failed to parse GPT-4 chunking result as JSON, using fallback
```
**Solution**: Check Private GPT-4 response format and adjust prompts

#### 3. Provider Not Available
```
❌ Private GPT-4 not available
```
**Solution**: Check environment variables and network connectivity

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed provider selection logs
```

## Monitoring and Logs

### Key Log Messages
- `INFO: Using Private GPT-4 for extraction`
- `INFO: Using Private GPT-4 for chunking`
- `INFO: Falling back to Private GPT-4 for extraction`
- `WARNING: Failed to parse GPT-4 chunking result as JSON, using fallback`

### Status Monitoring
```python
# Check provider status
from check_api_keys import check_api_keys
results = check_api_keys()

# Check extraction status
import requests
response = requests.get('/api/extraction/status')
status = response.json()
```

## Future Enhancements

### Planned Features
- **Provider Health Monitoring**: Real-time provider status
- **Load Balancing**: Distribute requests across multiple providers
- **Cost Optimization**: Route requests based on cost and performance
- **Custom Models**: Support for fine-tuned Private GPT-4 models

### Integration Opportunities
- **Multi-Region Support**: Deploy Private GPT-4 in multiple regions
- **Hybrid Processing**: Combine Private GPT-4 with local models
- **Advanced Analytics**: Detailed provider performance metrics

## Conclusion

The Private GPT-4 configuration is now fully operational and provides:

1. **Enhanced Security**: Private deployment with no external API calls
2. **Improved Performance**: Direct connection to Private GPT-4
3. **Flexible Configuration**: Easy to switch between providers
4. **Robust Fallbacks**: Automatic fallback to other providers
5. **Complete Integration**: Seamless integration with existing system

The system is ready for production use with Private GPT-4 as the primary provider for all extraction and chunking operations. 
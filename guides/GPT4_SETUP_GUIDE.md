# GPT-4 API Setup Guide

## Current Status

The GPT-4 extraction system is installed but not configured. You're seeing the warning:
```
WARNING:gpt4_extraction:No GPT-4 clients available - extraction will use fallback methods
```

## Required API Keys

To use GPT-4 enhanced extraction, you need at least one of these API keys:

### 1. OpenAI API Key (Recommended)
- **Get it from**: https://platform.openai.com/api-keys
- **Cost**: Pay-per-use (very reasonable for text processing)
- **Models**: GPT-4o, GPT-4

### 2. Anthropic API Key (Alternative)
- **Get it from**: https://console.anthropic.com/
- **Cost**: Pay-per-use
- **Models**: Claude 3.5 Sonnet

### 3. Private GPT-4 (Already Configured)
- **Status**: ✅ Already configured in your system
- **Key**: `1dba719f943748818dd22fcecedff284`
- **URL**: Azure endpoint

## Setup Instructions

### Step 1: Get API Keys

1. **For OpenAI**:
   - Go to https://platform.openai.com/api-keys
   - Sign up/login
   - Create a new API key
   - Copy the key (starts with `sk-`)

2. **For Anthropic**:
   - Go to https://console.anthropic.com/
   - Sign up/login
   - Create a new API key
   - Copy the key

### Step 2: Update Environment Variables

Edit your `.env.local` file and replace the placeholder values:

```bash
# Replace these placeholder values:
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# With your actual API keys:
OPENAI_API_KEY=sk-your_actual_openai_key_here
ANTHROPIC_API_KEY=sk-ant-your_actual_anthropic_key_here
```

### Step 3: Test Configuration

Run the test script to verify your setup:

```bash
python test_gpt4_extraction.py
```

## Alternative: Use Only Private GPT-4

If you don't want to set up additional API keys, you can use only the Private GPT-4 that's already configured:

1. Go to the **Configure** page
2. Set **Document Extraction Method** to **GPT-4 Enhanced**
3. Set **GPT-4 Model** to **GPT-4o** (this will use your Private GPT-4)
4. Test the configuration

## Cost Considerations

- **OpenAI GPT-4o**: ~$0.01 per 1K tokens (very cheap for text processing)
- **OpenAI GPT-4**: ~$0.03 per 1K tokens (higher quality)
- **Anthropic Claude**: ~$0.015 per 1K tokens
- **Private GPT-4**: Depends on your Azure subscription

For document processing, costs are typically very low (cents per document).

## Troubleshooting

### "No GPT-4 clients available"
- Check that API keys are properly set in `.env.local`
- Verify API keys are valid by testing them
- Restart the Flask application after updating keys

### "API key invalid"
- Ensure you copied the full API key
- Check for extra spaces or characters
- Verify the key hasn't expired

### "Rate limit exceeded"
- Wait a few minutes and try again
- Consider upgrading your API plan
- Use a different model temporarily

## Testing Your Setup

1. **Quick Test**: Run `python test_gpt4_extraction.py`
2. **Web Interface**: Go to Configure page and click "Test Extraction"
3. **Upload Test**: Upload a document and check if GPT-4 enhancement is applied

## Next Steps

Once configured:
1. Go to the **Configure** page
2. Select your preferred extraction method
3. Configure GPT-4 features
4. Test with a sample document
5. Start processing your documents with enhanced extraction! 
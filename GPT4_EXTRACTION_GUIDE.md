# GPT-4 Enhanced Data Extraction Guide

## Overview

This guide explains how to use GPT-4 for enhanced data extraction in the document RAG system. The GPT-4 extraction module provides advanced capabilities for improving document processing, extracting structured data, and generating summaries.

## Features

### 1. **Text Enhancement**
- Clean and format extracted text
- Preserve document structure and hierarchy
- Remove OCR artifacts and scanning errors
- Improve readability and formatting

### 2. **Structured Data Extraction**
- Extract dates, names, amounts, and key terms
- Identify contract terms and obligations
- Find contact information and references
- Extract legal contract data

### 3. **Document Summarization**
- Generate comprehensive summaries
- Create executive summaries
- Extract key points and findings
- Identify main topics and recommendations

### 4. **Contract Analysis**
- Extract contract information (parties, dates, values)
- Identify key terms and obligations
- Find risk factors and compliance requirements
- Analyze contract sections and clauses

## Setup

### 1. **API Keys Configuration**

The system supports multiple GPT-4 providers:

```bash
# OpenAI GPT-4
export OPENAI_API_KEY="your-openai-api-key"

# Anthropic Claude
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Private GPT-4 (Azure)
export PRIVATE_GPT4_URL="your-private-gpt4-url"
export PRIVATE_GPT4_API_KEY="your-private-gpt4-key"
```

### 2. **Dependencies**

The required dependencies are already included in `requirements.txt`:

```
openai
anthropic
requests
```

## Usage

### 1. **Direct Python Usage**

```python
from gpt4_extraction import GPT4Extractor

# Initialize extractor
extractor = GPT4Extractor(
    openai_api_key=os.getenv('OPENAI_API_KEY'),
    anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
    private_gpt4_url=os.getenv('PRIVATE_GPT4_URL'),
    private_gpt4_key=os.getenv('PRIVATE_GPT4_API_KEY')
)

# Text enhancement
result = extractor.enhance_text_extraction(raw_text, '.pdf')

# Structured data extraction
result = extractor.extract_structured_data(text, ['dates', 'names', 'amounts'])

# Contract analysis
result = extractor.extract_legal_contract_data(contract_text)

# Document summary
result = extractor.generate_document_summary(text, 'comprehensive')
```

### 2. **API Endpoints**

#### Test GPT-4 Extraction
```bash
curl -X POST http://localhost:5001/api/extract/test
```

#### Custom Extraction
```bash
curl -X POST http://localhost:5001/api/extract/gpt4 \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your document text here",
    "type": "structured",
    "data_types": ["dates", "names", "amounts"],
    "model": "gpt-4o"
  }'
```

### 3. **Extraction Types**

#### Text Enhancement
```json
{
  "text": "raw document text",
  "type": "enhance"
}
```

#### Structured Data Extraction
```json
{
  "text": "document text",
  "type": "structured",
  "data_types": ["dates", "names", "amounts", "contracts"]
}
```

#### Document Summary
```json
{
  "text": "document text",
  "type": "summary",
  "summary_type": "comprehensive"
}
```

#### Contract Analysis
```json
{
  "text": "contract text",
  "type": "contract"
}
```

#### Text Cleaning
```json
{
  "text": "document text",
  "type": "clean",
  "preserve_structure": true
}
```

## Integration with Document Processing

### 1. **Automatic Enhancement**

The GPT-4 extraction is automatically integrated into the document processing pipeline. When you upload a document, it will:

1. Extract raw text using traditional methods
2. Enhance the text using GPT-4 (if available)
3. Extract structured data
4. Store enhanced metadata

### 2. **Configuration**

You can control GPT-4 enhancement in the `DocumentProcessor`:

```python
# Enable GPT-4 enhancement (default)
processor = DocumentProcessor(use_gpt4_enhancement=True)

# Disable GPT-4 enhancement
processor = DocumentProcessor(use_gpt4_enhancement=False)
```

## Data Types for Structured Extraction

### Available Data Types

- **dates**: Dates, deadlines, time periods
- **names**: Person names, company names, organization names
- **amounts**: Monetary amounts, quantities, percentages
- **contracts**: Contract terms, clauses, obligations
- **contact_info**: Email addresses, phone numbers, addresses
- **references**: Document references, citations, cross-references
- **key_terms**: Important terms, definitions, acronyms

### Example Usage

```python
# Extract basic information
data_types = ["dates", "names", "amounts"]

# Extract legal contract information
data_types = ["dates", "names", "amounts", "contracts", "key_terms"]

# Extract contact information
data_types = ["names", "contact_info", "references"]
```

## Summary Types

### Available Summary Types

- **comprehensive**: Full document summary with details
- **executive**: High-level summary for decision-makers
- **key_points**: Bullet-point summary of main points

### Example Usage

```python
# Comprehensive summary
summary = extractor.generate_document_summary(text, "comprehensive")

# Executive summary
summary = extractor.generate_document_summary(text, "executive")

# Key points
summary = extractor.generate_document_summary(text, "key_points")
```

## Response Formats

### 1. **Text Enhancement Response**

```json
{
  "success": true,
  "extracted_data": {
    "enhanced_text": "cleaned and formatted text",
    "metadata": {
      "title": "document title",
      "author": "author if found",
      "date": "date if found",
      "document_type": "type of document",
      "purpose": "document purpose",
      "sections": ["list of main sections"],
      "tables": ["extracted table data"],
      "lists": ["extracted list data"]
    },
    "quality_score": 0.95,
    "processing_notes": "any notes about the processing"
  }
}
```

### 2. **Structured Data Response**

```json
{
  "success": true,
  "extracted_data": {
    "extracted_data": {
      "dates": ["list of dates found"],
      "names": ["list of names found"],
      "amounts": ["list of amounts found"],
      "contracts": ["list of contract terms"],
      "contact_info": ["list of contact information"],
      "references": ["list of references"],
      "key_terms": ["list of key terms"]
    },
    "confidence_scores": {
      "dates": 0.95,
      "names": 0.90,
      "amounts": 0.95,
      "contracts": 0.85,
      "contact_info": 0.90,
      "references": 0.80,
      "key_terms": 0.85
    },
    "processing_summary": "summary of what was extracted"
  }
}
```

### 3. **Contract Analysis Response**

```json
{
  "success": true,
  "extracted_data": {
    "contract_info": {
      "contract_title": "title of the contract",
      "parties": ["list of parties involved"],
      "effective_date": "effective date",
      "expiration_date": "expiration date",
      "contract_value": "total contract value",
      "contract_type": "type of contract"
    },
    "key_terms": {
      "obligations": ["list of key obligations"],
      "deliverables": ["list of deliverables"],
      "payment_terms": ["payment terms"],
      "termination_clauses": ["termination clauses"],
      "liability_terms": ["liability terms"]
    },
    "sections": {
      "section_1": {"title": "section title", "key_points": ["key points"]}
    },
    "risk_factors": ["list of risk factors"],
    "compliance_requirements": ["list of compliance requirements"],
    "extraction_confidence": 0.90
  }
}
```

## Testing

### 1. **Run Test Script**

```bash
python test_gpt4_extraction.py
```

This will test:
- Text enhancement
- Structured data extraction
- Contract analysis
- Document summarization
- Text cleaning
- API endpoints

### 2. **Test API Endpoints**

```bash
# Test with sample data
curl -X POST http://localhost:5001/api/extract/test

# Test custom extraction
curl -X POST http://localhost:5001/api/extract/gpt4 \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Contract between ABC Corp and XYZ Ltd. Value: $100,000. Date: 2024-01-15.",
    "type": "structured",
    "data_types": ["dates", "names", "amounts"]
  }'
```

## Error Handling

### Common Errors

1. **API Key Issues**
   - Check that API keys are properly set
   - Verify API key permissions and quotas

2. **Model Availability**
   - Ensure the requested model is available
   - Check API endpoint URLs for private GPT-4

3. **Rate Limiting**
   - Implement retry logic for rate-limited requests
   - Monitor API usage and quotas

### Error Response Format

```json
{
  "success": false,
  "error": "Error description",
  "extracted_data": {}
}
```

## Best Practices

### 1. **Text Length Management**
- GPT-4 has token limits (typically 4K-8K tokens)
- For long documents, consider chunking before extraction
- Use appropriate max_tokens parameter

### 2. **Model Selection**
- Use `gpt-4o` for general extraction (faster, cheaper)
- Use `gpt-4` for complex analysis (more accurate)
- Use `claude-3-5-sonnet-20241022` for alternative perspective

### 3. **Data Type Selection**
- Only extract needed data types to reduce costs
- Use specific data types for better accuracy
- Combine related data types for comprehensive analysis

### 4. **Error Handling**
- Always check for API errors
- Implement fallback mechanisms
- Log extraction results for debugging

## Performance Considerations

### 1. **Cost Optimization**
- Use appropriate model sizes
- Limit max_tokens where possible
- Cache extraction results

### 2. **Speed Optimization**
- Use async processing for multiple documents
- Implement parallel extraction for different data types
- Consider batch processing for large document sets

### 3. **Quality Optimization**
- Use specific prompts for better results
- Validate extraction results
- Implement confidence scoring

## Troubleshooting

### 1. **GPT-4 Not Available**
- Check API keys and permissions
- Verify network connectivity
- Check API service status

### 2. **Poor Extraction Quality**
- Review and refine prompts
- Check input text quality
- Try different models

### 3. **Rate Limiting**
- Implement exponential backoff
- Use multiple API keys
- Monitor usage patterns

## Future Enhancements

### Planned Features

1. **Batch Processing**: Process multiple documents simultaneously
2. **Custom Prompts**: Allow user-defined extraction prompts
3. **Result Validation**: Automatic validation of extracted data
4. **Caching**: Cache extraction results for improved performance
5. **Analytics**: Track extraction quality and performance metrics

### Integration Opportunities

1. **Document Classification**: Automatically classify document types
2. **Content Analysis**: Analyze document sentiment and tone
3. **Compliance Checking**: Check documents against compliance requirements
4. **Risk Assessment**: Automatically assess document risks
5. **Workflow Integration**: Integrate with document management workflows 
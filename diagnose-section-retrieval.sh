#!/bin/bash
# Diagnose Section 3.2 objectives retrieval issue
# Check if Section 3.2 content is properly chunked and indexed

set -e

echo "🔍 Diagnosing Section 3.2 objectives retrieval..."

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    if [ -d "venv" ]; then
        echo "📦 Activating virtual environment..."
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        echo "📦 Activating virtual environment..."
        source .venv/bin/activate
    else
        echo "❌ No virtual environment found. Please create one first."
        exit 1
    fi
fi

echo ""
echo "🔍 Step 1: Check ChromaDB collection contents..."

python << 'EOF'
import chromadb
import json

try:
    # Connect to ChromaDB
    client = chromadb.PersistentClient(
        path="./chroma_db",
        settings=chromadb.config.Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )
    
    collection = client.get_collection("documents")
    
    # Get all documents in the collection
    all_results = collection.get(include=['documents', 'metadatas', 'ids'])
    
    print(f"📊 Total chunks in collection: {len(all_results['ids'])}")
    
    # Search for Section 3.2 related chunks
    section_32_chunks = []
    objectives_chunks = []
    
    for i, (chunk_id, content, metadata) in enumerate(zip(
        all_results['ids'], 
        all_results['documents'], 
        all_results['metadatas']
    )):
        content_lower = content.lower()
        
        # Check for Section 3.2 references
        if '3.2' in content or 'section 3.2' in content_lower:
            section_32_chunks.append({
                'id': chunk_id,
                'content': content[:200] + '...' if len(content) > 200 else content,
                'metadata': metadata,
                'full_content': content
            })
        
        # Check for objectives content
        if 'objective' in content_lower and ('3.2' in content or any(word in content_lower for word in ['(a)', '(b)', '(c)', '(d)', '(e)'])):
            objectives_chunks.append({
                'id': chunk_id,
                'content': content[:200] + '...' if len(content) > 200 else content,
                'metadata': metadata,
                'full_content': content
            })
    
    print(f"🎯 Chunks containing '3.2': {len(section_32_chunks)}")
    print(f"🎯 Chunks containing objectives: {len(objectives_chunks)}")
    
    print("\n📋 Section 3.2 chunks:")
    for i, chunk in enumerate(section_32_chunks):
        print(f"  {i+1}. ID: {chunk['id']}")
        print(f"     Section: {chunk['metadata'].get('section_number', 'Unknown')}")
        print(f"     Title: {chunk['metadata'].get('section_title', 'Unknown')}")
        print(f"     Content: {chunk['content']}")
        print()
    
    print("\n📋 Objectives chunks:")
    for i, chunk in enumerate(objectives_chunks):
        print(f"  {i+1}. ID: {chunk['id']}")
        print(f"     Section: {chunk['metadata'].get('section_number', 'Unknown')}")
        print(f"     Title: {chunk['metadata'].get('section_title', 'Unknown')}")
        print(f"     Content: {chunk['content']}")
        print()
    
    # Save detailed analysis for further inspection
    analysis = {
        'total_chunks': len(all_results['ids']),
        'section_32_chunks': len(section_32_chunks),
        'objectives_chunks': len(objectives_chunks),
        'section_32_details': section_32_chunks,
        'objectives_details': objectives_chunks
    }
    
    with open('section_32_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"💾 Detailed analysis saved to 'section_32_analysis.json'")
    
except Exception as e:
    print(f"❌ Error accessing ChromaDB: {e}")
    import traceback
    traceback.print_exc()
EOF

echo ""
echo "🔍 Step 2: Test hybrid search directly..."

python << 'EOF'
try:
    from hybrid_search import HybridSearch
    
    # Initialize hybrid search
    hybrid_search = HybridSearch()
    
    # Test queries
    test_queries = [
        "Section 3.2",
        "objectives in Section 3.2", 
        "Section 3.2 objectives",
        "3.2 objectives",
        "Give me the objectives in Section 3.2"
    ]
    
    print("🧪 Testing hybrid search queries:")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        
        # Check query classification
        is_list = hybrid_search.is_list_query(query)
        is_objectives = hybrid_search.is_objectives_query(query)
        section_numbers = hybrid_search.extract_section_numbers(query)
        
        print(f"   List query: {is_list}")
        print(f"   Objectives query: {is_objectives}")
        print(f"   Section numbers: {section_numbers}")
        
        # Run search
        results = hybrid_search.search_with_fallback(query, n_results=5)
        
        print(f"   Results found: {len(results)}")
        
        for i, result in enumerate(results):
            contains_32 = '3.2' in result['text']
            contains_objectives = 'objective' in result['text'].lower()
            relevance = '✅ RELEVANT' if (contains_32 and contains_objectives) else '❌ NOT RELEVANT'
            score = result.get('combined_score', 1.0 - result.get('distance', 1.0))
            
            print(f"   {i+1}. Score: {score:.4f} | {relevance}")
            print(f"      Type: {result.get('search_type', 'unknown')}")
            print(f"      Text: {result['text'][:150]}...")
            
            if contains_32:
                print(f"      ✅ Contains '3.2'")
            if contains_objectives:
                print(f"      ✅ Contains 'objectives'")
            print()

except Exception as e:
    print(f"❌ Error testing hybrid search: {e}")
    import traceback
    traceback.print_exc()
EOF

echo ""
echo "🔍 Step 3: Check document processing and chunking..."

python << 'EOF'
import os
import glob

# Check for uploaded PDF files
pdf_files = glob.glob("uploads/*.pdf")
print(f"📁 PDF files in uploads: {len(pdf_files)}")

for pdf_file in pdf_files[:3]:  # Check first 3 files
    print(f"   - {os.path.basename(pdf_file)}")

# Check if there are any documents that might contain Section 3.2
if pdf_files:
    print(f"\n📄 Checking if any uploaded documents contain Section 3.2...")
    
    # Try to extract text from one PDF to see if Section 3.2 is there
    try:
        import pdfplumber
        
        sample_pdf = pdf_files[0]
        print(f"🔍 Analyzing: {os.path.basename(sample_pdf)}")
        
        with pdfplumber.open(sample_pdf) as pdf:
            all_text = ""
            for page in pdf.pages:
                all_text += page.extract_text() or ""
            
            # Search for Section 3.2
            if '3.2' in all_text:
                print("✅ Found '3.2' in the document")
                
                # Find context around 3.2
                lines = all_text.split('\n')
                section_32_lines = []
                
                for i, line in enumerate(lines):
                    if '3.2' in line:
                        # Get context around this line
                        start = max(0, i-3)
                        end = min(len(lines), i+10)
                        context = lines[start:end]
                        section_32_lines.extend(context)
                
                print(f"📋 Section 3.2 context (first 1000 chars):")
                context_text = '\n'.join(section_32_lines)
                print(context_text[:1000])
                
                if 'objective' in context_text.lower():
                    print("✅ Found 'objectives' near Section 3.2")
                else:
                    print("❌ No 'objectives' found near Section 3.2")
                    
            else:
                print("❌ No '3.2' found in the document")
                
    except Exception as e:
        print(f"❌ Error analyzing PDF: {e}")
else:
    print("❌ No PDF files found in uploads directory")
EOF

echo ""
echo "🎯 Diagnosis completed!"
echo ""
echo "📋 Next steps:"
echo "1. Check section_32_analysis.json for detailed chunk analysis"
echo "2. If Section 3.2 is missing from chunks, the issue is in document processing"
echo "3. If Section 3.2 chunks exist but queries fail, the issue is in search logic"
echo "4. If documents don't contain Section 3.2, you may need to upload the correct document"

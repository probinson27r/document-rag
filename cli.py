#!/usr/bin/env python3
"""
Command Line Interface for Document RAG System
Usage: python3 cli.py [command] [options]
"""

import argparse
import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Import our RAG system
from document_rag import DocumentRAG

def setup_rag():
    """Initialize the RAG system and check status"""
    rag = DocumentRAG()
    status = rag.check_setup()
    
    if not all(status.values()):
        print("⚠️  System Status Issues:")
        for component, is_ok in status.items():
            icon = "✓" if is_ok else "✗"
            print(f"  {icon} {component}")
        
        if not status['ollama_available']:
            print("\n🔧 To fix: Start Ollama with Docker:")
            print("   docker run -d -v ~/.ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama")
        
        if not status['model_available']:
            print(f"\n🔧 To fix: Pull the model:")
            print(f"   docker exec -it ollama ollama pull {rag.model_name}")
        
        print()
    
    return rag, all(status.values())

def cmd_status(args):
    """Show system status"""
    rag, is_ready = setup_rag()
    
    print("🚀 Document RAG System Status")
    print("=" * 40)
    
    # System components
    setup_status = rag.check_setup()
    for component, status in setup_status.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {component.replace('_', ' ').title()}")
    
    if is_ready:
        print("\n📋 System Information:")
        
        # Current model
        print(f"🤖 Current Model: {rag.model_name}")
        
        # Available models
        try:
            models = rag.ollama_client.list_models()
            print(f"📚 Available Models ({len(models)}):")
            for model in models:
                current = " ← CURRENT" if model == rag.model_name else ""
                print(f"   • {model}{current}")
        except Exception as e:
            print(f"❌ Could not fetch available models: {e}")
        
        # Document count
        docs = rag.list_documents()
        print(f"📄 Documents in Database: {len(docs)}")
        
        # ChromaDB info
        try:
            total_chunks = sum(doc.get('total_chunks', 0) for doc in docs)
            print(f"🧩 Total Document Chunks: {total_chunks}")
        except:
            pass
        
        # Model info
        print(f"🔧 Chunk Size: {rag.chunk_size}")
        print(f"🔧 Chunk Overlap: {rag.chunk_overlap}")
        
    else:
        print("\n❌ System not ready")
        if not setup_status['ollama_available']:
            print("💡 Start Ollama: docker run -d -v ~/.ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama")
        if not setup_status['model_available']:
            print(f"💡 Pull model: docker exec -it ollama ollama pull {rag.model_name}")
        
        return 1
    
    return 0

def cmd_ingest(args):
    """Ingest documents"""
    rag, is_ready = setup_rag()
    if not is_ready:
        print("❌ System not ready. Run 'status' command for details.")
        return 1
    
    if args.directory:
        print(f"📁 Ingesting documents from: {args.directory}")
        results = rag.ingest_directory(args.directory)
        for result in results:
            print(f"  {result}")
    elif args.file:
        print(f"📄 Ingesting document: {args.file}")
        
        # Check if it's a PDF and if password is needed
        pdf_password = None
        if args.file.lower().endswith('.pdf') and args.password:
            pdf_password = args.password
        elif args.file.lower().endswith('.pdf') and not args.password:
            # Try without password first
            result = rag.ingest_document(args.file)
            if "password-protected" in result.lower():
                import getpass
                print("🔒 This PDF appears to be password-protected.")
                pdf_password = getpass.getpass("Enter PDF password (input hidden): ")
        
        if pdf_password:
            result = rag.ingest_document(args.file, pdf_password=pdf_password)
        else:
            result = rag.ingest_document(args.file)
        
        print(f"  {result}")
    else:
        print("❌ Please specify either --file or --directory")
        return 1
    
    return 0

def cmd_query(args):
    """Query documents"""
    rag, is_ready = setup_rag()
    if not is_ready:
        print("❌ System not ready. Run 'status' command for details.")
        return 1
    
    question = args.question
    if not question:
        # Interactive mode
        print("🤖 Interactive Query Mode (type 'quit' to exit)")
        print("=" * 50)
        
        while True:
            try:
                question = input("\n❓ Your question: ").strip()
                if question.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not question:
                    continue
                
                print("🔍 Searching documents...")
                result = rag.query(question, n_results=args.results)
                
                print(f"\n💡 Answer:")
                print(result['answer'])
                
                if result['sources']:
                    print(f"\n📚 Sources:")
                    for source in result['sources']:
                        print(f"  • {source}")
                
                if args.verbose and result['context_used']:
                    print(f"\n🔍 Context used:")
                    for i, context in enumerate(result['context_used'][:2], 1):
                        print(f"  {i}. {context}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    else:
        # Single query mode
        print(f"❓ Question: {question}")
        print("🔍 Searching documents...")
        
        result = rag.query(question, n_results=args.results)
        
        print(f"\n💡 Answer:")
        print(result['answer'])
        
        if result['sources']:
            print(f"\n📚 Sources:")
            for source in result['sources']:
                print(f"  • {source}")
        
        if args.verbose:
            print(f"\n🔍 Search Results:")
            for i, search_result in enumerate(result['search_results'][:3], 1):
                print(f"  {i}. {search_result['metadata']['filename']} (distance: {search_result['distance']:.3f})")
                print(f"     {search_result['document'][:100]}...")
    
    return 0

def cmd_list(args):
    """List documents"""
    rag, is_ready = setup_rag()
    if not is_ready:
        print("❌ System not ready. Run 'status' command for details.")
        return 1
    
    docs = rag.list_documents()
    
    if not docs:
        print("📭 No documents in database")
        return 0
    
    print(f"📚 Documents in database ({len(docs)}):")
    print("-" * 80)
    
    for doc in docs:
        print(f"📄 {doc['filename']}")
        print(f"   Type: {doc['file_type']} | Chunks: {doc['total_chunks']}")
        print(f"   Path: {doc['filepath']}")
        print(f"   Processed: {doc['processed_time']}")
        if args.verbose:
            print(f"   Full path: {doc['filepath']}")
        print()
    
    return 0

def cmd_delete(args):
    """Delete documents"""
    rag, is_ready = setup_rag()
    if not is_ready:
        print("❌ System not ready. Run 'status' command for details.")
        return 1
    
    if args.all:
        # Delete all documents
        docs = rag.list_documents()
        if not docs:
            print("📭 No documents to delete")
            return 0
        
        confirm = input(f"⚠️  Delete ALL {len(docs)} documents? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Cancelled")
            return 0
        
        for doc in docs:
            result = rag.delete_document(doc['filename'])
            print(f"  {result}")
    
    elif args.filename:
        result = rag.delete_document(args.filename)
        print(result)
    
    else:
        print("❌ Please specify either --filename or --all")
        return 1
    
    return 0

def cmd_search(args):
    """Search documents without generating answers"""
    rag, is_ready = setup_rag()
    if not is_ready:
        print("❌ System not ready. Run 'status' command for details.")
        return 1
    
    query = args.query
    results = rag.search_documents(query, n_results=args.results)
    
    if not results:
        print(f"🔍 No results found for: '{query}'")
        return 0
    
    print(f"🔍 Search results for: '{query}'")
    print("-" * 50)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['metadata']['filename']} (similarity: {1-result['distance']:.3f})")
        print(f"   {result['document'][:200]}...")
        print()
    
    return 0

def cmd_export(args):
    """Export document metadata"""
    rag, is_ready = setup_rag()
    if not is_ready:
        print("❌ System not ready. Run 'status' command for details.")
        return 1
    
    docs = rag.list_documents()
    
    if args.format == 'json':
        output = json.dumps(docs, indent=2)
    elif args.format == 'csv':
        import csv
        import io
        output_io = io.StringIO()
        if docs:
            writer = csv.DictWriter(output_io, fieldnames=docs[0].keys())
            writer.writeheader()
            writer.writerows(docs)
        output = output_io.getvalue()
    else:
        # Plain text
        output = f"Document Database Export - {datetime.now().isoformat()}\n"
        output += "=" * 60 + "\n\n"
        for doc in docs:
            output += f"Filename: {doc['filename']}\n"
            output += f"Type: {doc['file_type']}\n"
            output += f"Chunks: {doc['total_chunks']}\n"
            output += f"Processed: {doc['processed_time']}\n"
            output += f"Path: {doc['filepath']}\n\n"
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"📄 Exported to: {args.output}")
    else:
        print(output)
    
    return 0

def main():
    parser = argparse.ArgumentParser(
        description="Document RAG System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 cli.py status                           # Check system status
  python3 cli.py ingest --file document.pdf      # Ingest single document
  python3 cli.py ingest --directory ./docs       # Ingest directory
  python3 cli.py query                           # Interactive query mode
  python3 cli.py query "What is AI?"             # Single query
  python3 cli.py list                            # List all documents
  python3 cli.py delete --filename doc.pdf       # Delete specific document
  python3 cli.py search "machine learning"       # Search without answering
  python3 cli.py export --format json            # Export metadata
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    parser_status = subparsers.add_parser('status', help='Check system status')
    
    # Ingest command
    parser_ingest = subparsers.add_parser('ingest', help='Ingest documents')
    ingest_group = parser_ingest.add_mutually_exclusive_group(required=True)
    ingest_group.add_argument('--file', help='Single file to ingest')
    ingest_group.add_argument('--directory', help='Directory to ingest')
    parser_ingest.add_argument('--password', help='Password for encrypted PDF files')
    
    # Query command
    parser_query = subparsers.add_parser('query', help='Query documents')
    parser_query.add_argument('question', nargs='?', help='Question to ask (optional for interactive mode)')
    parser_query.add_argument('--results', type=int, default=5, help='Number of search results to consider')
    parser_query.add_argument('--verbose', action='store_true', help='Show detailed search results')
    
    # List command
    parser_list = subparsers.add_parser('list', help='List documents')
    parser_list.add_argument('--verbose', action='store_true', help='Show detailed information')
    
    # Delete command
    parser_delete = subparsers.add_parser('delete', help='Delete documents')
    delete_group = parser_delete.add_mutually_exclusive_group(required=True)
    delete_group.add_argument('--filename', help='Specific file to delete')
    delete_group.add_argument('--all', action='store_true', help='Delete all documents')
    
    # Search command
    parser_search = subparsers.add_parser('search', help='Search documents')
    parser_search.add_argument('query', help='Search query')
    parser_search.add_argument('--results', type=int, default=5, help='Number of results to show')
    
    # Export command
    parser_export = subparsers.add_parser('export', help='Export document metadata')
    parser_export.add_argument('--format', choices=['json', 'csv', 'txt'], default='txt', help='Output format')
    parser_export.add_argument('--output', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate command handler
    commands = {
        'status': cmd_status,
        'ingest': cmd_ingest,
        'query': cmd_query,
        'list': cmd_list,
        'delete': cmd_delete,
        'search': cmd_search,
        'export': cmd_export,
    }
    
    try:
        return commands[args.command](args)
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        if '--verbose' in sys.argv:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
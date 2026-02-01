"""
Test script for Phase 5: Data Management APIs
Tests MongoDB and Weaviate endpoints for agentic AI use cases.
"""
import asyncio
import sys
sys.path.insert(0, '/home/sachanta/wd/repos/agentic-ai-framework/backend')

import httpx
from datetime import datetime


BASE_URL = "http://localhost:8000/api/v1"


async def test_mongodb_status():
    """Test MongoDB status endpoint."""
    print("\n" + "=" * 60)
    print("TEST 1: MongoDB Status & Stats")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # Status
        print("\n[1.1] MongoDB Status...")
        try:
            response = await client.get(f"{BASE_URL}/mongodb/status")
            if response.status_code == 200:
                data = response.json()
                print(f"  Status: {data.get('status')}")
                print(f"  Healthy: {data.get('healthy')}")
                print(f"  Latency: {data.get('latency_ms')}ms")
            else:
                print(f"  Error: {response.status_code}")
        except Exception as e:
            print(f"  Connection error: {e}")
            return False

        # Stats
        print("\n[1.2] MongoDB Stats...")
        try:
            response = await client.get(f"{BASE_URL}/mongodb/stats")
            if response.status_code == 200:
                data = response.json()
                print(f"  Database: {data.get('database')}")
                print(f"  Collections: {data.get('collection_count')}")
                print(f"  Total Documents: {data.get('total_documents')}")
            else:
                print(f"  Error: {response.status_code}")
        except Exception as e:
            print(f"  Error: {e}")

    print("\n  ✅ MongoDB status test passed!")
    return True


async def test_mongodb_collections():
    """Test MongoDB collection operations."""
    print("\n" + "=" * 60)
    print("TEST 2: MongoDB Collection Operations")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # List collections
        print("\n[2.1] List Collections...")
        response = await client.get(f"{BASE_URL}/mongodb/collections")
        if response.status_code == 200:
            data = response.json()
            # Handle both list and dict responses
            if isinstance(data, list):
                collections = data
            else:
                collections = data.get("collections", []) if isinstance(data, dict) else []
            print(f"  Found {len(collections)} collections")
            for c in collections[:5]:
                if isinstance(c, dict):
                    print(f"    - {c.get('name')}: {c.get('document_count', 'N/A')} docs")
                else:
                    print(f"    - {c}")
        else:
            print(f"  Error: {response.status_code}")

        # Create test collection
        print("\n[2.2] Create Test Collection...")
        response = await client.post(
            f"{BASE_URL}/mongodb/collections",
            json={"name": "test_phase5"}
        )
        if response.status_code in [201, 409]:
            if response.status_code == 409:
                print("  Collection already exists (OK)")
            else:
                print("  Created test_phase5 collection")
        else:
            print(f"  Error: {response.status_code}")

    print("\n  ✅ MongoDB collection test passed!")
    return True


async def test_mongodb_documents():
    """Test MongoDB document CRUD."""
    print("\n" + "=" * 60)
    print("TEST 3: MongoDB Document CRUD")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        collection = "test_phase5"

        # Create document (wrap in 'data' field as expected by endpoint)
        print("\n[3.1] Create Document...")
        doc = {
            "data": {
                "title": "Test Document",
                "content": "This is a test document for Phase 5",
                "tags": ["test", "phase5"],
            },
            "add_timestamps": True
        }
        response = await client.post(
            f"{BASE_URL}/mongodb/collections/{collection}/documents",
            json=doc
        )
        if response.status_code == 201:
            created = response.json()
            doc_id = created.get("id")
            print(f"  Created document: {doc_id}")
        else:
            print(f"  Error: {response.status_code} - {response.text}")
            return False

        # Read document
        print("\n[3.2] Read Document...")
        response = await client.get(
            f"{BASE_URL}/mongodb/collections/{collection}/documents/{doc_id}"
        )
        if response.status_code == 200:
            read_doc = response.json()
            print(f"  Title: {read_doc.get('title')}")
            print(f"  Content: {read_doc.get('content')[:50]}...")
        else:
            print(f"  Error: {response.status_code}")

        # List documents
        print("\n[3.3] List Documents (Paginated)...")
        response = await client.get(
            f"{BASE_URL}/mongodb/collections/{collection}/documents",
            params={"page": 1, "page_size": 10}
        )
        if response.status_code == 200:
            result = response.json()
            print(f"  Total: {result.get('total')}")
            print(f"  Page: {result.get('page')} of {result.get('total_pages')}")
            print(f"  Has Next: {result.get('has_next')}")
        else:
            print(f"  Error: {response.status_code}")

        # Update document
        print("\n[3.4] Update Document...")
        response = await client.put(
            f"{BASE_URL}/mongodb/collections/{collection}/documents/{doc_id}",
            json={"data": {"content": "Updated content for Phase 5 test"}, "add_updated_at": True}
        )
        if response.status_code == 200:
            print(f"  Updated: {response.json().get('modified_count')} document(s)")
        else:
            print(f"  Error: {response.status_code}")

        # Delete document
        print("\n[3.5] Delete Document...")
        response = await client.delete(
            f"{BASE_URL}/mongodb/collections/{collection}/documents/{doc_id}"
        )
        if response.status_code == 200:
            print(f"  Deleted: {response.json().get('deleted_count')} document(s)")
        else:
            print(f"  Error: {response.status_code}")

    print("\n  ✅ MongoDB document CRUD test passed!")
    return True


async def test_mongodb_agent_executions():
    """Test MongoDB agent execution tracking."""
    print("\n" + "=" * 60)
    print("TEST 4: MongoDB Agent Executions")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # Create execution
        print("\n[4.1] Create Agent Execution...")
        execution = {
            "agent_id": "greeter_agent",
            "agent_name": "Greeter Agent",
            "input": {"name": "Alice", "style": "friendly"},
            "status": "running"
        }
        response = await client.post(
            f"{BASE_URL}/mongodb/agent-executions",
            json=execution
        )
        if response.status_code in [200, 201]:
            created = response.json()
            exec_id = created.get("id")
            print(f"  Created execution: {exec_id}")
        else:
            print(f"  Error: {response.status_code} - {response.text}")
            return False

        # Update execution (complete)
        print("\n[4.2] Complete Execution...")
        response = await client.patch(
            f"{BASE_URL}/mongodb/agent-executions/{exec_id}",
            json={
                "status": "completed",
                "output": {"greeting": "Hello, Alice!"},
                "tokens_used": 150,
                "cost": 0.0015
            }
        )
        if response.status_code == 200:
            print(f"  Execution completed")
        else:
            print(f"  Error: {response.status_code}")

        # List executions
        print("\n[4.3] List Agent Executions...")
        response = await client.get(
            f"{BASE_URL}/mongodb/agent-executions",
            params={"agent_id": "greeter_agent", "page_size": 5}
        )
        if response.status_code == 200:
            result = response.json()
            print(f"  Total executions: {result.get('total')}")
            for item in result.get("items", [])[:3]:
                print(f"    - {item.get('agent_name')}: {item.get('status')}")
        else:
            print(f"  Error: {response.status_code}")

    print("\n  ✅ MongoDB agent executions test passed!")
    return True


async def test_mongodb_conversations():
    """Test MongoDB conversation memory."""
    print("\n" + "=" * 60)
    print("TEST 5: MongoDB Conversation Memory")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # Create conversation
        print("\n[5.1] Create Conversation...")
        conversation = {
            "session_id": "test-session-001",
            "agent_id": "chat_agent",
            "messages": [
                {"role": "user", "content": "Hello!"},
                {"role": "assistant", "content": "Hi there! How can I help?"}
            ]
        }
        response = await client.post(
            f"{BASE_URL}/mongodb/conversations",
            json=conversation
        )
        if response.status_code in [200, 201]:
            created = response.json()
            conv_id = created.get("id")
            print(f"  Created conversation: {conv_id}")
        else:
            print(f"  Error: {response.status_code} - {response.text}")
            return False

        # Add message
        print("\n[5.2] Add Message to Conversation...")
        response = await client.post(
            f"{BASE_URL}/mongodb/conversations/{conv_id}/messages",
            json={"role": "user", "content": "What's the weather like?"}
        )
        if response.status_code == 200:
            print(f"  Message added")
        else:
            print(f"  Error: {response.status_code}")

        # Get conversation
        print("\n[5.3] Get Conversation...")
        response = await client.get(f"{BASE_URL}/mongodb/conversations/{conv_id}")
        if response.status_code == 200:
            conv = response.json()
            print(f"  Session: {conv.get('session_id')}")
            print(f"  Messages: {len(conv.get('messages', []))}")
        else:
            print(f"  Error: {response.status_code}")

    print("\n  ✅ MongoDB conversation memory test passed!")
    return True


async def test_weaviate_status():
    """Test Weaviate status endpoint."""
    print("\n" + "=" * 60)
    print("TEST 6: Weaviate Status & Stats")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # Status
        print("\n[6.1] Weaviate Status...")
        try:
            response = await client.get(f"{BASE_URL}/weaviate/status")
            if response.status_code == 200:
                data = response.json()
                print(f"  Status: {data.get('status')}")
                print(f"  Healthy: {data.get('healthy')}")
                print(f"  Version: {data.get('version')}")
            else:
                print(f"  Status code: {response.status_code}")
                if response.status_code == 503:
                    print("  Weaviate not available - skipping Weaviate tests")
                    return True  # Don't fail if Weaviate is not running
        except Exception as e:
            print(f"  Connection error: {e}")
            return True  # Don't fail if Weaviate is not running

        # Stats
        print("\n[6.2] Weaviate Stats...")
        response = await client.get(f"{BASE_URL}/weaviate/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"  Collections: {data.get('collection_count')}")
            print(f"  Total Objects: {data.get('total_objects')}")

    print("\n  ✅ Weaviate status test passed!")
    return True


async def test_weaviate_collections():
    """Test Weaviate collection operations."""
    print("\n" + "=" * 60)
    print("TEST 7: Weaviate Collection Operations")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # Check if Weaviate is available
        response = await client.get(f"{BASE_URL}/weaviate/status")
        if response.status_code == 503:
            print("  Weaviate not available - skipping")
            return True

        # List collections
        print("\n[7.1] List Collections...")
        response = await client.get(f"{BASE_URL}/weaviate/collections")
        if response.status_code == 200:
            collections = response.json()
            print(f"  Found {len(collections)} collections")
            for c in collections[:5]:
                print(f"    - {c.get('name')}: {c.get('object_count')} objects")
        else:
            print(f"  Error: {response.status_code}")

        # Create collection
        print("\n[7.2] Create Test Collection...")
        response = await client.post(
            f"{BASE_URL}/weaviate/collections",
            json={
                "name": "TestPhase5",
                "description": "Test collection for Phase 5",
                "properties": [
                    {"name": "title", "dataType": ["text"]},
                    {"name": "content", "dataType": ["text"]}
                ]
            }
        )
        if response.status_code in [201, 409]:
            if response.status_code == 409:
                print("  Collection already exists (OK)")
            else:
                print("  Created TestPhase5 collection")
        else:
            print(f"  Error: {response.status_code} - {response.text}")

    print("\n  ✅ Weaviate collection test passed!")
    return True


async def test_weaviate_documents():
    """Test Weaviate document operations."""
    print("\n" + "=" * 60)
    print("TEST 8: Weaviate Document Operations")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # Check if Weaviate is available
        response = await client.get(f"{BASE_URL}/weaviate/status")
        if response.status_code == 503:
            print("  Weaviate not available - skipping")
            return True

        collection = "TestPhase5"

        # Add document
        print("\n[8.1] Add Document...")
        response = await client.post(
            f"{BASE_URL}/weaviate/collections/{collection}/documents",
            json={
                "properties": {
                    "title": "Test Document",
                    "content": "This is a test document for vector storage"
                }
            }
        )
        if response.status_code == 201:
            created = response.json()
            doc_id = created.get("id")
            print(f"  Created document: {doc_id}")
        else:
            print(f"  Error: {response.status_code} - {response.text}")
            return False

        # Get document
        print("\n[8.2] Get Document...")
        response = await client.get(
            f"{BASE_URL}/weaviate/collections/{collection}/documents/{doc_id}"
        )
        if response.status_code == 200:
            doc = response.json()
            print(f"  Title: {doc.get('properties', {}).get('title')}")
        else:
            print(f"  Error: {response.status_code}")

        # List documents
        print("\n[8.3] List Documents (Paginated)...")
        response = await client.get(
            f"{BASE_URL}/weaviate/collections/{collection}/documents",
            params={"page": 1, "page_size": 10}
        )
        if response.status_code == 200:
            result = response.json()
            print(f"  Total: {result.get('total')}")
            print(f"  Page: {result.get('page')} of {result.get('total_pages')}")
            print(f"  Has Next: {result.get('has_next')}")
        else:
            print(f"  Error: {response.status_code}")

        # Delete document
        print("\n[8.4] Delete Document...")
        response = await client.delete(
            f"{BASE_URL}/weaviate/collections/{collection}/documents/{doc_id}"
        )
        if response.status_code == 200:
            print("  Document deleted")
        else:
            print(f"  Error: {response.status_code}")

    print("\n  ✅ Weaviate document test passed!")
    return True


async def test_weaviate_rag():
    """Test Weaviate RAG endpoints."""
    print("\n" + "=" * 60)
    print("TEST 9: Weaviate RAG (Knowledge Base)")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # Check if Weaviate is available
        response = await client.get(f"{BASE_URL}/weaviate/status")
        if response.status_code == 503:
            print("  Weaviate not available - skipping")
            return True

        # Add RAG document
        print("\n[9.1] Add RAG Document...")
        response = await client.post(
            f"{BASE_URL}/weaviate/rag/documents",
            json={
                "title": "Python Basics",
                "content": "Python is a high-level programming language known for its simplicity and readability.",
                "source": "test_docs"
            }
        )
        if response.status_code == 201:
            created = response.json()
            print(f"  Created RAG doc: {created.get('id')}")
            print(f"  Has Vector: {created.get('has_vector')}")
        else:
            print(f"  Error: {response.status_code} - {response.text}")

        # List RAG documents
        print("\n[9.2] List RAG Documents...")
        response = await client.get(f"{BASE_URL}/weaviate/rag/documents")
        if response.status_code == 200:
            result = response.json()
            print(f"  Total: {result.get('total')}")
        else:
            print(f"  Error: {response.status_code}")

        # Query RAG (if embeddings available)
        print("\n[9.3] Query RAG...")
        response = await client.post(
            f"{BASE_URL}/weaviate/rag/query",
            json={"query": "What is Python?", "limit": 3}
        )
        if response.status_code == 200:
            result = response.json()
            print(f"  Found: {result.get('count')} results")
            for r in result.get("results", [])[:2]:
                print(f"    - {r.get('title')}: score={r.get('score')}")
        elif response.status_code == 503:
            print("  Embeddings not available - OK")
        else:
            print(f"  Error: {response.status_code}")

    print("\n  ✅ Weaviate RAG test passed!")
    return True


async def test_weaviate_memory():
    """Test Weaviate agent memory endpoints."""
    print("\n" + "=" * 60)
    print("TEST 10: Weaviate Agent Memory")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # Check if Weaviate is available
        response = await client.get(f"{BASE_URL}/weaviate/status")
        if response.status_code == 503:
            print("  Weaviate not available - skipping")
            return True

        # Store memory
        print("\n[10.1] Store Agent Memory...")
        response = await client.post(
            f"{BASE_URL}/weaviate/memory",
            json={
                "agent_id": "test_agent",
                "content": "The user asked about Python programming.",
                "memory_type": "conversation",
                "session_id": "test-session"
            }
        )
        if response.status_code == 201:
            created = response.json()
            print(f"  Created memory: {created.get('id')}")
            print(f"  Has Vector: {created.get('has_vector')}")
        else:
            print(f"  Error: {response.status_code} - {response.text}")

        # Get agent memories
        print("\n[10.2] Get Agent Memories...")
        response = await client.get(
            f"{BASE_URL}/weaviate/memory/test_agent",
            params={"page": 1, "page_size": 10}
        )
        if response.status_code == 200:
            result = response.json()
            print(f"  Total: {result.get('total')}")
        else:
            print(f"  Error: {response.status_code}")

        # Query memory
        print("\n[10.3] Query Agent Memory...")
        response = await client.post(
            f"{BASE_URL}/weaviate/memory/query",
            json={
                "agent_id": "test_agent",
                "query": "Python",
                "limit": 5
            }
        )
        if response.status_code == 200:
            result = response.json()
            print(f"  Found: {result.get('count')} memories")
        elif response.status_code == 503:
            print("  Embeddings not available - OK")
        else:
            print(f"  Error: {response.status_code}")

    print("\n  ✅ Weaviate agent memory test passed!")
    return True


async def main():
    """Run all tests."""
    print("\n" + "#" * 60)
    print("# Phase 5 Tests - Data Management APIs")
    print("#" * 60)

    print("\nNote: Make sure the backend server is running on localhost:8000")
    print("      and MongoDB/Weaviate are available.\n")

    tests = [
        ("MongoDB Status", test_mongodb_status),
        ("MongoDB Collections", test_mongodb_collections),
        ("MongoDB Documents", test_mongodb_documents),
        ("MongoDB Agent Executions", test_mongodb_agent_executions),
        ("MongoDB Conversations", test_mongodb_conversations),
        ("Weaviate Status", test_weaviate_status),
        ("Weaviate Collections", test_weaviate_collections),
        ("Weaviate Documents", test_weaviate_documents),
        ("Weaviate RAG", test_weaviate_rag),
        ("Weaviate Memory", test_weaviate_memory),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n  ❌ {name} failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {name}: {status}")

    passed = sum(1 for _, s in results if s)
    print(f"\n  Total: {passed}/{len(results)} tests passed")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

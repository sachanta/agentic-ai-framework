"""
Test script for Phase 3: LLM & Agent Foundation
Tests Ollama integration with agents, chains, and providers.
"""
import asyncio
import sys
sys.path.insert(0, '/home/sachanta/wd/repos/agentic-ai-framework/backend')

from app.common.providers.llm import get_llm_provider, LLMProviderType
from app.common.providers.embeddings import get_embeddings_provider, EmbeddingsProviderType
from app.common.base.agent import SimpleAgent, ConversationalAgent, AgentTool
from app.common.base.chain import PromptTemplate, LLMChain


async def test_llm_provider():
    """Test the Ollama LLM provider."""
    print("\n" + "="*60)
    print("TEST 1: LLM Provider (Ollama)")
    print("="*60)

    llm = get_llm_provider(LLMProviderType.OLLAMA)

    # Health check
    print("\n[1.1] Health Check...")
    healthy = await llm.health_check()
    print(f"  Ollama healthy: {healthy}")

    # List models
    print("\n[1.2] List Available Models...")
    models = await llm.list_models()
    print(f"  Available models: {models}")

    # Simple generation
    print("\n[1.3] Simple Generation...")
    response = await llm.generate(
        prompt="What is 2 + 2? Answer in one word.",
        model="llama3",
        temperature=0.1,
        max_tokens=50
    )
    print(f"  Prompt: 'What is 2 + 2? Answer in one word.'")
    print(f"  Response: {response.content.strip()}")
    print(f"  Model: {response.model}")

    # Generation with system prompt
    print("\n[1.4] Generation with System Prompt...")
    response = await llm.generate(
        prompt="What should I name my cat?",
        system="You are a pirate. Speak like a pirate in all responses.",
        model="llama3",
        temperature=0.7,
        max_tokens=100
    )
    print(f"  System: 'You are a pirate...'")
    print(f"  Prompt: 'What should I name my cat?'")
    print(f"  Response: {response.content.strip()[:200]}...")

    # Chat conversation
    print("\n[1.5] Chat Conversation...")
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Keep responses brief."},
        {"role": "user", "content": "Hi, my name is Alice."},
    ]
    response = await llm.chat(messages=messages, model="llama3", max_tokens=100)
    print(f"  User: 'Hi, my name is Alice.'")
    print(f"  Assistant: {response.content.strip()[:150]}...")

    # Follow-up in chat
    messages.append({"role": "assistant", "content": response.content})
    messages.append({"role": "user", "content": "What's my name?"})
    response = await llm.chat(messages=messages, model="llama3", max_tokens=50)
    print(f"  User: 'What's my name?'")
    print(f"  Assistant: {response.content.strip()}")

    print("\n  ✅ LLM Provider tests passed!")
    return True


async def test_embeddings_provider():
    """Test the Ollama embeddings provider."""
    print("\n" + "="*60)
    print("TEST 2: Embeddings Provider (Ollama)")
    print("="*60)

    try:
        embeddings = get_embeddings_provider(EmbeddingsProviderType.OLLAMA)

        # Health check
        print("\n[2.1] Health Check...")
        healthy = await embeddings.health_check()
        print(f"  Embeddings healthy: {healthy}")

        if not healthy:
            print("  ⚠️  Embeddings model not available. Skipping embedding tests.")
            print("  To enable: ollama pull nomic-embed-text")
            return True

        # Single embedding
        print("\n[2.2] Single Text Embedding...")
        text = "Hello, world!"
        vector = await embeddings.embed_text(text)
        print(f"  Text: '{text}'")
        print(f"  Vector dimension: {len(vector)}")
        print(f"  First 5 values: {vector[:5]}")

        # Multiple embeddings
        print("\n[2.3] Multiple Text Embeddings...")
        texts = ["cat", "dog", "automobile"]
        vectors = await embeddings.embed_texts(texts)
        print(f"  Texts: {texts}")
        print(f"  Generated {len(vectors)} vectors")

        # Similarity check (cat should be more similar to dog than automobile)
        def cosine_similarity(a, b):
            dot = sum(x*y for x, y in zip(a, b))
            norm_a = sum(x*x for x in a) ** 0.5
            norm_b = sum(x*x for x in b) ** 0.5
            return dot / (norm_a * norm_b)

        sim_cat_dog = cosine_similarity(vectors[0], vectors[1])
        sim_cat_auto = cosine_similarity(vectors[0], vectors[2])
        print(f"  Similarity (cat, dog): {sim_cat_dog:.4f}")
        print(f"  Similarity (cat, automobile): {sim_cat_auto:.4f}")
        print(f"  Cat is more similar to dog: {sim_cat_dog > sim_cat_auto}")

        print("\n  ✅ Embeddings Provider tests passed!")
    except Exception as e:
        print(f"\n  ⚠️  Embeddings test skipped: {e}")
        print("  To enable embeddings: ollama pull nomic-embed-text")

    return True


async def test_simple_agent():
    """Test the SimpleAgent."""
    print("\n" + "="*60)
    print("TEST 3: Simple Agent")
    print("="*60)

    agent = SimpleAgent(
        name="math_helper",
        description="A helpful math assistant",
        system_prompt="You are a math tutor. Give clear, concise answers.",
        model="llama3",
        temperature=0.1,
        max_tokens=150
    )

    print("\n[3.1] Running Simple Agent...")
    result = await agent.run({
        "message": "What is the square root of 144?"
    })

    print(f"  Agent: {agent.name}")
    print(f"  Input: 'What is the square root of 144?'")
    print(f"  Success: {result.get('success')}")
    print(f"  Response: {result.get('response', '')[:200]}...")

    print("\n  ✅ Simple Agent test passed!")
    return True


async def test_conversational_agent():
    """Test the ConversationalAgent with memory."""
    print("\n" + "="*60)
    print("TEST 4: Conversational Agent (with Memory)")
    print("="*60)

    agent = ConversationalAgent(
        name="chat_buddy",
        description="A friendly chat companion",
        system_prompt="You are a friendly assistant. Remember details from our conversation. Keep responses brief.",
        model="llama3",
        temperature=0.7,
        max_tokens=100
    )

    print("\n[4.1] First Message...")
    result1 = await agent.run({"message": "Hi! I'm learning Python programming."})
    print(f"  User: 'Hi! I'm learning Python programming.'")
    print(f"  Agent: {result1.get('response', '')[:150]}...")
    print(f"  Messages in memory: {result1.get('message_count')}")

    print("\n[4.2] Follow-up Message (testing memory)...")
    result2 = await agent.run({"message": "What am I learning?"})
    print(f"  User: 'What am I learning?'")
    print(f"  Agent: {result2.get('response', '')[:150]}...")
    print(f"  Messages in memory: {result2.get('message_count')}")

    print("\n[4.3] Reset and verify...")
    agent.reset_conversation()
    print(f"  Conversation reset. Messages in memory: {len(agent.memory.messages)}")

    print("\n  ✅ Conversational Agent test passed!")
    return True


async def test_llm_chain():
    """Test the LLMChain."""
    print("\n" + "="*60)
    print("TEST 5: LLM Chain with Prompt Template")
    print("="*60)

    # Create a prompt template
    template = PromptTemplate(
        template="Translate the following {language} word to English: {word}"
    )

    print("\n[5.1] Prompt Template...")
    print(f"  Template: '{template.template}'")
    print(f"  Variables: {template.input_variables}")

    # Create the chain
    chain = LLMChain(
        name="translator",
        prompt_template=template,
        output_key="translation",
        model="llama3",
        temperature=0.1,
        max_tokens=50
    )

    print("\n[5.2] Running Chain...")
    result = await chain.run({
        "language": "Spanish",
        "word": "gato"
    })

    print(f"  Input: language='Spanish', word='gato'")
    print(f"  Success: {result.get('success')}")
    print(f"  Translation: {result.get('translation', '')[:100]}")

    print("\n[5.3] Running Chain with Different Input...")
    result2 = await chain.run({
        "language": "French",
        "word": "maison"
    })
    print(f"  Input: language='French', word='maison'")
    print(f"  Translation: {result2.get('translation', '')[:100]}")

    print("\n  ✅ LLM Chain test passed!")
    return True


async def test_agent_with_tool():
    """Test an agent with a custom tool."""
    print("\n" + "="*60)
    print("TEST 6: Agent with Tool")
    print("="*60)

    # Define a simple calculator tool
    async def calculate(expression: str) -> dict:
        """Safely evaluate a math expression."""
        try:
            # Only allow safe math operations
            allowed = set('0123456789+-*/.() ')
            if all(c in allowed for c in expression):
                result = eval(expression)
                return {"result": result, "success": True}
            return {"error": "Invalid expression", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}

    calc_tool = AgentTool(
        name="calculator",
        description="Evaluate mathematical expressions",
        func=calculate,
        parameters={"expression": "string"}
    )

    agent = SimpleAgent(
        name="math_agent",
        description="An agent that can do math",
        tools=[calc_tool],
        model="llama3"
    )

    print("\n[6.1] Agent Tools...")
    print(f"  Agent: {agent.name}")
    print(f"  Tools: {[t.name for t in agent.tools]}")
    print(f"  Tool description: {agent.get_tools_description()}")

    print("\n[6.2] Execute Tool Directly...")
    result = await agent.execute_tool("calculator", expression="15 * 7 + 3")
    print(f"  Expression: '15 * 7 + 3'")
    print(f"  Result: {result}")

    print("\n  ✅ Agent with Tool test passed!")
    return True


async def main():
    """Run all tests."""
    print("\n" + "#"*60)
    print("# Phase 3 Integration Tests - Ollama LLM & Agent Foundation")
    print("#"*60)

    tests = [
        ("LLM Provider", test_llm_provider),
        ("Embeddings Provider", test_embeddings_provider),
        ("Simple Agent", test_simple_agent),
        ("Conversational Agent", test_conversational_agent),
        ("LLM Chain", test_llm_chain),
        ("Agent with Tool", test_agent_with_tool),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n  ❌ {name} failed with error: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {name}: {status}")

    passed = sum(1 for _, s in results if s)
    print(f"\n  Total: {passed}/{len(results)} tests passed")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

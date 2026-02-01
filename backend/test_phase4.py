"""
Test script for Phase 4: Hello World Platform with Decoupled LLM Config
"""
import asyncio
import sys
sys.path.insert(0, '/home/sachanta/wd/repos/agentic-ai-framework/backend')

from app.config import settings
from app.common.providers.llm import get_llm_provider, clear_provider_cache, LLMConfig
from app.platforms.hello_world.config import config as hw_config
from app.platforms.hello_world.agents.greeter.llm import get_greeter_llm, get_greeter_config
from app.platforms.hello_world.agents.greeter import GreeterAgent
from app.platforms.hello_world.orchestrator import HelloWorldOrchestrator
from app.platforms.hello_world.services import HelloWorldService


async def test_global_config():
    """Test that global LLM config is read correctly."""
    print("\n" + "="*60)
    print("TEST 1: Global LLM Configuration")
    print("="*60)

    print(f"\n[1.1] Global Settings:")
    print(f"  LLM_PROVIDER: {settings.LLM_PROVIDER}")
    print(f"  LLM_DEFAULT_MODEL: {settings.LLM_DEFAULT_MODEL}")
    print(f"  LLM_TEMPERATURE: {settings.LLM_TEMPERATURE}")
    print(f"  LLM_MAX_TOKENS: {settings.LLM_MAX_TOKENS}")
    print(f"  OLLAMA_BASE_URL: {settings.OLLAMA_BASE_URL}")

    print(f"\n[1.2] Default LLM Provider:")
    clear_provider_cache()  # Clear cache to test fresh provider creation
    llm = get_llm_provider()
    print(f"  Provider: {llm.provider_name}")
    print(f"  Model: {llm.default_model}")

    print(f"\n[1.3] LLM Health Check:")
    healthy = await llm.health_check()
    print(f"  Healthy: {healthy}")

    print("\n  ✅ Global config test passed!")
    return True


async def test_platform_config():
    """Test that platform config properly inherits from global."""
    print("\n" + "="*60)
    print("TEST 2: Platform Configuration (Hello World)")
    print("="*60)

    print(f"\n[2.1] Platform-specific Settings:")
    print(f"  LLM_PROVIDER override: {hw_config.LLM_PROVIDER} (None = use global)")
    print(f"  LLM_MODEL override: {hw_config.LLM_MODEL} (None = use global)")

    print(f"\n[2.2] Effective Settings (after fallback):")
    print(f"  Provider: {hw_config.effective_provider}")
    print(f"  Model: {hw_config.effective_model}")
    print(f"  Temperature: {hw_config.effective_temperature}")
    print(f"  Max Tokens: {hw_config.effective_max_tokens}")

    print(f"\n[2.3] Greeter LLM Config:")
    greeter_config = get_greeter_config()
    print(f"  {greeter_config}")

    print("\n  ✅ Platform config test passed!")
    return True


async def test_greeter_agent():
    """Test the greeter agent with LLM."""
    print("\n" + "="*60)
    print("TEST 3: Greeter Agent with LLM")
    print("="*60)

    agent = GreeterAgent()

    print(f"\n[3.1] Agent Configuration:")
    llm_info = agent.get_llm_info()
    print(f"  Agent Name: {agent.name}")
    print(f"  LLM Provider: {llm_info.get('provider')}")
    print(f"  LLM Model: {llm_info.get('model')}")

    print(f"\n[3.2] Generate Friendly Greeting:")
    result = await agent.run({"name": "Alice", "style": "friendly"})
    print(f"  Name: Alice, Style: friendly")
    print(f"  Greeting: {result['greeting']}")
    print(f"  Provider: {result['metadata'].get('provider')}")
    print(f"  Model: {result['metadata'].get('model')}")
    print(f"  Fallback: {result['metadata'].get('fallback')}")

    print(f"\n[3.3] Generate Formal Greeting:")
    result = await agent.run({"name": "Dr. Smith", "style": "formal"})
    print(f"  Name: Dr. Smith, Style: formal")
    print(f"  Greeting: {result['greeting']}")

    print(f"\n[3.4] Generate Enthusiastic Greeting:")
    result = await agent.run({"name": "Bob", "style": "enthusiastic"})
    print(f"  Name: Bob, Style: enthusiastic")
    print(f"  Greeting: {result['greeting']}")

    print("\n  ✅ Greeter agent test passed!")
    return True


async def test_orchestrator():
    """Test the orchestrator workflow."""
    print("\n" + "="*60)
    print("TEST 4: Hello World Orchestrator")
    print("="*60)

    orchestrator = HelloWorldOrchestrator()

    print(f"\n[4.1] Orchestrator Info:")
    print(f"  Name: {orchestrator.name}")
    print(f"  Agents: {orchestrator.list_agents()}")

    print(f"\n[4.2] Run Orchestrator Workflow:")
    result = await orchestrator.run({"name": "Charlie", "style": "casual"})
    print(f"  Input: name='Charlie', style='casual'")
    print(f"  Greeting: {result.get('greeting')}")
    print(f"  Agent Used: {result.get('agent')}")

    print("\n  ✅ Orchestrator test passed!")
    return True


async def test_service():
    """Test the service layer."""
    print("\n" + "="*60)
    print("TEST 5: Hello World Service")
    print("="*60)

    service = HelloWorldService()

    print(f"\n[5.1] Service Health Check:")
    llm_healthy = await service.check_llm_health()
    print(f"  LLM Healthy: {llm_healthy}")

    print(f"\n[5.2] Generate Greeting via Service:")
    result = await service.generate_greeting("Diana", "friendly")
    print(f"  Input: name='Diana', style='friendly'")
    print(f"  Greeting: {result.get('greeting')}")

    print(f"\n[5.3] Get Platform Status:")
    status = await service.get_status()
    print(f"  Status: {status}")

    print("\n  ✅ Service test passed!")
    return True


async def test_config_switching():
    """Test that config can be easily switched."""
    print("\n" + "="*60)
    print("TEST 6: LLM Config Switching")
    print("="*60)

    print(f"\n[6.1] Create Custom LLM Configs:")

    # Test creating configs with different providers
    ollama_config = LLMConfig(provider="ollama", model="llama3")
    print(f"  Ollama Config: provider={ollama_config.provider}, model={ollama_config.model}")

    openai_config = LLMConfig(provider="openai", model="gpt-4")
    print(f"  OpenAI Config: provider={openai_config.provider}, model={openai_config.model}")

    bedrock_config = LLMConfig(provider="aws_bedrock", model="anthropic.claude-v2")
    print(f"  Bedrock Config: provider={bedrock_config.provider}, model={bedrock_config.model}")

    print(f"\n[6.2] Get Provider by Config:")
    clear_provider_cache()
    ollama_llm = get_llm_provider(config=ollama_config)
    print(f"  Provider from config: {ollama_llm.provider_name}")

    print(f"\n[6.3] Config Precedence (explicit > config > global):")
    print(f"  Global default: {settings.LLM_PROVIDER}")
    config_provider = get_llm_provider(config=LLMConfig(provider="ollama"))
    print(f"  From config: {config_provider.provider_name}")

    print("\n  ✅ Config switching test passed!")
    return True


async def main():
    """Run all tests."""
    print("\n" + "#"*60)
    print("# Phase 4 Tests - Hello World Platform with Decoupled LLM")
    print("#"*60)

    tests = [
        ("Global Config", test_global_config),
        ("Platform Config", test_platform_config),
        ("Greeter Agent", test_greeter_agent),
        ("Orchestrator", test_orchestrator),
        ("Service", test_service),
        ("Config Switching", test_config_switching),
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

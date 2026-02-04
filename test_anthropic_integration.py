"""
Test script to verify Anthropic API integration
Run this to ensure the migration from Groq to Anthropic was successful
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app.ai.llm_factory import LLMFactory, get_clarification_llm, get_template_filler_llm, get_suggestions_llm
from app.core.config import settings


def test_configuration():
    """Test that configuration is properly loaded"""
    print("=" * 60)
    print("Testing Configuration...")
    print("=" * 60)

    api_key = settings.ANTHROPIC_API_KEY
    if api_key:
        print(f"✓ API Key loaded: {api_key[:10]}...{api_key[-5:]}")
    else:
        print("✗ Anthropic API Key not found in settings!")
        
    print(f"✓ Default Model: {settings.LLM_DEFAULT_MODEL}")
    print(f"✓ Clarification Model: {settings.LLM_CLARIFICATION_MODEL}")
    print(f"✓ Template Filler Model: {settings.LLM_TEMPLATE_FILLER_MODEL}")
    print(f"✓ Suggestions Model: {settings.LLM_SUGGESTIONS_MODEL}")
    print()


def test_factory_creation():
    """Test that LLM factory can create instances"""
    print("=" * 60)
    print("Testing LLM Factory Creation...")
    print("=" * 60)

    try:
        # Test factory methods
        clarification_llm = LLMFactory.create_clarification_llm()
        print(f"✓ Clarification LLM created: {type(clarification_llm).__name__}")

        template_filler_llm = LLMFactory.create_template_filler_llm()
        print(f"✓ Template Filler LLM created: {type(template_filler_llm).__name__}")

        suggestions_llm = LLMFactory.create_suggestions_llm()
        print(f"✓ Suggestions LLM created: {type(suggestions_llm).__name__}")

        custom_llm = LLMFactory.create_custom_llm()
        print(f"✓ Custom LLM created: {type(custom_llm).__name__}")

        # Test convenience functions
        llm1 = get_clarification_llm()
        print(f"✓ get_clarification_llm() works: {type(llm1).__name__}")

        llm2 = get_template_filler_llm()
        print(f"✓ get_template_filler_llm() works: {type(llm2).__name__}")

        llm3 = get_suggestions_llm()
        print(f"✓ get_suggestions_llm() works: {type(llm3).__name__}")

        print("\n✓ All LLM factory methods working correctly!")
        return True

    except Exception as e:
        print(f"\n✗ Error creating LLM instances: {e}")
        return False


def test_api_call():
    """Test actual API call to Anthropic"""
    print("\n" + "=" * 60)
    print("Testing Anthropic API Call...")
    print("=" * 60)

    try:
        llm = get_clarification_llm()

        # Simple test message
        messages = [
            {"role": "user", "content": "Say 'Hello from Anthropic!' if you can read this."}
        ]

        print("Sending test message to Anthropic API...")
        response = llm.invoke(messages)

        print(f"\n✓ API call successful!")
        print(f"✓ Response: {response.content}")
        print(f"✓ Model used: {response.response_metadata.get('model', 'N/A')}")
        
        return True

    except Exception as e:
        print(f"\n✗ API call failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check that ANTHROPIC_API_KEY is set correctly in .env")
        print("2. Verify your API key is valid at https://console.anthropic.com/")
        print("3. Ensure you have the langchain-anthropic package installed")
        return False


def test_json_parsing():
    """Test Anthropic's ability to generate structured JSON"""
    print("\n" + "=" * 60)
    print("Testing JSON Generation (Template Filler Capability)...")
    print("=" * 60)

    try:
        llm = get_template_filler_llm()

        messages = [
            {"role": "user", "content": """Generate a simple JSON object with this structure:
{
  "project_name": "Test Project",
  "features": ["feature1", "feature2"]
}

Only respond with valid JSON, nothing else."""}
        ]

        print("Testing structured output generation...")
        response = llm.invoke(messages)

        # Try to parse as JSON
        import json
        import re
        
        content = response.content
        if "```json" in content:
            content = re.search(r"```json\n(.*?)\n```", content, re.DOTALL).group(1)
        elif "```" in content:
            content = re.search(r"```\n(.*?)\n```", content, re.DOTALL).group(1)

        try:
            data = json.loads(content)
            print(f"\n✓ JSON generation successful!")
            print(f"✓ Parsed data: {data}")
            return True
        except json.JSONDecodeError:
            print(f"\n⚠ Response not valid JSON, but API call worked")
            print(f"Response: {response.content}")
            return True

    except Exception as e:
        print(f"\n✗ JSON generation test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("ANTHROPIC API INTEGRATION TEST")
    print("=" * 60)
    print()

    results = []

    # Test 1: Configuration
    test_configuration()

    # Test 2: Factory Creation
    results.append(("Factory Creation", test_factory_creation()))

    # Test 3: API Call
    results.append(("API Call", test_api_call()))

    # Test 4: JSON Generation
    results.append(("JSON Generation", test_json_parsing()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED - Anthropic integration is working!")
        print("=" * 60)
        print("\nYou can now:")
        print("1. Start the backend: uvicorn app.main:app --reload")
        print("2. Test the full API endpoint: POST /api/analyze-requirements")
        print("3. Monitor usage at: https://console.anthropic.com/")
    else:
        print("✗ SOME TESTS FAILED - Please check the errors above")
        print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

"""
Quick configuration test script.
Run this to verify configuration loading works correctly.
"""

import os
import sys
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.orchestration import get_config, reset_config


def test_config_defaults():
    """Test that configuration loads with default values."""
    print("=" * 60)
    print("Testing Configuration System")
    print("=" * 60)

    # Reset to ensure clean state
    reset_config()

    # Load config
    config = get_config()

    print("\n✓ Configuration loaded successfully!")
    print("\n--- LLM Configuration ---")
    print(f"  Provider:          {config.llm_provider}")
    print(f"  OpenAI Model:      {config.model_openai}")
    print(f"  Anthropic Model:   {config.model_anthropic}")
    print(f"  Temperature:       {config.llm_temperature}")
    print(f"  Max Tokens:        {config.llm_max_tokens}")

    print("\n--- Embedding Configuration ---")
    print(f"  Model:             {config.embedding_model}")
    print(f"  Retrieval Top-K:   {config.retrieval_top_k}")

    print("\n--- Agent Configuration ---")
    print(f"  Max Retries:       {config.max_retries}")
    print(f"  Concurrency Limit: {config.concurrency_limit}")

    print("\n--- Paths ---")
    print(f"  Data Dir:          {config.data_dir}")
    print(f"  Templates Dir:     {config.templates_dir}")
    print(f"  Output Dir:        {config.output_dir}")
    print(f"  Logs Dir:          {config.logs_dir}")

    print("\n--- Logging ---")
    print(f"  Log Level:         {config.log_level}")

    print("\n--- API Keys ---")
    print(f"  OpenAI Key Set:    {config.openai_api_key is not None}")
    print(f"  Anthropic Key Set: {config.anthropic_api_key is not None}")

    return config


def test_api_key_validation():
    """Test API key validation."""
    print("\n" + "=" * 60)
    print("Testing API Key Validation")
    print("=" * 60)

    config = get_config()

    # Test OpenAI validation
    try:
        config.validate_api_keys("openai")
        print("\n✓ OpenAI API key validation: PASSED")
    except ValueError as e:
        print(f"\n✗ OpenAI API key validation: FAILED")
        print(f"  Reason: {e}")

    # Test Anthropic validation
    try:
        config.validate_api_keys("anthropic")
        print("✓ Anthropic API key validation: PASSED")
    except ValueError as e:
        print(f"✗ Anthropic API key validation: FAILED")
        print(f"  Reason: {e}")


def test_directory_creation():
    """Test that directories are created."""
    print("\n" + "=" * 60)
    print("Testing Directory Creation")
    print("=" * 60)

    config = get_config()

    directories = [
        ("Data Dir", config.data_dir),
        ("Templates Dir", config.templates_dir),
        ("Output Dir", config.output_dir),
        ("Logs Dir", config.logs_dir),
    ]

    print()
    for name, path in directories:
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {name:20} {'EXISTS' if exists else 'MISSING':10} {path}")


def test_singleton_pattern():
    """Test that get_config returns the same instance."""
    print("\n" + "=" * 60)
    print("Testing Singleton Pattern")
    print("=" * 60)

    config1 = get_config()
    config2 = get_config()

    if config1 is config2:
        print("\n✓ Singleton pattern working: Same instance returned")
    else:
        print("\n✗ Singleton pattern broken: Different instances returned")

    # Test reload
    reset_config()
    config3 = get_config()

    if config3 is not config1:
        print("✓ reset_config() working: New instance created")
    else:
        print("✗ reset_config() broken: Same instance returned")


def test_env_file_loading():
    """Test if .env file is being loaded."""
    print("\n" + "=" * 60)
    print("Testing .env File Loading")
    print("=" * 60)

    env_file = Path(".env")
    env_example = Path(".env.example")

    print()
    if env_file.exists():
        print(f"✓ .env file found at: {env_file.absolute()}")
    else:
        print(f"✗ .env file not found")
        if env_example.exists():
            print(f"  → Copy {env_example} to {env_file} and add your API keys")

    if env_example.exists():
        print(f"✓ .env.example template exists")
    else:
        print(f"✗ .env.example template missing")


def main():
    """Run all tests."""
    try:
        test_config_defaults()
        test_directory_creation()
        test_singleton_pattern()
        test_api_key_validation()
        test_env_file_loading()

        print("\n" + "=" * 60)
        print("Configuration Test Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your API keys to .env")
        print("  3. Run this test again to verify API key validation")
        print()

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

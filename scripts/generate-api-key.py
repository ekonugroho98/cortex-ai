#!/usr/bin/env python3
"""
Generate secure API keys for CortexAI
"""
import secrets
import sys
import os


def generate_api_key():
    """Generate a secure random API key (64 character hex string)"""
    return secrets.token_hex(32)


def main():
    """Generate and display API key configuration"""
    print("=" * 60)
    print("CortexAI - API Key Generator")
    print("=" * 60)
    print()

    # Generate API key
    api_key = generate_api_key()

    print("Generated API Key:")
    print("-" * 60)
    print(api_key)
    print("-" * 60)
    print()

    # Show configuration
    print("Add this to your .env file:")
    print("-" * 60)
    print(f"API_KEYS=[\"{api_key}\"]")
    print("ENABLE_AUTH=true")
    print("-" * 60)
    print()

    # Show usage examples
    print("Usage Examples:")
    print("-" * 60)
    print(f"# Using curl with header")
    print(f'curl -H "X-API-Key: {api_key}" \\')
    print(f'  http://localhost:8000/api/v1/datasets')
    print()
    print(f"# Using curl with environment variable")
    print(f'export CORTEX_API_KEY="{api_key}"')
    print(f'curl -H "X-API-Key: $CORTEX_API_KEY" \\')
    print(f'  http://localhost:8000/api/v1/datasets')
    print("-" * 60)
    print()

    # Security reminders
    print("Security Reminders:")
    print("  ✓ Store API keys securely (use environment variables)")
    print("  ✓ Never commit API keys to git")
    print("  ✓ Rotate API keys regularly")
    print("  ✓ Use different keys for dev/staging/prod")
    print("  ✓ Monitor API key usage in logs")
    print()

    # Optional: Write directly to .env
    if len(sys.argv) > 1 and sys.argv[1] == "--write-env":
        env_path = ".env"
        if os.path.exists(env_path):
            print(f"Updating {env_path}...")
            with open(env_path, "a") as f:
                f.write(f'\n# Generated API Key\n')
                f.write(f'API_KEYS=["{api_key}"]\n')
                f.write(f'ENABLE_AUTH=true\n')
            print(f"✓ API key added to {env_path}")
        else:
            print(f"Error: {env_path} not found. Please create it first.")

    print()


if __name__ == "__main__":
    main()

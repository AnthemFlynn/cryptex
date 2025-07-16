#!/usr/bin/env python3
"""
Demonstration of New Zero-Config Cryptex Architecture

Shows how Cryptex eliminates config files entirely while maintaining 
maximum flexibility for edge cases.
"""

import asyncio
from cryptex.decorators.mcp import protect_tool
from cryptex.patterns import register_pattern, list_patterns


async def demo_zero_config():
    """Demonstrate zero-config usage (95% of users)."""
    
    print("🚀 Zero-Config Cryptex Demo")
    print("=" * 40)
    
    # Show built-in patterns
    print(f"\n📦 Built-in patterns: {', '.join(list_patterns())}")
    
    # Define tools with zero config
    @protect_tool(secrets=["openai_key"])
    async def ai_completion(prompt: str, api_key: str) -> str:
        return f"AI response to '{prompt}' using key: {api_key}"
    
    @protect_tool(secrets=["file_path", "github_token"])
    async def process_repo(file_path: str, token: str) -> str:
        return f"Processing {file_path} with GitHub token: {token}"
    
    # Test zero-config protection
    print("\n🔐 Zero-Config Protection:")
    
    # OpenAI key test
    fake_openai_key = "sk-" + "x" * 48
    result1 = await ai_completion("Hello world", fake_openai_key)
    print(f"   Input:  {fake_openai_key}")
    print(f"   Output: {result1}")
    print(f"   ✅ Protected: {fake_openai_key not in result1}")
    
    # Multiple secrets test
    fake_path = "/Users/johndoe/secret_project/README.md"
    fake_token = "ghp_" + "y" * 36
    result2 = await process_repo(fake_path, fake_token)
    print(f"\n   Path Input:  {fake_path}")
    print(f"   Token Input: {fake_token}")
    print(f"   Output:      {result2}")
    print(f"   ✅ Path Protected:  {fake_path not in result2}")
    print(f"   ✅ Token Protected: {fake_token not in result2}")


async def demo_custom_patterns():
    """Demonstrate custom pattern registration (5% of users)."""
    
    print("\n\n🛠️  Custom Pattern Registration (Advanced)")
    print("=" * 45)
    
    # Register custom patterns
    register_pattern(
        name="slack_token",
        regex=r"xoxb-[0-9-a-zA-Z]{51}",
        placeholder="{{SLACK_TOKEN}}",
        description="Slack bot token"
    )
    
    register_pattern(
        name="custom_api_key",
        regex=r"myapp-[a-f0-9]{32}",
        placeholder="{{CUSTOM_API_KEY}}",
        description="MyApp API key"
    )
    
    print(f"📦 Available patterns: {', '.join(list_patterns())}")
    
    # Use custom patterns in decorators
    @protect_tool(secrets=["slack_token", "custom_api_key"])
    async def custom_integration(slack_token: str, api_key: str) -> str:
        return f"Slack: {slack_token}, API: {api_key}"
    
    # Test custom protection
    fake_slack = "xoxb-" + "1234567890-1234567890-" + "x" * 24
    fake_custom = "myapp-" + "a1b2c3d4" * 4
    
    result = await custom_integration(fake_slack, fake_custom)
    
    print(f"\n🔐 Custom Pattern Protection:")
    print(f"   Slack Input:  {fake_slack}")
    print(f"   Custom Input: {fake_custom}")
    print(f"   Output:       {result}")
    print(f"   ✅ Slack Protected:  {fake_slack not in result}")
    print(f"   ✅ Custom Protected: {fake_custom not in result}")


def demo_architecture_benefits():
    """Show the benefits of the new architecture."""
    
    print("\n\n🏗️  Architecture Benefits")
    print("=" * 30)
    
    print("✅ Zero Configuration Required")
    print("   • No config files (cryptex.toml)")
    print("   • No environment variables")
    print("   • No setup or initialization")
    
    print("\n✅ Middleware Library Principles")
    print("   • Lightweight (no file I/O)")
    print("   • Fast startup (no config loading)")
    print("   • No external dependencies")
    print("   • Predictable behavior")
    
    print("\n✅ Developer Experience")
    print("   • One decorator line = complete protection")
    print("   • Built-in patterns for 95% of use cases")
    print("   • Simple registration API for edge cases")
    print("   • All configuration in version-controlled code")
    
    print("\n✅ Security Benefits")
    print("   • No config file injection attacks")
    print("   • No parsing vulnerabilities")
    print("   • No file system dependencies")
    print("   • Zero attack surface from configuration")


async def main():
    """Run the complete demo."""
    await demo_zero_config()
    await demo_custom_patterns()
    demo_architecture_benefits()
    
    print("\n\n🎉 Config Files Eliminated Successfully!")
    print("💡 Cryptex: Bulletproof secrets isolation with zero cognitive overhead")


if __name__ == "__main__":
    asyncio.run(main())
"""
Test Secret Samples and Data

Centralized test data for consistent testing across the suite.
Provides realistic secret patterns for testing secret detection and sanitization.
"""

# Sample API Keys
SAMPLE_OPENAI_KEYS = [
    "sk-1234567890abcdefghijklmnopqrstuvwxyzABCDEF123456",
    "sk-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnop789012",
    "sk-zyxwvutsrqponmlkjihgfedcba9876543210FEDCBA345678",
]

SAMPLE_ANTHROPIC_KEYS = [
    "sk-ant-api03-1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ123456",
    "sk-ant-api03-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz789012",
]

SAMPLE_GITHUB_TOKENS = [
    "ghp_1234567890abcdefghijklmnopqrstuvwxyz",
    "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef12",
    "ghp_zyxwvutsrqponmlkjihgfedcba98765432",
]

# Sample Database URLs
SAMPLE_DATABASE_URLS = [
    "postgresql://user:pass@localhost:5432/mydb",
    "mysql://root:secret@db.example.com:3306/app",
    "sqlite:///path/to/database.db",
    "redis://localhost:6379/0",
    "mongodb://user:password@cluster.mongodb.net/database",
]

# Sample File Paths
SAMPLE_FILE_PATHS = [
    "/Users/john/documents/secret.txt",
    "/home/jane/config/api_keys.json",
    "/Users/test/data/credentials.env",
    "/home/admin/.ssh/id_rsa",
]

# Sample Mixed Content (for integration testing)
SAMPLE_MIXED_CONTENT = {
    "config": {
        "api_key": SAMPLE_OPENAI_KEYS[0],
        "db_url": SAMPLE_DATABASE_URLS[0],
        "debug_file": SAMPLE_FILE_PATHS[0],
    },
    "tokens": {
        "github": SAMPLE_GITHUB_TOKENS[0],
        "anthropic": SAMPLE_ANTHROPIC_KEYS[0],
    },
}

# Invalid/Non-Secret Samples (for negative testing)
NON_SECRET_SAMPLES = [
    "sk-short",  # Too short for OpenAI
    "not-an-api-key",  # Wrong format
    "sk-proj-",  # Missing key part
    "regular-string-with-dashes",
    "http://not-a-database-url.com",
    "just-a-file.txt",  # Not a full path
]

# Expected Placeholders
EXPECTED_PLACEHOLDERS = {
    "openai_key": "{{OPENAI_API_KEY}}",
    "anthropic_key": "{{ANTHROPIC_API_KEY}}",
    "github_token": "{{GITHUB_TOKEN}}",
    "database_url": "{{DATABASE_URL}}",
    "file_path": "{{FILE_PATH}}",
}


def get_sample_secret(secret_type: str, index: int = 0) -> str:
    """Get a sample secret by type and index."""
    samples = {
        "openai_key": SAMPLE_OPENAI_KEYS,
        "anthropic_key": SAMPLE_ANTHROPIC_KEYS,
        "github_token": SAMPLE_GITHUB_TOKENS,
        "database_url": SAMPLE_DATABASE_URLS,
        "file_path": SAMPLE_FILE_PATHS,
    }
    return samples[secret_type][index]


def get_expected_placeholder(secret_type: str) -> str:
    """Get expected placeholder for a secret type."""
    return EXPECTED_PLACEHOLDERS[secret_type]

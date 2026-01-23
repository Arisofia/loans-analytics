#!/usr/bin/env python3
"""
Data Architecture Discovery Tool
Searches codebase for database, storage, and API connections
"""

import os
import re
from collections import defaultdict
from pathlib import Path

# Patterns to search for
PATTERNS = {
    "postgresql": [
        r'postgresql://.*?(?:\s|\'|"|$)',
        r'postgres://.*?(?:\s|\'|"|$)',
        r"host=.*?dbname=",
    ],
    "mysql": [
        r'mysql://.*?(?:\s|\'|"|$)',
        r'mysql\+pymysql://.*?(?:\s|\'|"|$)',
    ],
    "azure_sql": [
        r"Driver={ODBC Driver.*?}.*?Server=",
        r"azure\.sql",
        r"database\.windows\.net",
    ],
    "cosmos_db": [
        r"cosmosdb",
        r"cosmos\.azure",
        r"AccountEndpoint=https://.*?\.documents\.azure\.com",
    ],
    "blob_storage": [
        r"https://.*?\.blob\.core\.windows\.net",
        r"azure\.storage\.blob",
        r"BlobServiceClient",
    ],
    "supabase": [
        r"supabase\.co",
        r"supabase\.js",
        r"PostgrestClient",
    ],
    "api_endpoints": [
        r"https://api\.(hubapi\.com|openai\.com|cascade)",
        r'api_url.*?=.*?["\']https://',
    ],
    "env_vars": [
        r"(DATABASE_URL|DB_HOST|DB_NAME|STORAGE|API_KEY|CONNECTION)",
    ],
}

EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    ".pytest_cache",
    "dist",
    "build",
}
EXCLUDED_EXTENSIONS = {".pyc", ".o", ".so", ".dylib", ".png", ".jpg", ".jpeg", ".gif"}


def search_files(root_dir="."):
    """Search codebase for data architecture patterns"""
    findings = defaultdict(list)

    for root, dirs, files in os.walk(root_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for file in files:
            # Skip excluded extensions
            if any(file.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
                continue

            filepath = Path(root) / file
            if not filepath.is_file():
                continue

            try:
                # Try to read file as text
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                    for category, patterns in PATTERNS.items():
                        for pattern in patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                # Extract context (line around match)
                                lines = content[: match.start()].split("\n")
                                line_num = len(lines)

                                findings[category].append(
                                    {
                                        "file": str(filepath),
                                        "line": line_num,
                                        "match": match.group(0)[:80],  # First 80 chars
                                    }
                                )
            except (UnicodeDecodeError, IOError):
                pass

    return findings


def print_report(findings):
    """Print discovery report"""
    print("\n" + "=" * 70)
    print("DATA ARCHITECTURE DISCOVERY REPORT")
    print("=" * 70 + "\n")

    if not findings:
        print("❌ No data architecture patterns found in codebase")
        print("\n📋 Critical Question: Where is production loan data stored?\n")
        return

    for category, items in findings.items():
        if items:
            print(f"✅ {category.upper()}")
            print("-" * 70)
            for item in items[:5]:  # Limit to first 5 per category
                print(f"  📄 {item['file']}:{item['line']}")
                print(f"     → {item['match']}")
            if len(items) > 5:
                print(f"  ... and {len(items) - 5} more")
            print()


if __name__ == "__main__":
    findings = search_files()
    print_report(findings)

    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print(
        """
1. Review findings above for database/storage connections
2. If no PostgreSQL/MySQL/Azure SQL found:
   → Check if data stored in Blob Storage (CSV/Parquet files)
   → Check if data stored in external Cascade API
   → Check if data stored in HubSpot directly

3. Connect to identified data sources:
   → Get connection strings from Azure Key Vault
   → Test connectivity: psql, mysql, az storage blob list, etc.
   → Verify data freshness and integrity

4. Map data flow in ARCHITECTURE.md:
   - Where does data come from (sources)?
   - Where does it get stored (storage)?
   - How do pipelines access it?
   - How does dashboard query it?
"""
    )

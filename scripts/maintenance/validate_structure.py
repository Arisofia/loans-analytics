#!/usr/bin/env python3
"""
ABACO INFRASTRUCTURE VALIDATOR v2.2
Role: Lead Architect
Purpose: Dynamic validation of the fintech architecture based on .repo-structure.json.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Color codes for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    END = "\033[0m"
    BOLD = "\033[1m"

class AbacoValidator:
    def __init__(self, verbose: bool = False):
        self.repo_root = Path(__file__).resolve().parents[2]
        self.structure_file = self.repo_root / ".repo-structure.json"
        self.verbose = verbose
        self.found: List[str] = []
        self.missing: List[str] = []
        self.warnings: List[str] = []

    def _load_manifest(self) -> Dict:
        """Parses the source of truth for the repository architecture."""
        if not self.structure_file.exists():
            print(f"{Colors.RED}CRITICAL ERROR: {self.structure_file} missing.{Colors.END}")
            sys.exit(1)
            
        try:
            with open(self.structure_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"{Colors.RED}CRITICAL ERROR: Failed to parse {self.structure_file}: {e}{Colors.END}")
            sys.exit(1)

    def _check_path(self, relative_path: str, purpose: str = "N/A") -> bool:
        """Check if a path exists and record the result."""
        full_path = self.repo_root / relative_path
        if full_path.exists():
            self.found.append(relative_path)
            if self.verbose:
                print(f"{Colors.GREEN}✅{Colors.END} {relative_path} {Colors.CYAN}({purpose}){Colors.END}")
            return True
        else:
            self.missing.append(relative_path)
            print(f"{Colors.RED}❌ MISSING:{Colors.END} {relative_path} {Colors.YELLOW}({purpose}){Colors.END}")
            return False

    def validate(self):
        """Executes a non-negotiable audit of the file system."""
        manifest = self._load_manifest()
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}--- ABACO ARCHITECTURE AUDIT v2.2 ---{Colors.END}")
        print(f"Repository: {self.repo_root.name}")
        print(f"Status defined in manifest: {manifest.get('status', 'UNKNOWN')}")
        print("=" * 60)

        # 1. Validate Workflow Folders and explicit Files
        print(f"\n{Colors.BOLD}{Colors.CYAN}1. Production Workflow Validation{Colors.END}")
        workflow = manifest.get("ACTIVE_PRODUCTION_WORKFLOW", {})
        for folder in workflow.get("folders", []):
            path_str = folder.get("path")
            if not path_str: continue
            
            # Check the folder/file itself
            self._check_path(path_str, folder.get("purpose", "Workflow Component"))
            
            # Check explicit files within that folder
            for file_name in folder.get("files", []):
                file_rel_path = str(Path(path_str) / file_name)
                self._check_path(file_rel_path, "Explicit workflow file")

        # 2. Validate Process Phases
        print(f"\n{Colors.BOLD}{Colors.CYAN}2. Process Phase Implementation Check{Colors.END}")
        phases = manifest.get("PROCESS_PHASES", {})
        for phase_name, phase_def in phases.items():
            loc = phase_def.get("location")
            if loc:
                self._check_path(loc, f"Phase implementation: {phase_name}")
            
            for support in phase_def.get("support_files", []):
                self._check_path(support, f"Support for {phase_name}")

        # 3. Validate External Integration Configs
        print(f"\n{Colors.BOLD}{Colors.CYAN}3. External Integration Configurations{Colors.END}")
        integrations = manifest.get("EXTERNAL_INTEGRATIONS", {}).get("tools", [])
        for tool in integrations:
            config_str = tool.get("config", "")
            # Split comma-separated configs if any
            configs = [c.strip() for c in config_str.split(",") if c.strip() and not c.startswith(".env")]
            for cfg in configs:
                self._check_path(cfg, f"Config for {tool.get('name')}")

        # 4. Final Summary
        total = len(self.found) + len(self.missing)
        completion_rate = (len(self.found) / total * 100) if total > 0 else 0
        
        print("\n" + "=" * 60)
        print(f"{Colors.BOLD}AUDIT SUMMARY{Colors.END}")
        print(f"Components Found:   {Colors.GREEN}{len(self.found)}{Colors.END}")
        print(f"Components Missing: {Colors.RED}{len(self.missing)}{Colors.END}")
        print(f"Completion Rate:    {Colors.BOLD}{completion_rate:.1f}%{Colors.END}")
        
        if len(self.missing) == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}RESULT: INFRASTRUCTURE IS ROBUST & PREDICTABLE ✅{Colors.END}")
            return True
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}RESULT: SYSTEM FRAGILITY DETECTED ❌{Colors.END}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Production-grade Infrastructure Validator")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all checks")
    args = parser.parse_args()

    validator = AbacoValidator(verbose=args.verbose)
    success = validator.validate()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

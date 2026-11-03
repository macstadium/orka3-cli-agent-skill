#!/usr/bin/env python3
"""
Orka CLI Skill Test Harness

Installs the skill from this repo and analyzes Claude Code sessions
to measure reference-file routing efficiency.

Usage:
  python3 tests/test-harness.py setup      # Install skill from repo
  python3 tests/test-harness.py analyze     # Analyze recent sessions
  python3 tests/test-harness.py queries     # Print test queries
"""

import json
import os
import re
import shutil
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


def normalize(text: str) -> str:
    """Strip punctuation and extra whitespace for fuzzy matching."""
    return re.sub(r'[^\w\s]', '', text.lower()).strip()


# Paths
HOME = Path.home()
SKILL_DIR = HOME / ".claude" / "skills" / "orka-cli"
REPO_SKILL_DIR = Path(__file__).resolve().parent.parent / "skill"
SESSIONS_DIR = HOME / ".claude" / "projects"

# Test queries (subset for quick testing — full set in test-queries.md)
TEST_QUERIES = [
    ("Q1", "Tier 1", "Deploy a VM with macOS Sonoma"),
    ("Q2", "Tier 1", "Show me all my VMs"),
    ("Q3", "Tier 1", "How do I connect to my VM?"),
    ("Q5", "Tier 2", "Set up a service account for Jenkins"),
    ("Q8", "Tier 3", "How do I create a golden image for my team?"),
    ("Q12", "Tier 4", "Who has access to the production namespace?"),
    ("Q18", "Tier 6", "I'm getting an authentication error"),
    ("Q22", "Tier 7", "How do I suspend an Intel VM?"),
    ("Q25", "Tier 8", "Best practices for remote developers using Orka?"),
    ("Q27", "Tier 8", "Where can I find audit logs for VM operations?"),
]


def setup_skill():
    """Install the skill from this repo's skill/ directory."""
    if not REPO_SKILL_DIR.exists():
        print(f"Error: skill/ directory not found at {REPO_SKILL_DIR}")
        print("Run this script from the repo root: python3 tests/test-harness.py setup")
        sys.exit(1)

    if SKILL_DIR.exists():
        shutil.rmtree(SKILL_DIR)
    shutil.copytree(REPO_SKILL_DIR, SKILL_DIR)

    # Verify
    refs = list((SKILL_DIR / "references").iterdir()) if (SKILL_DIR / "references").exists() else []
    ref_names = [r.name for r in refs]

    print(f"\n{'='*50}")
    print(f"Installed skill from {REPO_SKILL_DIR}")
    print(f"{'='*50}")
    print(f"Reference files: {ref_names}")
    print(f"\nStart a NEW Claude Code session and run these queries:")
    print("-" * 50)
    for qid, tier, query in TEST_QUERIES:
        print(f"  {qid} ({tier}): \"{query}\"")
    print("-" * 50)
    print(f"\nAfter testing, run: python3 tests/test-harness.py analyze")


def find_recent_sessions(hours: int = 4) -> list:
    """Find session files modified in the last N hours."""
    cutoff = datetime.now() - timedelta(hours=hours)
    sessions = []

    for project_dir in SESSIONS_DIR.iterdir():
        if project_dir.is_dir():
            for jsonl in project_dir.glob("*.jsonl"):
                if jsonl.name.startswith("agent-"):
                    continue
                mtime = datetime.fromtimestamp(jsonl.stat().st_mtime)
                if mtime > cutoff:
                    sessions.append((jsonl, mtime))

    return sorted(sessions, key=lambda x: x[1], reverse=True)


def analyze_session(session_path: Path) -> dict:
    """Analyze a session for skill-related tool calls."""
    results = {
        "path": str(session_path),
        "queries": [],
        "skill_reads": [],
        "total_reads": 0,
        "skill_md_reads": 0,
        "ref_reads": 0,
    }

    current_query = None
    query_reads = defaultdict(list)

    with open(session_path, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line)
                msg = entry.get('message', {})

                # Track skill file reads
                if msg.get('role') == 'assistant':
                    content = msg.get('content', [])
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get('type') == 'tool_use':
                                if item.get('name') == 'Read':
                                    path = item.get('input', {}).get('file_path', '')
                                    if 'orka-cli' in path.lower():
                                        if '/.claude/skills/orka-cli/' in path:
                                            short_path = path.split('orka-cli/')[-1]
                                        elif '/skill/' in path:
                                            short_path = path.split('/skill/')[-1]
                                        else:
                                            short_path = path.split('orka-cli/')[-1]

                                        results['skill_reads'].append(short_path)
                                        results['total_reads'] += 1

                                        if short_path == 'SKILL.md':
                                            results['skill_md_reads'] += 1
                                        else:
                                            results['ref_reads'] += 1

                                        if current_query:
                                            query_reads[current_query].append(short_path)

                # Track user queries
                if entry.get('type') == 'user':
                    content = msg.get('content', '')
                    if isinstance(content, str) and len(content) > 10:
                        norm_content = normalize(content)
                        for qid, tier, query in TEST_QUERIES:
                            if normalize(query) in norm_content:
                                current_query = qid
                                results['queries'].append(qid)
                                break

            except json.JSONDecodeError:
                pass

    results['query_reads'] = dict(query_reads)
    return results


def analyze():
    """Analyze recent sessions for skill routing efficiency."""
    print("\n" + "="*60)
    print("ANALYZING RECENT SESSIONS")
    print("="*60)

    sessions = find_recent_sessions(hours=4)

    if not sessions:
        print("No recent sessions found. Run some tests first!")
        return

    print(f"\nFound {len(sessions)} recent sessions:\n")

    skill_sessions = []

    for session_path, mtime in sessions[:10]:
        results = analyze_session(session_path)

        if results['total_reads'] > 0:
            time_str = mtime.strftime("%H:%M:%S")
            print(f"  {time_str} | {results['total_reads']:2} reads | queries: {results['queries']}")
            skill_sessions.append(results)

    if not skill_sessions:
        print("  No sessions with skill reads found.")
        return

    # Summary
    total_reads = sum(r['total_reads'] for r in skill_sessions)
    total_queries = sum(len(r['queries']) for r in skill_sessions)
    skill_md = sum(r['skill_md_reads'] for r in skill_sessions)
    refs = sum(r['ref_reads'] for r in skill_sessions)

    all_files = []
    for r in skill_sessions:
        all_files.extend(r['skill_reads'])
    unique_files = set(all_files)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"  Sessions analyzed: {len(skill_sessions)}")
    print(f"  Test queries matched: {total_queries}")
    print(f"  Total skill reads: {total_reads}")
    print(f"    - SKILL.md: {skill_md}")
    print(f"    - Reference files: {refs}")
    if total_queries > 0:
        print(f"  Avg reads per query: {total_reads / total_queries:.2f}")
    print(f"  Unique files accessed: {len(unique_files)}")
    for f in sorted(unique_files):
        print(f"    - {f}")


def print_queries():
    """Print the test queries for easy copy/paste."""
    print("\n" + "="*60)
    print("TEST QUERIES")
    print("="*60)
    for qid, tier, query in TEST_QUERIES:
        print(f"\n{qid} ({tier}):")
        print(f"  {query}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("Commands:")
        print("  setup    - Install skill from repo's skill/ directory")
        print("  analyze  - Analyze recent Claude Code sessions")
        print("  queries  - Print test queries for copy/paste")
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "setup":
        setup_skill()
    elif cmd == "analyze":
        analyze()
    elif cmd == "queries":
        print_queries()
    else:
        print(f"Unknown command: {cmd}")
        print("Use: setup, analyze, or queries")
        sys.exit(1)


if __name__ == "__main__":
    main()

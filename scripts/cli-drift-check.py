#!/usr/bin/env python3
"""Check the skill's CLI commands and flags against the CLI's own help.

The CLI has a hidden `docs generate` command that writes every command's
usage, examples, and flags to one Markdown file. This script runs it, reads
each command's aliases from `--help`, and compares the result with the skill:

  errors    a command heading, an example command, or an example flag that
            the CLI doesn't have, or an Options list entry the CLI doesn't have
  warnings  a CLI flag that a command reference's Options list leaves out

An example is any line in a fenced code block that starts with `orka3` or
`orka` (also after `$ `, `- `, `$(`, `|`, `&&`, or `;`). Lines ending in `\\`
are joined first.

The generated help leaves out removed commands and deprecated (hidden) ones.
A command missing from it is skipped if its section, or the intro of its
enclosing '##' group, says "Removed in Orka X" or "Deprecated in Orka X".

From 4.0 the CLI is `orka`, and `orka3` lines are 3.x-only. When checking a
4.x `orka` CLI, `orka3` lines are skipped; when checking a 3.x `orka3` CLI,
`orka` lines are skipped.

Usage:
  python3 scripts/cli-drift-check.py --cli ./orka3 [--binary-name orka3] [--strict]

Run it from the repo root. Exits 1 if there are errors (or warnings, with --strict).
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_DIR = "orka3-cli"
COMMAND_REFS = "orka3-cli/references/commands"
LONG_FLAG_RE = re.compile(r"(?<![\w-])(--[a-z][\w-]*)")
# A generated option line: "  -o, --output string   help" or "      --all   help"
OPTION_LINE_RE = re.compile(r"^\s*(?:(-\w),\s+)?(--[a-z][\w-]*)(?:\s(\w+))?", re.M)
REMOVED_RE = re.compile(r"(removed|deprecated) in orka", re.I)
IGNORED_FLAGS = {"--help", "-h"}
# Where a command starts inside a code line: line start (after "$ " or "- "),
# or after a subshell, pipe, "&&", or ";".
EXAMPLE_START_RE = re.compile(r"(?:^(?:\$\s+|-\s+)?|\$\(|\|\s*|&&\s*|;\s*)\b(orka3?)\s+(?=[a-z<\[-])")
# Where a command ends: a comment, pipe, "&&", "||", ";", closing subshell, or redirect.
EXAMPLE_END_RE = re.compile(r"\s#|\||&&|;|\)|`|\s\d?>\s|\s>>?\S")
# Skill headings like "### orka3 imagecache add (alias: ic)" or "## orka3 vm push (Apple Silicon only)".
HEADING_RE = re.compile(r"^#{2,6}\s+`?(orka3?)\s+([a-z][\w-]*(?:\s+[a-z][\w-]*)*)`?")
# The start of an Options list: "**Options:**", "**Intel-only Options:**", and so on.
OPTIONS_LABEL_RE = re.compile(r"^\*\*[^*\n]*Options:\*\*\s*$")
OPTIONS_ENTRY_RE = re.compile(r"^\s*(?:[-*]\s+|\|\s*)`(?:-\w,\s+)?(--[a-z][\w-]*)")
COMMAND_WORD_RE = re.compile(r"^[a-z][a-z0-9-]*$")
PLACEHOLDER_KUBECONFIG = """\
apiVersion: v1
kind: Config
clusters:
- name: placeholder
  cluster:
    server: https://127.0.0.1:6443
users:
- name: placeholder
  user:
    token: placeholder
contexts:
- name: placeholder
  context:
    cluster: placeholder
    user: placeholder
current-context: placeholder
"""


class Cli:
    """Commands, flags, and aliases of one CLI build."""

    def __init__(self, binary, commands, aliases):
        self.binary = binary          # "orka" or "orka3"
        self.commands = commands      # {"vm deploy": {"--image": True, "-i": True, "--tag-required": False}}
        self.aliases = aliases        # {("", "sa"): "serviceaccount", ("vm-config", "ls"): "vm-config list"}
        self.groups = {c.rsplit(" ", 1)[0] if " " in c else "" for c in commands if c}
        # Flags that take a value anywhere in the CLI, so their values aren't read as commands.
        self.value_flags = {f for flags in commands.values() for f, takes in flags.items() if takes}

    def resolve(self, words):
        """Walk command words (aliases allowed). Return (command, words used, unknown word or None)."""
        current = ""
        used = 0
        for w in words:
            if current not in self.groups:
                break
            candidate = f"{current} {w}".strip()
            if candidate in self.commands:
                current = candidate
            elif (current, w) in self.aliases:
                current = self.aliases[(current, w)]
            else:
                # A group takes no arguments, so a plain word after one is an unknown subcommand.
                return current, used, w if COMMAND_WORD_RE.match(w) else None
            used += 1
        return current, used, None


def run(cmd, **kwargs):
    return subprocess.run(cmd, capture_output=True, text=True, check=False, **kwargs)


def load_cli(cli_path, binary_name=None):
    """Run `docs generate` and `--help` for each command, and return a Cli."""
    cli_path = str(Path(cli_path).resolve())
    with tempfile.TemporaryDirectory() as tmp:
        # Every CLI command except a short allow-list (not including `docs`) first loads a
        # kubeconfig. It only parses it and never contacts the server, so a placeholder works.
        kubeconfig = Path(tmp, "kubeconfig")
        kubeconfig.write_text(PLACEHOLDER_KUBECONFIG)
        env = dict(os.environ, KUBECONFIG=str(kubeconfig))
        res = run([cli_path, "docs", "generate", "-d", "gen"], cwd=tmp, env=env)
        generated = sorted(Path(tmp, "gen").glob("*-all-in-one.md"))
        if res.returncode != 0 or not generated:
            sys.exit(f"`{cli_path} docs generate` failed:\n{res.stdout}{res.stderr}")
        text = generated[0].read_text()

        first = re.search(r"^## (orka3?)\b", text, re.M)
        if not first:
            sys.exit(f"{generated[0]}: no '## orka' sections found. Is this the `docs generate` output?")
        binary = binary_name or first.group(1)
        commands = {}
        for m in re.finditer(rf"^## {first.group(1)}(?: ([^\n]+))?\n(.*?)(?=^<a name=|\Z)", text, re.S | re.M):
            name = (m.group(1) or "").strip()
            flags = {"--help": False, "-h": False}
            for block in re.findall(r"### Options[^\n]*\n\n```\n(.*?)```", m.group(2), re.S):
                for short, long_, kind in OPTION_LINE_RE.findall(block):
                    takes_value = bool(kind)
                    flags[long_] = takes_value
                    if short:
                        flags[short] = takes_value
            commands[name] = flags

        aliases = {}
        for name in commands:
            if not name:
                continue
            res = run([cli_path, *name.split(), "--help"], cwd=tmp, env=env)
            m = re.search(r"^Aliases:\n\s+(.+)$", res.stdout, re.M)
            if not m:
                continue
            parent = name.rsplit(" ", 1)[0] if " " in name else ""
            for alias in (a.strip() for a in m.group(1).split(",")):
                if alias:
                    aliases[(parent, alias)] = name
    return Cli(binary, commands, aliases)


def sections(lines):
    """Yield (start, end, heading line or None, group intro) for each heading-delimited section.

    The group intro is the text between the enclosing '##' (or '#') heading and its first
    subheading, where a page often notes that a whole group of commands is removed or deprecated.
    """
    heads = [(0, 1, None)]
    in_code = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:  # shell comments like "# Deploy a VM" aren't headings
            continue
        h = re.match(r"^(#{1,6}) ", line)
        if h:
            heads.append((i, len(h.group(1)), line))
    intro = ""
    for idx, (start, level, heading) in enumerate(heads):
        end = heads[idx + 1][0] if idx + 1 < len(heads) else len(lines)
        if level <= 2:
            intro = "\n".join(lines[start + 1:end])
        yield start, end, heading, intro


def code_lines(lines, start, end):
    """Yield (line number, logical line) for each code line in lines[start:end], joining `\\` continuations."""
    in_code = False
    pending, pending_line = "", None
    for i in range(start, end):
        line = lines[i]
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if not in_code:
            continue
        if pending_line is None:
            pending_line = i + 1
        stripped = line.rstrip()
        if stripped.endswith("\\"):
            pending += stripped[:-1] + " "
            continue
        yield pending_line, (pending + stripped).strip()
        pending, pending_line = "", None


def examples(logical):
    """Yield (binary, argument text) for each CLI invocation in one code line."""
    if logical.startswith("#"):
        return
    for m in EXAMPLE_START_RE.finditer(logical):
        rest = logical[m.end():]
        stop = EXAMPLE_END_RE.search(rest)
        yield m.group(1), rest[: stop.start()] if stop else rest


def options_flags(lines, start, end):
    """Return the long flags listed under **...Options:** labels in lines[start:end]."""
    flags = set()
    in_list = False
    for i in range(start, end):
        line = lines[i]
        if OPTIONS_LABEL_RE.match(line):
            in_list = True
            continue
        if in_list:
            m = OPTIONS_ENTRY_RE.match(line)
            if m:
                flags.add(m.group(1))
            elif line.strip() and not line.lstrip().startswith("|"):
                in_list = False
    return flags


def check_example(cli, binary, args, path, line, context, findings):
    tokens = args.split()
    words, flags = [], []
    skip_value = False
    for tok in tokens:
        if skip_value:
            skip_value = False
            continue
        if re.match(r"^--?[A-Za-z]", tok):
            flag = tok.split("=", 1)[0]
            if re.match(r"^-[A-Za-z]{2,}$", flag):  # not a flag we can check, like -abc
                continue
            flags.append(flag)
            skip_value = "=" not in tok and flag in cli.value_flags
            continue
        words.append(tok)
    target, _, unknown = cli.resolve(words)
    if unknown:
        if not REMOVED_RE.search(context):
            findings.append(("error", path, line,
                             f"`{binary} {target} {unknown}`: example uses a command the CLI doesn't have".replace("  ", " ")))
        return
    if not target:
        return
    for flag in flags:
        if flag not in cli.commands[target] and flag not in IGNORED_FLAGS:
            findings.append(("error", path, line,
                             f"`{binary} {target}`: example uses `{flag}`, which the CLI doesn't have"))


def check_file(path, cli, findings, stats):
    lines = path.read_text().split("\n")
    is_command_ref = Path(COMMAND_REFS) in path.parents
    for start, end, heading, intro in sections(lines):
        body = "\n".join(lines[start + 1:end])
        context = body + "\n" + intro

        # A command heading: the command must exist, and its Options list must match.
        m = HEADING_RE.match(heading) if heading else None
        if m and m.group(1) == cli.binary:
            name = m.group(2)
            target, used, unknown = cli.resolve(name.split())
            if unknown or used < len(name.split()):
                if not (REMOVED_RE.search(heading) or REMOVED_RE.search(context)):
                    findings.append(("error", path, start + 1,
                                     f"`{cli.binary} {name}`: not in the CLI's help. Remove it, or mark it removed or deprecated"))
            elif is_command_ref:
                documented = options_flags(lines, start + 1, end)
                long_flags = {f for f in cli.commands[target] if f.startswith("--")}
                for flag in sorted(documented - long_flags - IGNORED_FLAGS):
                    findings.append(("error", path, start + 1,
                                     f"`{cli.binary} {target}`: Options lists `{flag}`, which the CLI doesn't have"))
                if documented:
                    for flag in sorted(long_flags - documented - IGNORED_FLAGS):
                        findings.append(("warning", path, start + 1,
                                         f"`{cli.binary} {target}`: CLI flag `{flag}` isn't in the Options list"))
        elif m:
            stats["skipped"] += 1

        # Example lines in this section's code blocks.
        for line_no, logical in code_lines(lines, start + 1, end):
            for binary, args in examples(logical):
                if binary != cli.binary:
                    stats["skipped"] += 1
                    continue
                stats["examples"] += 1
                check_example(cli, binary, args, path, line_no, context + "\n" + logical, findings)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cli", required=True, help="path to the CLI binary to check against")
    parser.add_argument("--binary-name", choices=["orka", "orka3"],
                        help="the checked CLI's name (default: read from its generated help)")
    parser.add_argument("--files", nargs="*", help=f"Markdown files to check (default: every file under {SKILL_DIR}/)")
    parser.add_argument("--strict", action="store_true", help="also fail on warnings")
    args = parser.parse_args()

    cli = load_cli(args.cli, args.binary_name)
    if args.files:
        pages = [Path(p) for p in args.files]
    else:
        pages = sorted(Path(SKILL_DIR).rglob("*.md"))
    if not pages:
        sys.exit(f"No Markdown files found under {SKILL_DIR}/. Run this from the repo root.")

    findings = []
    stats = {"examples": 0, "skipped": 0}
    for page in pages:
        check_file(page, cli, findings, stats)

    errors = [f for f in findings if f[0] == "error"]
    warnings = [f for f in findings if f[0] == "warning"]
    in_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    for level, path, line, msg in findings:
        if in_ci:
            print(f"::{level} file={path},line={line}::{msg}")
        else:
            print(f"{level.upper():7} {path}:{line}  {msg}")

    other = "orka3" if cli.binary == "orka" else "orka"
    summary = (f"Checked {len(pages)} files ({stats['examples']} example commands) against `{cli.binary}` "
               f"({len(cli.commands)} commands): {len(errors)} errors, {len(warnings)} warnings. "
               f"Skipped {stats['skipped']} `{other}` lines and headings.")
    print(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(f"## CLI drift check\n\n{summary}\n\n")
            for level, path, line, msg in findings:
                f.write(f"- **{level}** `{path}:{line}`: {msg}\n")

    sys.exit(1 if errors or (args.strict and warnings) else 0)


if __name__ == "__main__":
    main()

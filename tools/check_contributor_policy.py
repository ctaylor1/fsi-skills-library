#!/usr/bin/env python3
"""Reject contributor-credit trailers and AI authorship claims in repository work."""

import argparse
import json
import pathlib
import re
import subprocess
import sys


AI_IDENTITY = re.compile(
    r'claude|anthropic|codex|openai|chatgpt|copilot|gemini|cursor|aider|windsurf|'
    r'amazon[ -]+q\b|\bkiro\b|\bdevin\b|\btabnine\b|\bcodeium\b|'
    r'\bAI\b|\bGPT(?:\b|[- ])|deepseek|\bgrok\b|\bqwen\b|'
    r'language[ -]+model|\bLLM\b|\[bot\]',
    re.IGNORECASE,
)
CREDIT = re.compile(
    r'^\s*(?:[#*/>!;\-]+\s*)?(?:'
    r'(?:(?:co[ -]?)?authored|signed[ -]off|reviewed|assisted|suggested|generated|'
    r'written|created|implemented|developed|contributed|coded|built|powered)'
    r'[ -](?:by|with)\s*:|claude-session\s*:|'
    r'(?:(?:this|the)\s+(?:code|file|project|repository)\s+(?:was\s+)?)?'
    r'(?:generated|written|authored|coded|implemented|developed|created|built|'
    r'contributed|reviewed|assisted|powered)\s+(?:by|with)\b|'
    r'(?:authors?|contributors?|credits?|acknowledg(?:e)?ments?)\s*(?:[:=]|$)|'
    r'(?:special\s+)?thanks\s+to\b|'
    r'@author\b)',
    re.IGNORECASE,
)
COAUTHOR = re.compile(r'^\s*co[ -]?authored[ -]?by\s*:', re.IGNORECASE)


def git(*args):
    return subprocess.check_output(['git', *args])


def violations(text, message=False):
    """Return credit lines, leaving operational model/tool references alone."""
    findings = []
    lines = text.splitlines()
    for number, line in enumerate(lines, 1):
        normalized = re.sub(r'^[^\w@]+', '', line)
        for decoration in ('**', '`', '"', "'"):
            normalized = normalized.replace(decoration, '')
        if message and COAUTHOR.search(normalized):
            findings.append(number)
        elif match := CREDIT.search(normalized):
            block = line
            # Only empty credit headings introduce a following contributor list.
            if not normalized[match.end():].strip():
                block = '\n'.join(lines[number - 1:number + 3])
            if AI_IDENTITY.search(block):
                findings.append(number)
    return findings


def check_files(staged):
    if staged:
        names = git('diff', '--cached', '--name-only', '-z', '--diff-filter=ACMR')
    else:
        names = git('ls-files', '-z')
    errors = []
    root = pathlib.Path(git('rev-parse', '--show-toplevel').decode().strip())
    for name in names.split(b'\0'):
        if not name:
            continue
        path = name.decode('utf-8', errors='surrogateescape')
        if staged:
            content = git('show', ':' + path)
        else:
            target = root / path
            if target.is_symlink() or not target.is_file():
                continue
            content = target.read_bytes()
        if b'\0' in content:
            continue
        for line in violations(content.decode('utf-8', errors='replace')):
            errors.append(f'{path}:{line}: AI contributor credit is prohibited')
    return errors


def check_history(ref):
    errors = []
    # Examine each ancestor, including all sides of merges, not just new commits.
    for oid in git('rev-list', ref).decode().splitlines():
        raw = git('cat-file', 'commit', oid).decode('utf-8', errors='replace')
        headers, message = raw.split('\n\n', 1)
        for line in headers.splitlines():
            if line.startswith(('author ', 'committer ')) and AI_IDENTITY.search(line):
                errors.append(f'{oid[:12]}: AI contributor identity is prohibited')
        if violations(message, message=True):
            errors.append(f'{oid[:12]}: contributor credit in commit message')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', action='store_true')
    parser.add_argument('--tree', action='store_true')
    parser.add_argument('--history', metavar='REF')
    parser.add_argument('--message', type=pathlib.Path)
    parser.add_argument('--event', type=pathlib.Path, help='GitHub event JSON; check PR title and body')
    parser.add_argument('--identities', action='store_true')
    args = parser.parse_args()
    if not any((args.staged, args.tree, args.history, args.message, args.event, args.identities)):
        parser.error('select --staged, --tree, --history REF, --message FILE, or --identities')
    errors = []
    if args.staged or args.tree:
        errors.extend(check_files(staged=args.staged))
    if args.history:
        errors.extend(check_history(args.history))
    if args.message:
        text = args.message.read_text(encoding='utf-8')
        if violations(text, message=True):
            errors.append('Commit message contains a prohibited contributor credit')
    if args.event:
        pull_request = json.loads(args.event.read_text(encoding='utf-8')).get('pull_request')
        if pull_request:
            text = (pull_request.get('title') or '') + '\n' + (pull_request.get('body') or '')
            if violations(text, message=True):
                errors.append('Pull request text contains a prohibited contributor credit')
    if args.identities:
        for variable in ('GIT_AUTHOR_IDENT', 'GIT_COMMITTER_IDENT'):
            if AI_IDENTITY.search(git('var', variable).decode()):
                errors.append(f'{variable}: use the configured human identity')
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        print('Follow AGENTS.md: omit AI/tool contributor credits and coauthor trailers.', file=sys.stderr)
    return bool(errors)


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Run prepared synthetic P4 conditions in fresh local Codex sessions.

This runner captures evidence, not semantic grades. It never installs a runtime,
changes saved configuration, reads credentials itself, or replaces an earlier run.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_inventory(folder):
    return {
        str(p.relative_to(folder)): digest(p)
        for p in sorted(folder.rglob('*'))
        if not p.is_symlink() and p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'
    }


def read_events(path):
    events, errors = [], []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError('event is not an object')
            events.append(event)
        except ValueError as exc:
            errors.append(f'event line {number}: {exc}')
    return events, errors


def command_for(binary, workspace, state, output, model, reasoning):
    command = [
        binary, 'exec', '--ignore-user-config', '--ephemeral',
        '--skip-git-repo-check', '--sandbox', 'workspace-write', '--json',
        '-m', model, '-C', str(workspace), '-o', str(output),
    ]
    settings = {
        'model_reasoning_effort': reasoning,
        'sqlite_home': str(state),
        'project_doc_max_bytes': 0,
        'web_search': 'disabled',
        'approval_policy': 'never',
        'sandbox_workspace_write.network_access': False,
        'sandbox_workspace_write.exclude_slash_tmp': True,
        'sandbox_workspace_write.exclude_tmpdir_env_var': True,
        'shell_environment_policy.inherit': 'core',
    }
    for feature in ('memories', 'chronicle', 'plugins', 'apps', 'hooks', 'multi_agent'):
        settings[f'features.{feature}'] = False
    settings['features.skip_host_skill_discovery'] = True
    for key, value in settings.items():
        command.extend(['-c', f'{key}={json.dumps(value)}'])
    return command + ['-']


def execute(condition, output_root, binary, model, reasoning, timeout, runtime_version):
    condition = condition.resolve()
    target = output_root.resolve() / condition.name
    # An exclusive mkdir preserves failed and successful earlier attempts alike.
    target.mkdir(parents=True, exist_ok=False)
    before = file_inventory(condition)
    started = utc_now()
    record = {
        'schema_version': 'wealth-p4-runtime-v1',
        'run_id': condition.name,
        'started_at': started,
        'model_requested': model,
        'model_identity_basis': 'CLI request; exact server model snapshot not exposed',
        'reasoning_effort': reasoning,
        'runtime_version': runtime_version,
        'condition_files_sha256': before,
        'status': 'failed',
        'fresh_session': True,
        'initial_response_only': True,
        'timeout_seconds': timeout,
        'isolation': 'fresh cwd and disabled host context; not a hermetic read filesystem',
        'external_actions_authorized': False,
    }
    start_clock = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='wealth-p4-model-') as temporary:
        base = Path(temporary)
        workspace = base / 'work'
        shutil.copytree(condition, workspace)
        response = target / 'response.md'
        command = command_for(binary, workspace, base / 'state', response, model, reasoning)
        record['command'] = command
        env = dict(os.environ, RUST_LOG='error', PYTHONDONTWRITEBYTECODE='1')
        # No resume/fork parameter and no parent task identity is supplied.
        env.pop('CODEX_THREAD_ID', None)
        try:
            with (target / 'events.jsonl').open('w') as stdout, (target / 'stderr.txt').open('w') as stderr:
                process = subprocess.Popen(
                    command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                    text=True, cwd=workspace, env=env, start_new_session=True,
                )
                try:
                    process.communicate((workspace / 'prompt.txt').read_text(), timeout=timeout)
                except subprocess.TimeoutExpired:
                    record['timed_out'] = True
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                record['exit_code'] = process.returncode
            events, errors = read_events(target / 'events.jsonl')
            record['event_parse_errors'] = errors
            record['session_ids'] = [e['thread_id'] for e in events if e.get('type') == 'thread.started']
            record['turn_completed'] = any(e.get('type') == 'turn.completed' for e in events)
            record['turn_failed'] = any(e.get('type') == 'turn.failed' for e in events)
            record['usage'] = [e.get('usage', {}) for e in events if e.get('type') == 'turn.completed']
            record['tool_event_count'] = sum(
                e.get('type') == 'item.completed'
                and e.get('item', {}).get('type') not in ('agent_message', 'reasoning', 'error')
                for e in events
            )
            record['runtime_notices'] = [
                e.get('message') or e.get('item', {}).get('message')
                for e in events
                if e.get('type') == 'error' or e.get('item', {}).get('type') == 'error'
            ]
            if response.exists():
                record['response_sha256'] = digest(response)
                record['response_bytes'] = response.stat().st_size
            if (
                process.returncode == 0 and record['turn_completed']
                and not record['turn_failed'] and not errors
                and response.exists() and response.read_text().strip()
                and not record.get('timed_out')
            ):
                record['status'] = 'completed-ungraded'
            after = file_inventory(workspace)
            record['unretained_symlinks'] = [str(p.relative_to(workspace)) for p in workspace.rglob('*') if p.is_symlink()]
            changed = {name: sha for name, sha in after.items() if before.get(name) != sha}
            record['generated_or_modified_files_sha256'] = changed
            record['deleted_condition_files'] = sorted(set(before) - set(after))
            for name in changed:
                source = workspace / name
                if source.is_symlink():
                    record.setdefault('artifact_errors', []).append(f'symlink not retained: {name}')
                    continue
                destination = target / 'generated' / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
        except (OSError, ValueError) as exc:
            record['runner_error'] = str(exc)
    record['finished_at'] = utc_now()
    record['elapsed_seconds'] = round(time.monotonic() - start_clock, 3)
    record['retained_files_sha256'] = file_inventory(target)
    (target / 'runtime.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def import_record(experiment, runtime):
    """Bind a captured runtime to its predeclared evaluation record, without grading."""
    from wealth_p4_eval import load, ref, save, validate_prepared
    experiment = experiment.resolve()
    manifest, _ = validate_prepared(experiment)
    metadata = load(runtime)
    retained = file_inventory(runtime.parent)
    retained.pop('runtime.json', None)
    if retained != metadata['retained_files_sha256']:
        raise ValueError('Retained runtime evidence changed after capture')
    if 'response_sha256' in metadata and retained.get('response.md') != metadata['response_sha256']:
        raise ValueError('Initial response differs from runtime capture')
    expected = next(r for r in manifest['expected_runs'] if r['run_id'] == metadata['run_id'])
    prefix = expected['packet_dir'] + '/'
    bound_inventory = {item['path'][len(prefix):]: item['sha256'] for item in expected['exposed_files']}
    if metadata['condition_files_sha256'] != bound_inventory:
        raise ValueError('Runtime input inventory differs from frozen condition')
    destination = experiment / expected['record_path']
    record = load(destination)
    if record['attempts'] or record['execution']['status'] != 'missing':
        raise ValueError('Cannot replace an already imported first-pass record')
    folder = runtime.parent
    relative = lambda path: path.resolve().relative_to(experiment).as_posix()
    evidence = [ref(experiment, relative(folder / name)) for name in ('runtime.json', 'events.jsonl', 'stderr.txt') if (folder / name).exists()]
    start = metadata['started_at'].replace('+00:00', 'Z')
    end = metadata['finished_at'].replace('+00:00', 'Z')
    events, _ = read_events(folder / 'events.jsonl')
    tool_events = []
    for event in events:
        item = event.get('item', {})
        kind = item.get('type')
        if event.get('type') != 'item.completed' or kind in ('agent_message', 'reasoning', 'error'):
            continue
        tool_events.append({
            'tool': kind or 'unknown',
            'description': item.get('command') or json.dumps(item, ensure_ascii=False),
            'status': 'failed' if item.get('exit_code', 0) not in (0, None) or item.get('status') == 'failed' else 'succeeded',
            'started_at': start, 'ended_at': end,
            'timestamp_precision': 'bounded by whole run; event stream has no wall-clock timestamps',
            'evidence_refs': [ref(experiment, relative(folder / 'events.jsonl'))],
        })
    completed = metadata['status'] == 'completed-ungraded'
    record['generator']['identity'] = 'codex-cli:' + (metadata.get('session_ids') or [metadata['run_id']])[0]
    record['generator']['requested_model'] = {'provider': 'OpenAI', 'model_id': metadata['model_requested'], 'reasoning_effort': metadata['reasoning_effort']}
    record['generator']['runtime_version'] = metadata['runtime_version']
    record['generator']['model_identity_note'] = 'Requested model accepted by CLI service; event stream does not report resolved backend model/snapshot. Retain model.availability=unknown.'
    record['execution'] = {
        'status': 'completed' if completed else 'failed', 'started_at': start, 'ended_at': end,
        'isolation': {'fresh_context': True, 'isolated_workdir': True, 'hidden_rubric_unavailable': True, 'tool_policy_matched': False},
        'isolation_note': 'Only condition files copied; fresh non-resumed CLI session; rubric/repo paths absent. Not an OS-enforced private read filesystem. Inspect tool events for violations.',
        'tool_policy_audit_status': 'pending separate review of retained tool events',
        'evidence_refs': evidence,
    }
    response = folder / 'response.md'
    record['attempts'] = [{
        'attempt_id': 'first-pass', 'stage': 'first-pass', 'parent_attempt_id': None,
        'status': 'completed' if completed else 'failed', 'started_at': start, 'ended_at': end,
        'response': ref(experiment, relative(response)) if response.exists() and response.read_text().strip() else None,
        'generated_artifacts': [ref(experiment, relative(folder / 'generated' / name)) for name in sorted(metadata.get('generated_or_modified_files_sha256', {})) if (folder / 'generated' / name).is_file()],
        'evidence_refs': evidence,
        'tool_usage': {'status': 'used' if tool_events else 'none', 'events': tool_events},
        'repair': None,
    }]
    save(destination, record)


def attach_generated(experiment):
    """Attach unchanged captured deliverables to runs imported by older runners."""
    from wealth_p4_eval import load, ref, save, validate_prepared
    experiment = experiment.resolve()
    manifest, _ = validate_prepared(experiment)
    for expected in manifest['expected_runs']:
        path = experiment / expected['record_path']
        record = load(path)
        if not record['attempts']:
            continue
        folder = experiment / 'artifacts' / expected['run_id']
        runtime = load(folder / 'runtime.json')
        current = file_inventory(folder)
        current.pop('runtime.json', None)
        if current != runtime['retained_files_sha256']:
            raise ValueError('Captured files changed: ' + expected['run_id'])
        artifacts = [ref(experiment, (folder / 'generated' / name).relative_to(experiment).as_posix()) for name in sorted(runtime.get('generated_or_modified_files_sha256', {})) if (folder / 'generated' / name).is_file()]
        attempt = record['attempts'][0]
        if 'generated_artifacts' in attempt:
            if attempt['generated_artifacts'] != artifacts:
                raise ValueError('Cannot replace the retained deliverable inventory')
            continue
        review = experiment / 'reviews' / (expected['run_id'] + '--first-pass.json')
        if review.exists():
            raise ValueError('Cannot change output bindings after scoring')
        attempt['generated_artifacts'] = artifacts
        save(path, record)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--conditions', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--codex', default='codex')
    parser.add_argument('--model', required=True)
    parser.add_argument('--reasoning', default='high', choices=['low', 'medium', 'high', 'xhigh', 'ultra'])
    parser.add_argument('--jobs', type=int, default=2, choices=range(1, 4))
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--run-id', action='append', help='Optional explicit condition directory names')
    parser.add_argument('--import-experiment', type=Path, help='Bind captured records to this prepared experiment; output must be inside it')
    parser.add_argument('--attach-generated-only', action='store_true', help='Bind already captured deliverables without calling a model')
    args = parser.parse_args()
    if args.attach_generated_only:
        if not args.import_experiment:
            parser.error('--attach-generated-only requires --import-experiment')
        attach_generated(args.import_experiment)
        return 0
    if args.timeout < 1:
        parser.error('timeout must be positive')
    conditions = sorted(p.parent for p in args.conditions.glob('*/prompt.txt'))
    if args.run_id:
        conditions = [p for p in conditions if p.name in args.run_id]
        if set(args.run_id) != {p.name for p in conditions}:
            parser.error('one or more requested condition directories do not exist')
    if not conditions:
        parser.error('no prepared conditions found')
    if any((args.output / p.name).exists() for p in conditions):
        parser.error('output already contains a selected run; use a new output directory')
    version = subprocess.run([args.codex, '--version'], capture_output=True, text=True, check=True).stdout.strip()
    records = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        jobs = {pool.submit(execute, p, args.output, args.codex, args.model, args.reasoning, args.timeout, version): p for p in conditions}
        for future in as_completed(jobs):
            result = future.result()
            records.append(result)
            if args.import_experiment:
                import_record(args.import_experiment, args.output / result['run_id'] / 'runtime.json')
            print(json.dumps({k: result.get(k) for k in ['run_id', 'status', 'elapsed_seconds', 'response_bytes']}), flush=True)
    return int(any(r['status'] != 'completed-ungraded' for r in records))


if __name__ == '__main__':
    raise SystemExit(main())

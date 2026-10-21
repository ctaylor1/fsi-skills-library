"""Read-only comparison with the dirty-checkout baseline captured before Phase2."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASELINE = HERE / 'checkout-baseline.json'
ALLOWED_PREFIXES = ('skills/compliance-financial-crime/',
                    'shared/compliance-financial-crime/',
                    'docs/compliance-financial-crime/')
ALLOWED_FILES = {
    'STATUS.md', 'README.md', 'docs/SOURCES.md',
    'tools/run_compliance_portable.py', 'tools/sync_cfc_resources.py',
    'tools/check_compliance_financial_crime.py',
    'tools/test_compliance_foundation_phase2.py', 'tools/test_compliance_phase2.py',
    'catalog/skills-catalog.json', 'catalog/skills-catalog.csv',
    'catalog/provisional-additions.json', 'catalog/approved-overrides.json',
    'catalog/compliance-financial-crime-capabilities.json',
    'catalog/compliance-financial-crime-migrations.json',
    'catalog/compliance-resource-lock.json',
    'catalog/compliance-financial-crime-phase2-capabilities.json',
    'skills/capital-markets/communications-compliance-reviewer/SKILL.md',
    'skills/capital-markets/communications-compliance-reviewer/CHANGELOG.md',
    'skills/capital-markets/communications-compliance-reviewer/references/handoffs.md',
    'skills/data-ai-model-governance/privacy-impact-assessment-assistant/references/evidence-contract.md',
    'skills/data-ai-model-governance/privacy-impact-assessment-assistant/references/package-manifest.json',
}

def allowed(rel):
    return ((rel in ALLOWED_FILES or rel.startswith(ALLOWED_PREFIXES))
            and not rel.startswith('docs/compliance-financial-crime/phase1-validation/'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify():
    baseline = json.loads(BASELINE.read_text())
    before = baseline['files']
    protected = {rel: value for rel, value in before.items() if not allowed(rel)}
    changed = [rel for rel, value in protected.items()
               if not (ROOT / rel).is_file() or digest(ROOT / rel) != value]
    changed_allowed = [rel for rel, value in before.items() if allowed(rel)
                       and (not (ROOT / rel).is_file() or digest(ROOT / rel) != value)]
    unexpected_new = []
    new_allowed = []
    for path in ROOT.rglob('*'):
        if not path.is_file() or any(p in path.parts for p in ('.git', '__pycache__')) or path.name == '.DS_Store' or path.suffix == '.pyc':
            continue
        rel = str(path.relative_to(ROOT))
        if rel not in before:
            (new_allowed if allowed(rel) else unexpected_new).append(rel)
    return {
        'scope': 'Existing unrelated work and Phase1 validation archives; explicitly authorized Phase2 edit paths excluded',
        'baseline_files': len(before),
        'baseline_date': baseline['date'],
        'protected_files': len(protected),
        'phase1_validation_files': sum(rel.startswith('docs/compliance-financial-crime/phase1-validation/') for rel in protected),
        'protected_changed_files': sorted(changed),
        'authorized_existing_changes': sorted(changed_allowed),
        'authorized_new_files_count': len(new_allowed),
        'unexpected_new_files': sorted(unexpected_new),
        'passed': not changed and not unexpected_new,
    }

if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))

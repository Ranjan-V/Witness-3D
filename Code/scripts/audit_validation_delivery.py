"""Check delivered reports, evidence counts and unchanged experiment source."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from witness3d.io import atomic_json
from witness3d.pipeline import source_fingerprint

root = Path(__file__).resolve().parents[1]
out = root/'docs/validation'
required = ['README.md', 'mathematical_audit.md', 'proof_status_ledger.md', 'test_report.md',
            'synthetic_config.yaml', 'synthetic_results.csv', 'baseline_comparisons.md',
            'bounded_baseline_comparisons.md', 'failure_case_analysis.md', 'numerical_verification.md',
            'runtime_memory.md', 'novelty_risk.md', 'recommended_improvements.md',
            'kaggle_readiness.md', 'commands.ps1', 'environment.json', 'validation_overview.png']
assert all((out/name).is_file() for name in required)
test = ET.parse(out/'tests_after_fixes.xml').getroot()[0].attrib
assert (test['tests'], test['failures'], test['errors'], test['skipped']) == ('109', '0', '0', '0')
identity = json.loads((out/'results/sweep/identity.json').read_text())
assert source_fingerprint(root/'src/witness3d') == identity['source_hash']
checker = json.loads((out/'standalone_checker_results.json').read_text())
assert checker['record_files'] == 10080 and checker['arithmetic_artifacts'] == 11965
assert checker['invalid_arithmetic_artifacts'] == checker['invalid_envelope_traces'] == 0
assert checker['forbidden_imports_loaded'] == []
oracle = json.loads((out/'numerical_oracle_results.json').read_text())
assert len(oracle['cases']) == 48 and oracle['mismatches'] == 0 and oracle['support_queries'] == 240
bounded = json.loads((out/'bounded_control_checks.json').read_text())
assert bounded['counts']['records'] == 2240
assert bounded['counts']['points_outside_box_or_nonfinite'] == 0
assert bounded['counts']['invalid_reported_depths'] == 0
paper = root.parent/'Paper'
assert not list(paper.iterdir())
broken = []
for path in out.glob('*.md'):
    for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
        if target.startswith(('https:', 'http:', '#')):
            continue
        if not (path.parent/target).exists():
            broken.append({'file': path.name, 'target': target})
assert not broken, broken
authored = list((root/'src').rglob('*.py'))+list((root/'scripts').glob('*'))+list((root/'tests').glob('*.py'))
authored += list((root.parent/'Math').glob('*'))+list((root.parent/'Theory').glob('*'))
authored += [p for p in out.iterdir() if p.is_file() and p.name != 'delivery_integrity.json']
hashes = {str(p.relative_to(root.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(authored) if p.is_file()}
result = {'required_deliverables_present': required, 'test_counts': test,
          'source_matches_executed_sweep': True, 'primary_record_files': 10080,
          'supplemental_record_count': 2240, 'paper_empty_read_only_check': True,
          'broken_local_report_links': broken, 'sha256': hashes}
atomic_json(out/'delivery_integrity.json', result)
print(json.dumps({k: v for k, v in result.items() if k != 'sha256'}, indent=2))

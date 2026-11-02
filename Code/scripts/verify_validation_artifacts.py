"""Audit saved sweep artifacts in a process that forbids numerical imports."""
import importlib.abc
import json
from pathlib import Path
import sys


class RejectNumericalImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'numpy', 'scipy', 'torch', 'cv2'}:
            raise AssertionError('Independent checker imported '+fullname)
        return None


sys.meta_path.insert(0, RejectNumericalImports())
from witness3d.verify import check_artifact, check_envelope

root = Path(sys.argv[1])
counts = {'record_files': 0, 'arithmetic_artifacts': 0, 'invalid_arithmetic_artifacts': 0,
          'complete_envelope_traces': 0, 'invalid_envelope_traces': 0}
failures = []
for path in sorted(root.glob('*/seed_*/run/records/*.json')):
    counts['record_files'] += 1
    record = json.loads(path.read_text())
    artifacts = list(record['artifacts'])
    for envelope in record.get('envelopes', {}).values():
        if envelope['state'] in {'BOUNDED', 'MEASUREMENT_CONFLICT'}:
            counts['complete_envelope_traces'] += 1
            if not check_envelope(envelope).accepted:
                counts['invalid_envelope_traces'] += 1
                failures.append(str(path))
        for branch in envelope['evidence']:
            artifacts.extend(branch[key] for key in ['upper', 'negative_lower', 'exclusion'] if key in branch)
    for artifact in artifacts:
        counts['arithmetic_artifacts'] += 1
        if not check_artifact(artifact).accepted:
            counts['invalid_arithmetic_artifacts'] += 1
            failures.append(str(path))
counts['forbidden_imports_loaded'] = sorted({'numpy', 'scipy', 'torch', 'cv2'} & set(sys.modules))
result = {**counts, 'failures': failures}
Path(sys.argv[2]).write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result), flush=True)
if failures or counts['forbidden_imports_loaded'] or not counts['record_files']:
    raise SystemExit(1)

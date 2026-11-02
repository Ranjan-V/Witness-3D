"""Archival file copy/hash/security inspection only; no research execution."""
import hashlib
import json
from pathlib import Path
import re
import shutil

source = Path('D:/CVPR')
stage = Path(__file__).resolve().parents[1]
excluded_dirs = {'.git', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache',
                 '.venv', '.venv-validation', 'venv', 'env', 'build', 'dist', '.idea', '.vscode'}
excluded_ext = {'.pyc', '.pyo', '.pth', '.pt', '.ckpt', '.safetensors', '.onnx', '.pem', '.key'}
files = []
excluded = []
def visit(directory):
    for path in sorted(directory.iterdir()):
        rel = path.relative_to(source).as_posix()
        if path.is_dir():
            if path.name in excluded_dirs or path.name.endswith('.egg-info') or rel in {'Code/data','Code/checkpoints','Code/outputs','data','datasets','checkpoints'}:
                excluded.append({'path': rel+'/', 'reason': 'local runtime/cache/build/external assets'})
            else:
                visit(path)
        elif path.suffix.lower() in excluded_ext or path.name == '.env' or path.name.startswith('.env.') or path.name == 'kaggle.json':
            excluded.append({'path': rel,'reason':'cache, model asset or credential-sensitive filename'})
        else:
            files.append(path)
visit(source)
patterns = {
    'private_key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'github_token': re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b'),
    'openai_key': re.compile(rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b'),
    'aws_access_key': re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'assigned_secret': re.compile(rb'''(?i)(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*["'][A-Za-z0-9_+/=-]{24,}["']'''),
}
findings=[]; entries=[]
for path in files:
    data=path.read_bytes();rel=path.relative_to(source).as_posix()
    if len(data)>=100*1024*1024: raise RuntimeError('File exceeds archival size cap: '+rel)
    for name,pattern in patterns.items():
        if pattern.search(data):findings.append({'path':rel,'pattern':name})
    entries.append({'path':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
if findings:
    print(json.dumps({'sensitive_findings':findings}));raise SystemExit(1)
for path,entry in zip(files,entries):
    destination=stage/entry['path'];destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists() and destination.read_bytes()!=path.read_bytes():
        raise RuntimeError('Refusing overwrite: '+entry['path'])
    shutil.copy2(path,destination)
    assert hashlib.sha256(destination.read_bytes()).hexdigest()==entry['sha256']
manifest={'source':'D:/CVPR','purpose':'Faithful archival; no experiments/tests executed during archival',
          'source_files':entries,'excluded':excluded,'source_file_count':len(entries),
          'total_source_bytes':sum(e['bytes'] for e in entries),
          'maximum_source_file_bytes':max(e['bytes'] for e in entries),
          'secret_scan':{'patterns':list(patterns),'findings':findings,
                         'limitation':'Targeted pattern scan, not a proof that every possible secret format is absent'},
          'extra_archive_files':['README.md','.gitignore','.gitattributes','ARCHIVAL.md','ARCHIVE_MANIFEST.json',
                                 'Paper/.gitkeep','archive_tools/prepare_archive.py']}
(stage/'ARCHIVE_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in manifest.items() if k!='source_files'},indent=2))

"""Record the CPU validation environment without importing any model framework."""
import hashlib
import importlib.metadata as metadata
import json
import os
import platform
from pathlib import Path
import sys

import numpy as np
import psutil
import scipy
from threadpoolctl import threadpool_info

root = Path(__file__).resolve().parents[1]
out = root / 'docs' / 'validation'
out.mkdir(parents=True, exist_ok=True)
names = ['numpy', 'scipy', 'Pillow', 'PyYAML', 'pytest', 'matplotlib', 'psutil',
         'opencv-python', 'setuptools', 'pip', 'threadpoolctl']
versions = {name: metadata.version(name) for name in names}
record = {'python': sys.version, 'executable': sys.executable,
          'platform': platform.platform(), 'processor': platform.processor(),
          'logical_cpus': os.cpu_count(), 'physical_cpus': psutil.cpu_count(logical=False),
          'ram_bytes': psutil.virtual_memory().total, 'dependencies': versions,
          'threadpools': threadpool_info(),
          'environment': {key: os.environ.get(key) for key in
                          ['CUDA_VISIBLE_DEVICES', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                           'MKL_NUM_THREADS', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD']},
          'environment_type': 'local venv, system-site-packages; source imported with explicit PYTHONPATH; offline editable build blocked by missing wheel',
          'network_installations': False,
          'source_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in sorted((root / 'src').rglob('*.py'))}}
(out / 'environment.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
(out / 'requirements-validation.txt').write_text(
    '# Observed versions; no network install was performed. Python 3.11.9.\n' +
    '\n'.join(f'{name}=={version}' for name, version in versions.items()) + '\n', encoding='utf-8')
print(json.dumps({key: record[key] for key in ['python', 'platform', 'physical_cpus', 'ram_bytes', 'dependencies']}, indent=2))

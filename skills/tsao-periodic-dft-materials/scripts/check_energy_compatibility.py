#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import yaml
ap=argparse.ArgumentParser();ap.add_argument('expression',type=Path);a=ap.parse_args();d=yaml.safe_load(a.expression.read_text())
terms=d.get('terms') or [];fps={t.get('method_fingerprint') for t in terms};errors=[]
if len(terms)<2:errors.append('energy expression needs at least two terms')
if None in fps or len(fps)!=1:errors.append(f'incompatible method fingerprints: {sorted(str(x) for x in fps)}')
if abs(sum(float(t.get('coefficient',0)) for t in terms))<1e-12 and d.get('quantity')=='total_energy':errors.append('derived expression mislabeled total_energy')
print(json.dumps({'ok':not errors,'errors':errors,'fingerprints':sorted(str(x) for x in fps)},indent=2));raise SystemExit(0 if not errors else 1)

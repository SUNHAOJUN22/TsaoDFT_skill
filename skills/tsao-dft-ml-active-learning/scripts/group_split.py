#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('dataset',type=Path);ap.add_argument('--group',required=True);ap.add_argument('--out-dir',type=Path,required=True);ap.add_argument('--train',type=float,default=.7);ap.add_argument('--valid',type=float,default=.15);a=ap.parse_args()
rows=list(csv.DictReader(a.dataset.open(encoding='utf-8'))); groups=sorted({r[a.group] for r in rows})
def bucket(g): return int(hashlib.sha256(g.encode()).hexdigest()[:12],16)/float(16**12)
assign={g:('train' if bucket(g)<a.train else 'valid' if bucket(g)<a.train+a.valid else 'test') for g in groups}
a.out_dir.mkdir(parents=True,exist_ok=True)
for split in ['train','valid','test']:
 out=a.out_dir/f'{split}.csv'; subset=[r for r in rows if assign[r[a.group]]==split]
 with out.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(subset)
print({s:sum(assign[g]==s for g in groups) for s in ['train','valid','test']})

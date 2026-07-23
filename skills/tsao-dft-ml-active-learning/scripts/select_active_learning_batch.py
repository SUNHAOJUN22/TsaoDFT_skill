#!/usr/bin/env python3
import argparse,csv
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('pool',type=Path);ap.add_argument('--batch-size',type=int,required=True);ap.add_argument('--uncertainty',default='uncertainty');ap.add_argument('--group',default='parent_id');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
rows=list(csv.DictReader(a.pool.open(encoding='utf-8')));rows.sort(key=lambda r:(-float(r[a.uncertainty]),r.get(a.group,''),r.get('sample_id','')))
sel=[];seen=set()
for r in rows:
 g=r.get(a.group,r.get('sample_id'))
 if g in seen:continue
 sel.append(r);seen.add(g)
 if len(sel)>=a.batch_size:break
with a.out.open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(sel)
print(f'selected {len(sel)} candidates from distinct groups')

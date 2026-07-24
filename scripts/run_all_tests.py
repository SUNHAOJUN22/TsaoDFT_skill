#!/usr/bin/env python3
"""Run root and per-Skill unittest suites concurrently and report a stable summary."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def run_suite(path:Path)->dict:
    command=[sys.executable,'-m','unittest','discover','-s',str(path),'-p','test_*.py','-v']
    p=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    text=(p.stdout or '')+(p.stderr or '')
    m=re.search(r'Ran\s+(\d+)\s+tests?',text)
    return {'path':path,'returncode':p.returncode,'count':int(m.group(1)) if m else 0,'output':text}

def main()->int:
    suites=[ROOT/'tests']+sorted((ROOT/'skills').glob('*/tests'))
    results=[]
    with ThreadPoolExecutor(max_workers=min(6,len(suites))) as pool:
        futures={pool.submit(run_suite,path):path for path in suites if path.exists()}
        for future in as_completed(futures):results.append(future.result())
    results.sort(key=lambda r:str(r['path']))
    for r in results:
        print(f"\n=== unittest: {r['path'].relative_to(ROOT)} ===")
        print(r['output'].rstrip())
    failed=[r for r in results if r['returncode']]
    total=sum(r['count'] for r in results)
    print(f"\nSuites: {len(results)}  Tests: {total}  Failed suites: {len(failed)}")
    return 1 if failed else 0
if __name__=='__main__':raise SystemExit(main())

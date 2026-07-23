#!/usr/bin/env python3
import argparse,hashlib,json,os,platform,sys
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('files',nargs='+',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();records=[]
for p in a.files:records.append({'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
out={'python':sys.version,'platform':platform.platform(),'cwd':os.getcwd(),'files':records};a.out.write_text(json.dumps(out,indent=2)+'\n');print(a.out)

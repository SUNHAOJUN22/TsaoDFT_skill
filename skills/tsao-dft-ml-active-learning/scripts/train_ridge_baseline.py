#!/usr/bin/env python3
"""Train a deterministic train-only standardized ridge baseline on grouped DFT data."""
from __future__ import annotations
import argparse,csv,json,math,random
from pathlib import Path
import numpy as np

def read(path):
    with Path(path).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def metrics(y,p):
    y=np.asarray(y,float);p=np.asarray(p,float);err=p-y
    mae=float(np.mean(np.abs(err)));rmse=float(np.sqrt(np.mean(err**2)));den=float(np.sum((y-y.mean())**2));r2=float(1-np.sum(err**2)/den) if den>0 else None
    return {'mae':mae,'rmse':rmse,'r2':r2}
def split_groups(rows,group,seed,frac_train=.7,frac_valid=.15):
    groups=sorted({r[group] for r in rows});rng=random.Random(seed);rng.shuffle(groups);n=len(groups);nt=max(1,int(round(n*frac_train)));nv=max(1,int(round(n*frac_valid))) if n>=3 else 0
    if nt+nv>=n:nv=max(0,n-nt-1)
    assign={g:'train' if i<nt else 'valid' if i<nt+nv else 'test' for i,g in enumerate(groups)}
    return assign
def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('dataset',type=Path);ap.add_argument('--features',required=True);ap.add_argument('--target',required=True);ap.add_argument('--group',required=True);ap.add_argument('--seed',type=int,default=17);ap.add_argument('--alpha',type=float,default=1.0);ap.add_argument('--out-dir',type=Path,required=True);a=ap.parse_args()
    rows=read(a.dataset);features=[x.strip() for x in a.features.split(',') if x.strip()];errors=[]
    try:X=np.array([[float(r[f]) for f in features] for r in rows],float);y=np.array([float(r[a.target]) for r in rows],float)
    except Exception as exc:print(json.dumps({'ok':False,'errors':[str(exc)]},indent=2));return 1
    assign=split_groups(rows,a.group,a.seed);idx={s:np.array([i for i,r in enumerate(rows) if assign[r[a.group]]==s],int) for s in ['train','valid','test']}
    if len(idx['train'])<2 or len(idx['test'])<1:errors.append('insufficient grouped train/test samples')
    if errors:print(json.dumps({'ok':False,'errors':errors},indent=2));return 1
    mean=X[idx['train']].mean(axis=0);std=X[idx['train']].std(axis=0);std[std==0]=1.0;Xs=(X-mean)/std
    Xa=np.column_stack([np.ones(len(Xs)),Xs]);pen=np.eye(Xa.shape[1]);pen[0,0]=0
    beta=np.linalg.solve(Xa[idx['train']].T@Xa[idx['train']]+a.alpha*pen,Xa[idx['train']].T@y[idx['train']]);pred=Xa@beta
    a.out_dir.mkdir(parents=True,exist_ok=True)
    with (a.out_dir/'predictions.csv').open('w',newline='',encoding='utf-8') as f:
        fields=list(rows[0])+['split','prediction','residual'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();
        for i,r in enumerate(rows):w.writerow({**r,'split':assign[r[a.group]],'prediction':pred[i],'residual':pred[i]-y[i]})
    card={'schema_version':'1.0','model_id':'ridge-baseline','model_family':'ridge','features':features,'target':a.target,'group_column':a.group,'split_policy':'group','seed':a.seed,'alpha':a.alpha,'preprocessing_fit_scope':'train_only','standardization':{'mean':mean.tolist(),'std':std.tolist()},'coefficients':beta.tolist(),'metrics':{s:metrics(y[ii],pred[ii]) for s,ii in idx.items() if len(ii)},'counts':{s:int(len(ii)) for s,ii in idx.items()},'scientific_interpretation':'baseline_only','status':'validated'}
    (a.out_dir/'model-card.json').write_text(json.dumps(card,indent=2),encoding='utf-8');print(json.dumps({'ok':True,'outputs':[str(a.out_dir/'predictions.csv'),str(a.out_dir/'model-card.json')],'metrics':card['metrics']},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())

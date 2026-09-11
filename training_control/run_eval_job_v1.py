#!/usr/bin/env python3
"""Run one TruthGuard evaluation transaction in an isolated output directory.

External LLM calls are deliberately classified as non-training transactions. A
failed/incomplete transaction is restarted from a clean directory rather than
claiming optimizer-style exact resume across an external provider's hidden state.
Completed transactions are receipt-bound and idempotently skipped.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"artifacts"/"training_control"/"evaluations"
SCRIPTS={"edgecore":"experiments/run_edgecore_eval.py","pipeline":"experiments/run_pipeline_eval.py","memory":"experiments/run_memory_eval.py"}

def _safe(value:str)->str: return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)
def _fingerprint(payload:dict)->str: return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def parser():
    p=argparse.ArgumentParser(); p.add_argument("--kind",choices=sorted(SCRIPTS),required=True); p.add_argument("--provider",choices=["ollama","gemini"],required=True); p.add_argument("--model",required=True); p.add_argument("--session-length",type=int,default=50); p.add_argument("--num-samples",type=int,default=0); p.add_argument("--num-ctx",type=int,default=2048); p.add_argument("--max-context",type=int,default=8192); return p

def main()->int:
    a=parser().parse_args()
    if a.session_length<1 or a.num_samples<0 or a.num_ctx<1 or a.max_context<1: raise ValueError("invalid evaluation dimensions")
    name=f"{a.kind}__{a.provider}__{_safe(a.model)}"+(f"__{a.session_length}turns" if a.kind=="memory" else "")
    out=BASE/name; receipt=out/"COMPLETE.json"
    cfg={"schema_version":1,"kind":a.kind,"provider":a.provider,"model_name":a.model,"session_length":a.session_length if a.kind=="memory" else None,"num_samples":a.num_samples,"num_ctx":a.num_ctx,"max_context":a.max_context,"script":SCRIPTS[a.kind],"external_service_transaction":True,"optimizer_training":False}
    fp=_fingerprint(cfg)
    if receipt.is_file():
        prior=json.loads(receipt.read_text(encoding="utf-8"))
        if prior.get("fingerprint")==fp and prior.get("status")=="complete": print(json.dumps(prior,sort_keys=True)); return 0
        raise RuntimeError(f"completed output exists with different fingerprint: {out}")
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True,exist_ok=True)
    (out/"config.json").write_text(json.dumps(cfg,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    cmd=[sys.executable,SCRIPTS[a.kind],"--provider",a.provider,"--model_name",a.model,"--num_samples",str(a.num_samples),"--output_dir",str(out),"--num_ctx",str(a.num_ctx),"--max_context",str(a.max_context)]
    if a.kind=="memory": cmd.extend(["--session_length",str(a.session_length)])
    completed=subprocess.run(cmd,cwd=ROOT,check=False)
    if completed.returncode!=0: return int(completed.returncode)
    expected={"edgecore":"edgecore_ablation.csv","pipeline":"pipeline_eval.csv","memory":"memory_persistence.csv"}[a.kind]
    if not (out/expected).is_file(): raise RuntimeError(f"evaluation completed without expected artifact: {out/expected}")
    payload={"schema_version":1,"status":"complete","fingerprint":fp,"config":cfg,"artifact":expected,"external_provider_nondeterminism":True,"restart_semantics":"clean_transaction_restart","training_executed":False}
    tmp=receipt.with_suffix(".tmp"); tmp.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8"); os.replace(tmp,receipt); print(json.dumps(payload,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())

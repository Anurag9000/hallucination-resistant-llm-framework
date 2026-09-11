#!/usr/bin/env python3
"""Complete OPF-visible TruthGuard scientific evaluation authority."""
from __future__ import annotations
import os,sys
from pathlib import Path
from typing import Any,Iterator
ROOT=Path(__file__).resolve().parents[1]
EVAL_ROOT=ROOT/"artifacts"/"training_control"/"evaluations"
DEFAULT_MODELS=(("ollama","qwen2.5:1.5b"),("ollama","llama3.2"),("gemini","gemini-2.5-flash"))
DEFAULT_MEMORY_LENGTHS=(10,30,50)

def _models():
    raw=(os.environ.get("TRUTHGUARD_MODELS") or "").strip()
    if not raw:return DEFAULT_MODELS
    out=[]
    for item in raw.split(","):
        if "=" not in item: raise ValueError("TRUTHGUARD_MODELS entries must be provider=model")
        p,m=item.split("=",1);p=p.strip();m=m.strip()
        if p not in {"ollama","gemini"} or not m: raise ValueError(f"invalid model binding: {item}")
        out.append((p,m))
    if len(out)!=len(set(out)): raise ValueError("TRUTHGUARD_MODELS contains duplicates")
    return tuple(out)

def _lengths():
    raw=(os.environ.get("TRUTHGUARD_MEMORY_LENGTHS") or "").strip()
    if not raw:return DEFAULT_MEMORY_LENGTHS
    values=tuple(int(x.strip()) for x in raw.split(","))
    if any(v<1 for v in values) or len(values)!=len(set(values)): raise ValueError("invalid TRUTHGUARD_MEMORY_LENGTHS")
    return values

def _restart(job_id,command,phase,family,depends,artifacts):
    return {"id":job_id,"command":command,"phase":phase,"family":family,"device_capable":False,"depends_on":list(depends),"is_training_job":False,"resume_strategy":"restart_exact","deterministic":True,"idempotent":True,"atomic_outputs":True,"checkpoint_contract":{"exact_resume":True,"deterministic":True,"idempotent":True,"atomic_outputs":True},"early_stopping_applicable":False,"early_stopping_exception_reason":"non-optimizer repository lifecycle node","completion_artifacts":[str(x) for x in artifacts]}

def _eval(kind,provider,model,length=None):
    safe="".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in model)
    name=f"{kind}__{provider}__{safe}"+(f"__{length}turns" if kind=="memory" else "")
    cmd=[sys.executable,"training_control/run_eval_job_v1.py","--kind",kind,"--provider",provider,"--model",model,"--num-samples",os.environ.get("TRUTHGUARD_NUM_SAMPLES","0"),"--num-ctx",os.environ.get("TRUTHGUARD_NUM_CTX","2048"),"--max-context",os.environ.get("TRUTHGUARD_MAX_CONTEXT","8192")]
    if length is not None:cmd.extend(["--session-length",str(length)])
    return {"id":f"eval/{name}","command":cmd,"phase":"evaluation","family":f"truthguard/{kind}","device_capable":False,"depends_on":["prepare-evidence-data","audit-no-trainable-surface"],"is_training_job":False,"resume_strategy":"clean_transaction_restart","checkpoint_contract":{"exact_resume":False,"reason":"external provider hidden state is not locally checkpointable"},"early_stopping_applicable":False,"early_stopping_exception_reason":"external pretrained-model evaluation, not optimizer training","completion_artifacts":[str(EVAL_ROOT/name/"COMPLETE.json")],"provider":provider,"model":model,"pipeline":kind,"session_length":length,"external_service_transaction":True,"source_configuration_only":False}

def iter_jobs()->Iterator[dict[str,Any]]:
    yield _restart("audit-no-trainable-surface",[sys.executable,"scripts/audit_no_trainable_surface_v1.py"],"audit","scientific-authority",[],[ROOT/"artifacts"/"training_control"/"no_trainable_surface_v1.json"])
    yield _restart("prepare-evidence-data",[sys.executable,"experiments/generate_eval_data.py"],"setup","evaluation-data",["audit-no-trainable-surface"],[ROOT/"evidence_data"/"eval_set.json"])
    ids=[]
    for provider,model in _models():
        for kind in ("edgecore","pipeline"):
            row=_eval(kind,provider,model);ids.append(row["id"]);yield row
        for length in _lengths():
            row=_eval("memory",provider,model,length);ids.append(row["id"]);yield row
    yield _restart("summarize-evaluations",[sys.executable,"experiments/summarize_results.py",str(EVAL_ROOT)],"reporting","truthguard/leaderboard",ids,[EVAL_ROOT/"leaderboard.txt"])

def catalog_metadata():
    return {"schema_version":1,"repository":"Anurag9000/hallucination-resistant-llm-framework","optimizer_training":False,"pipelines":["v1_edgecore_baseline_and_gated","v1.1_finalthought_verification_cache","v2_context_aware_memory_vault"],"providers_models":[{"provider":p,"model":m} for p,m in _models()],"memory_lengths":list(_lengths()),"dataset":"evidence_data/eval_set.json","evaluation_scripts":["experiments/run_edgecore_eval.py","experiments/run_pipeline_eval.py","experiments/run_memory_eval.py"],"external_service_restart_exact":False,"execution_claim_emitted":False}

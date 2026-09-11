#!/usr/bin/env python3
"""One-command exhaustive TruthGuard scientific lifecycle controller.

TruthGuard intentionally performs no model fine-tuning. The repository-owned v1
authority therefore (1) fails closed if an authored optimizer/trainer appears, and
(2) exposes the complete retained evaluation surface as OPF-visible transactions:
EdgeCore baseline/gated ablation, FinalThought verification/cache, and Context-Aware
Memory Vault across the authored Qwen/Llama/Gemini comparison models and memory
lengths, followed by the unified leaderboard.

External provider hidden state is explicitly not called optimizer-exact resume.
Resource admission, concurrency, pressure handling, retry and process control remain
exclusively in the literal byte-pinned OPF_ADP runtime loaded by controller v37.
"""
from __future__ import annotations
import hashlib,json,os,subprocess,sys,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
R="Anurag9000/hallucination-resistant-llm-framework"
C="fd34a95d18892df7fb14d1efbb99076a7810fb91";S="05ef472b29933f18e956c69dfb7e543921ddaff5";U=f"https://raw.githubusercontent.com/Anurag9000/RigorousRAG/{C}/tools/universal_training_controller_entry.py"
CATALOG="training_control/scientific_job_catalog_v1.py"
PROFILE={"repository":R,"scientific_authority":CATALOG,"job_catalog":{"path":CATALOG,"function":"iter_jobs","args":[],"kwargs":{}},"preferred_training_entrypoints":[],"preferred_dataset_entrypoints":[],"dynamic_registry_covers":["core/**/*.py","models/**/*.py","experiments/*.py","evidence_data/eval_set.json","training_control/*.py"],"ignore_entrypoints":["run_all_training.py","experiments/run_all.sh"],"strict_coverage":True,"require_native_resume":True,"require_exact_resume":True,"require_training_exact_resume":True,"require_training_early_stopping":True,"require_well_formed_training_exemptions":True,"require_dag_enforcement":True,"require_model_surface_accounting":True,"require_workload_surface_accounting":True,"require_literal_opf_mechanism_parity":True,"require_registry_member_accounting":True,"require_dynamic_registry_accounting":True,"require_scientific_component_config_accounting":True,"require_declared_combination_accounting":True,"require_scientific_ontology_accounting":True,"require_declarative_scientific_source_accounting":True,"require_extended_scientific_component_accounting":True,"require_full_scientific_choice_accounting":True,"require_role_paradigm_protocol_accounting":True,"require_existing_job_targets":True,"require_source_proven_training_exact_resume":True,"require_source_proven_training_early_stopping":True,"require_all_retained_trainable_source_reachability":True,"auto_console_training_jobs":False,"auto_console_subcommand_jobs":False}
def h(x):return hashlib.sha1(f"blob {len(x)}\0".encode()+x).hexdigest()
def atomic(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+".tmp");tmp.write_bytes(data);os.replace(tmp,path)
def main():
 q=ROOT/".training_control"/"universal_training_controller_entry.py"
 if not q.is_file() or h(q.read_bytes())!=S:
  x=urllib.request.urlopen(U,timeout=60).read()
  if h(x)!=S:raise RuntimeError("Pinned controller checksum mismatch")
  atomic(q,x)
 p=ROOT/".training_control"/"truthguard_scientific_v1_v37.json";atomic(p,(json.dumps(PROFILE,indent=2,sort_keys=True)+"\n").encode())
 e=os.environ.copy();e.pop("TRAINING_CONTROL_PROFILE",None);e["TRAINING_CONTROL_PROFILE_FILE"]=str(p);e["TRAINING_CONTROL_REPO_ROOT"]=str(ROOT);e.setdefault("TRAINING_CONTROL_TERMINATION_GRACE_SEC","30");return subprocess.call([sys.executable,str(q),*sys.argv[1:]],cwd=ROOT,env=e)
if __name__=="__main__":raise SystemExit(main())

#!/usr/bin/env python3
"""Fail closed if this inference/evaluation framework gains an authored trainer."""
from __future__ import annotations
import ast
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={".git",".training_control","__pycache__",".venv","venv","build","dist"}
EXCLUDED_FILES={"run_all_training.py","training_control/no_trainable_surface_v1.py","scripts/audit_no_trainable_surface_v1.py"}
ATTRS={"fit","partial_fit","fit_generator","train_on_batch","backward","zero_grad","optimizer_step","training_step","manual_backward"}
NAMES={"Trainer","Seq2SeqTrainer","TrainingArguments","Optimizer","SGD","Adam","AdamW","Adagrad","Adadelta","RMSprop","LBFGS","SparseAdam"}
PREFIXES=("torch.optim","tensorflow.keras.optimizers","keras.optimizers","pytorch_lightning","lightning.pytorch")

@dataclass(frozen=True,slots=True)
class Finding:
    path:str; line:int; kind:str; symbol:str

class Scanner(ast.NodeVisitor):
    def __init__(self,path:Path): self.path=path; self.findings:list[Finding]=[]
    def add(self,node:ast.AST,kind:str,symbol:str): self.findings.append(Finding(self.path.relative_to(ROOT).as_posix(),int(getattr(node,"lineno",0) or 0),kind,symbol))
    def visit_Import(self,node):
        for alias in node.names:
            if alias.name.startswith(PREFIXES): self.add(node,"training_import",alias.name)
        self.generic_visit(node)
    def visit_ImportFrom(self,node):
        module=node.module or ""
        if module.startswith(PREFIXES): self.add(node,"training_import",module)
        for alias in node.names:
            if alias.name in NAMES: self.add(node,"training_symbol_import",f"{module}.{alias.name}".strip("."))
        self.generic_visit(node)
    def visit_Call(self,node):
        f=node.func
        if isinstance(f,ast.Attribute) and f.attr in ATTRS: self.add(node,"training_call",f.attr)
        elif isinstance(f,ast.Name) and f.id in NAMES: self.add(node,"training_constructor",f.id)
        self.generic_visit(node)

def audit()->dict[str,object]:
    files=[]; findings=[]; parse_errors=[]
    for path in sorted(ROOT.rglob("*.py")):
        rel=path.relative_to(ROOT)
        if rel.as_posix() in EXCLUDED_FILES or any(p in EXCLUDED for p in rel.parts): continue
        files.append(path)
        try: tree=ast.parse(path.read_text(encoding="utf-8",errors="replace"),filename=str(path))
        except SyntaxError as exc:
            parse_errors.append({"path":rel.as_posix(),"line":int(exc.lineno or 0),"message":str(exc)}); continue
        scanner=Scanner(path); scanner.visit(tree); findings.extend(scanner.findings)
    unresolved=[]
    if parse_errors: unresolved.append({"type":"python_parse_errors","values":parse_errors})
    if findings: unresolved.append({"type":"retained_training_primitives_detected","values":[asdict(x) for x in findings]})
    return {"schema_version":1,"repository":"Anurag9000/hallucination-resistant-llm-framework","classification":"pretrained_inference_and_evaluation_only" if not unresolved else "training_surface_detected","retained_python_files":[p.relative_to(ROOT).as_posix() for p in files],"training_findings":[asdict(x) for x in findings],"parse_errors":parse_errors,"unresolved":unresolved,"complete":not unresolved,"source_configuration_only":True,"training_executed_by_audit":False,"benchmark_claim_emitted":False}

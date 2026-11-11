from __future__ import annotations
import json,platform,sys
from pathlib import Path
import qiskit,qiskit_aer,pennylane,torch
from qiskit import transpile
from qiskit_aer import AerSimulator
from .quantum_models import circuits,circuit_metadata
from .simulation.quantum_sampler import build_subscription_circuit

def _qiskit_resources(qc,name,backend=None):
    backend=backend or AerSimulator(); tq=transpile(qc,backend,optimization_level=1,seed_transpiler=42)
    one={k:int(v) for k,v in tq.count_ops().items() if k not in ("cx","cz","swap","rzz","rxx","ryy","measure")}
    two={k:int(v) for k,v in tq.count_ops().items() if k in ("cx","cz","swap","rzz","rxx","ryy")}
    return {"name":name,"framework":"Qiskit","backend":"AerSimulator (local)","logical_qubits":qc.num_qubits,"physical_qubits":"N/A (simulator)",
      "original_depth":qc.depth(),"transpiled_depth":tq.depth(),"one_qubit_gate_counts":one,"two_qubit_gate_counts":two,
      "total_transpiled_operations":tq.size(),"swap_count":int(tq.count_ops().get("swap",0)),"shots":"varies by experiment","seed":42}

def generate_circuit_audit(out="reports/quantum_circuit_resources.json"):
    fm,ans=circuits(); records=[_qiskit_resources(fm,"QSVC ZZ feature map"),_qiskit_resources(fm.compose(ans),"VQC feature map + ansatz"),
      _qiskit_resources(build_subscription_circuit([.5]*6),"Stage 3 probability circuit")]
    existing=Path("reports/stage2_circuit_complexity.json")
    if existing.exists():
        s=json.loads(existing.read_text())
        for name,v in s.items():
            if name=="formulation": continue
            records.append({"name":name,"framework":"Qiskit","backend":"AerSimulator (local)","logical_qubits":v["qubits"],"physical_qubits":"N/A (simulator)",
              "original_depth":v["depth"],"transpiled_depth":v["depth"],"one_qubit_gate_counts":"See gate_counts","two_qubit_gate_counts":"See gate_counts",
              "total_transpiled_operations":v["size"],"swap_count":int(v["gate_counts"].get("swap",0)),"gate_counts":v["gate_counts"],"shots":128,"seed":"42 or 137"})
    pl=Path("reports/quantum_circuits/complexity.json")
    if pl.exists():
        d=json.loads(pl.read_text())
        for name,v in d.items():
            if name=="qiskit" or not isinstance(v,dict): continue
            records.append({"name":name,"framework":"PennyLane","backend":"default.qubit/lightning.qubit","logical_qubits":v.get("qubits"),"physical_qubits":"N/A (simulator)",
              "original_depth":v.get("depth"),"transpiled_depth":"N/A (framework simulator; no target transpilation)","gate_counts":v.get("counts",{}),"total_gates":v.get("gates"),
              "swap_count":"N/A","shots":"analytic or experiment-specific","seed":"42/137 depending experiment"})
    result={"environment":{"python":sys.version,"platform":platform.platform(),"qiskit":qiskit.__version__,"qiskit_aer":qiskit_aer.__version__,"pennylane":pennylane.__version__,"torch":torch.__version__},"circuits":records}
    Path(out).write_text(json.dumps(result,indent=2),encoding="utf-8"); return result

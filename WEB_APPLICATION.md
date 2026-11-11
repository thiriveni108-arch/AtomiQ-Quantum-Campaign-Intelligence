# AtomiQ web application

## Architecture

The product is split into two isolated layers so the validated scientific CLI remains unchanged:

- `api/`: FastAPI adapter that reads official artifacts, exposes chart-ready summaries, launches existing CLI runs, and recomputes sandbox exact optimization through the existing solver.
- `web/`: Next.js App Router application with TypeScript, Tailwind, Framer Motion, React Three Fiber/Drei, ECharts, and Zustand.

The browser never rewrites official artifacts directly. Official pipeline execution is delegated to `run_end_to_end.py`; demo execution uses the existing demo mode. Sandbox results are returned in memory and labeled `sandbox`.

## Routes

- `/` — Command Center: product narrative, interactive 3D pipeline, official KPIs, selected campaign, run timeline, and snapshots.
- `/quantum-lab` — model comparison, circuit library, Stage 3 probability exploration, and experiment history.
- `/campaign-studio` — visual top-10 universe, exact/QAOA comparison, recommendation panel, and isolated what-if sandbox.

## Light visual system

The application uses one permanent light theme: `#F8FAFE` architectural-grid background, white primary surfaces, pale blue-gray secondary surfaces, and a localized violet/blue glow in the upper-right. A floating sidebar replaces horizontal navigation and expands from a 72px rail to a labeled 240px navigation surface. Cards use restrained pointer-reactive highlights, keyboard-visible focus rings, and reduced-motion fallbacks.

Scientific charts share a light ECharts treatment with high-contrast axes, dashed grid lines, white tooltips, restrained quantum/classical colors, and fullscreen controls. The model feature-space scene is built from the actual 300 training-fitted PCA angle coordinates. The Campaign Studio landscape contains all 210 actually enumerated six-customer combinations.

## Real-time versus saved results

- Official views load the real top-level submission files and generated result/report artifacts.
- **Run full pipeline** starts the real existing official CLI and polls its job status.
- Validation and demo jobs use their real CLI modes.
- Sandbox budget/capacity changes run real exact enumeration immediately.
- Sandbox QAOA cards use saved official experiments and say so explicitly. When constraints differ, they are labeled reference-only; expensive QAOA is not silently represented as recomputed.
- Circuit diagrams and resources come from generated audit and Qiskit text artifacts.

## Start locally

From the project root, open two PowerShell terminals.

API:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000
```

Frontend:

```powershell
cd web
npm.cmd install
npm.cmd run dev
```

Open `http://localhost:3000`. For production verification use `npm.cmd run build` and `npm.cmd start`.

## Modes

- **Official:** validated files, green trust indicators, real submission outputs.
- **Demo:** safe synthetic artifacts and replay jobs.
- **Sandbox:** amber visual treatment, in-memory what-if results, never written into official files.

## Limitations

- Full official/QAOA reruns are compute jobs and currently use process-local job state; a production deployment should add a persistent queue.
- QAOA under changed sandbox constraints is intentionally not recomputed by default. The live exact result is real; saved QAOA evidence is clearly labeled.
- The model repository contains aggregate/fold metrics but not pointwise PR/ROC/calibration coordinates, so the UI does not fabricate those curves.
- The API currently permits the local frontend origin only. Configure authenticated origins before external deployment.

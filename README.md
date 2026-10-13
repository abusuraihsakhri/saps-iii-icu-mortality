# SAPS 3 Hospital Mortality Estimator

Estimate **in-hospital mortality** from an **already calculated SAPS 3 admission score** using the original 2005 global model. This project does **not** calculate the full 20-variable SAPS 3 score from clinical observations.

## What it does

- Browser calculator: open the repository's root `index.html` directly, or serve the project with a static web server.
- Python conversion for a single precomputed score or CSV batch.
- FastAPI endpoint, `POST /api/mortality`, taking a single integer `saps3_score`.
- Input validation (integer 0–217) and tests against published-model reference values.

The original equation is:

`logit = -32.6659 + 7.3068 * ln(SAPS3 + 20.5958)`

`P(in-hospital death) = 1 / (1 + exp(-logit))`

Example: **SAPS 3 = 50 → 17.35% predicted in-hospital mortality** using the global model.

**Reference:** Moreno RP, Metnitz PGH, Almeida E, et al. *SAPS 3—From evaluation of the patient to evaluation of the intensive care unit. Part 2.* Intensive Care Med. 2005;31:1345–1355. [doi:10.1007/s00134-005-2763-5](https://doi.org/10.1007/s00134-005-2763-5).

## Use

Requires Python 3.10 or newer for the CLI.

```bash
python saps3_calc.py single --score 50
python saps3_calc.py batch -i sample.csv -o results.csv
```

The batch CSV must include a `saps3_score` column (one integer per row). Other columns are retained in the local output. Output includes probability (0–1) and percent (0–100). Use de-identified records.

For the API and development tools:

```bash
python -m pip install -e ".[dev]"
python -m pytest -v
uvicorn agents.api:app --host 127.0.0.1 --port 8000
```

API example:

```bash
curl -X POST http://127.0.0.1:8000/api/mortality \
  -H "Content-Type: application/json" \
  -d '{"saps3_score":50}'
```

Open `http://127.0.0.1:8000/` for the same browser calculator. API documentation is available at `/docs` and `/openapi.json`.

Alternatively, run `docker compose up --build`; Docker Compose binds to `127.0.0.1:8000` by default. If using audit demonstrations, set `AUDIT_SECRET_KEY` securely in the environment rather than committing it.

## Limitations and clinical safety

SAPS 3 is based on **20 variables** collected around ICU admission, within the original score's specified admission window. Enter only a correctly computed total score; this repository does not implement the score sheet. The global equation was developed in a multinational cohort and may be miscalibrated for a particular unit or population. Regional recalibration and local validation may be necessary.

**This calculator is for education and research, not individual treatment decisions, patient triage, automated interventions, or stand-alone clinical deployment.** It predicts death before hospital discharge—not ICU death or 28-day mortality. There are no validated risk categories or clinical recommendations in the calculator.

The historical `agents/`, `enrichment.py`, and `cli.py` audit workflows remain for backwards compatibility. They contain **synthetic threshold demonstrations**, not validated SAPS 3 physiology, clinical protocols, PHI de-identification, or production-quality medical decision support. Their audit chain is signed **in process and held only in memory**; it is not a durable, independently anchored audit ledger. The mock chat backend produces no validated clinical interpretation. The `/api/audit` and `/api/chat` routes are legacy demonstration endpoints.

## Privacy and implementation

- The standalone HTML/JavaScript calculator performs all calculations in the browser and does not send the entered score to a server, store it, or use third-party scripts.
- Python CLI/CSV operations stay on the machine running the command.
- FastAPI receives values sent to its endpoints. Do not submit patient identifiers or protected health information to a hosted API; pattern screening is not a complete de-identification safeguard.
- The browser uses standard HTML, CSS, and JavaScript and requires no browser Python/WebAssembly runtime.
- The package uses Python, FastAPI, Pydantic, and pytest. It is tested in CI on Python 3.10–3.12. A modern browser with JavaScript enabled is required.

## License

[MIT](LICENSE). The published SAPS 3 methodology and its applicable source attribution remain with the original investigators.
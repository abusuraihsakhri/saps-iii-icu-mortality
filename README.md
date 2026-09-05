# SAPS III ICU Mortality

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Reference Guidelines & Standards:** Standard Clinical Formulations & ISO/IEC Quality Frameworks

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## Overview

Simplified Acute Physiology Score III (SAPS 3) calculator for ICU admission mortality prediction.

This project provides a zero-dependency Python implementation with single and batch evaluation capabilities, featuring a multi-agent enterprise architecture with PHI protection and cryptographic audit trails.

**Author:** Dr. Abu Suraih Sakhri
**License:** MIT

---

## Features

### Core Calculation Engine (`saps3_calc.py`)
- **`calculate_metrics()`** - Core scoring algorithm with input validation
- **`process_single()`** - Evaluate a single case with parameterized inputs
- **`process_batch()`** - Process CSV files with multiple records

### Enterprise Agent Framework (`agents/`)
- **Multi-Worker Evaluation** - InvariantQC, SafetyEscalation, and ProtocolConformance workers
- **PHI Outbound Guard** - AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
- **HMAC-SHA256 Audit Trail** - Chained, cryptographically signed logs for every evaluation
- **FastAPI REST API** - OpenAPI 3.1 endpoints with Prometheus telemetry

### Enrichment Modules (`enrichment.py`)
- Ventilator Weaning Readiness Prediction
- Fluid Responsiveness Assessment
- Vasopressor Titration Guidance
- RRT Activation Auto-Trigger
- Organ Donor Management Protocol
- Prone Positioning Decision Support
- Family Communication Auto-Generation
- Delirium Screening Integration

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/saps-iii-icu-mortality.git
cd saps-iii-icu-mortality

# Install dependencies
pip install fastapi uvicorn pydantic pytest
```

---

## Usage

### CLI - Single Case Evaluation
```bash
python saps3_calc.py single --v1 14.5 --v2 4.2 --v3 1.8
```

### CLI - Batch CSV Processing
```bash
python saps3_calc.py batch -i sample.csv -o results.csv
```

### Enterprise CLI
```bash
# Run audit evaluation
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Batch processing
python cli.py batch -i sample.csv -o results.csv

# Verify audit trail integrity
python cli.py verify-audit

# Launch REST API server
python cli.py serve --host 127.0.0.1 --port 8000
```

### REST API
```bash
# Start server
python cli.py serve

# Health check
curl http://localhost:8000/health

# Process audit
curl -X POST http://localhost:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{"task-id": "T001", "target_identifier": "KEY-01", "primary_metric": 25.0}'

# View metrics
curl http://localhost:8000/metrics
```

---

## Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Patient identifier | Required |
| `v1` | Primary measurement value | Required |
| `v2` | Secondary measurement value | Required |
| `v3` | Tertiary measurement value | Required |

---

## Security

- **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
- **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation
- **Input Validation:** Numeric bounds checking and NaN/Inf detection
- **Path Traversal Protection:** File path validation for batch operations
- **Secure Defaults:** Auto-generated cryptographic secrets when not explicitly configured

---

## Testing

```bash
# Run full test suite
pytest -v

# Run with coverage
pytest -v --cov

# Run simulation benchmark
python simulator.py 1000
```

---

## Docker Deployment

```bash
# Build and run
docker build -t saps-iii-icu-mortality .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key saps-iii-icu-mortality

# Or use docker-compose
docker-compose up -d
```

---

## Project Structure

```
saps-iii-icu-mortality/
├── agents/                 # Enterprise agent framework
│   ├── api.py             # FastAPI REST server
│   ├── base.py            # Security, PHI guard, audit trail
│   ├── models.py          # Pydantic data models
│   ├── supervisor.py      # Multi-agent orchestrator
│   ├── workers.py         # Specialized evaluation workers
│   ├── llm_factory.py     # LLM provider abstraction
│   ├── metrics.py         # Prometheus metrics
│   ├── learning.py        # Bayesian calibration engine
│   └── streamer.py        # WebSocket telemetry
├── tests/                 # Test suite
├── saps3_calc.py          # Core calculation engine
├── cli.py                 # Enterprise CLI
├── enrichment.py          # Clinical enrichment modules
├── simulator.py           # High-throughput testing
├── web/index.html         # Operations console
├── Dockerfile             # Container definition
├── docker-compose.yml     # Compose configuration
└── pyproject.toml         # Project metadata
```

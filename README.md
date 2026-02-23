# FHIR-RAG-MED Interpretation System

## Overview
The **FHIR-RAG-MED Interpretation System** is a backend module designed for interpreting FHIR Bundles in compliance with the **SMART on FHIR** specification. This system allows users to fetch FHIR data from a SMART-enabled FHIR server and process it for medical recommendations using either a cloud-based API or a local Llama model.

## Configuration
The system is configured via `config.py`:

- `OPENROUTERAI_API_KEY`: API key for OpenRouter AI (Required if running bundle interpretation via cloud API).
- `RUN_BUNDLE_INTERPRETATION_LOCAL`: Determines how FHIR bundle interpretation is executed:
  - `False` (Default): Uses OpenRouter AI for interpretation.
  - `True`: Runs interpretation locally using Ollama.
    - Install Ollama.
    - Pull the model (if your machine has the necessary resources): `ollama pull llama3.3:70b`

## Installation
1. Extract the repository.
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Running the System
The system can be run in two modes depending on the availability of the FHIR Bundle.

### 1. Running as a Backend Service
If the FHIR Bundle needs to be fetched first:

#### Using Docker
```sh
docker compose up
```

#### Using a Local Python Environment
```sh
backend.bat  # Windows
# OR
set PYTHONPATH=. && python src/app/app.py  # Manually running the backend
```

After starting the backend, use the following cURL requests to fetch and interpret the FHIR Bundle:

#### Fetch FHIR Data
```sh
curl 'http://localhost:8000/fetch-fhir-data'   -H 'Accept: application/json, text/plain, */*'   -H 'Content-Type: application/json'   --data-raw '{"access_token":"eyJhbGciO...","patient_id":"pat12","fhir_server":"https://kroniq.srdc.com.tr/fhir"}'
```

#### Interpret FHIR Data
```sh
curl 'http://localhost:8000/interpret_fhir'   -H 'Accept: application/json, text/plain, */*'   -H 'Content-Type: application/x-www-form-urlencoded'   --data-raw 'fhir_bundle='
```

### 2. Running with an Existing FHIR Bundle
If you already have a FHIR Bundle, you can run the interpretation directly via command line:

```sh
set PYTHONPATH=. && python src/core/recommendation/interpretation.py -b fhir_bundle_file.json
```

## Notes
- Ensure the FHIR server is **SMART-on-FHIR enabled**.
- When using Docker, the service will be available at `http://localhost:8000/`.
- The system supports both **remote API** and **local model-based** interpretation for flexibility.

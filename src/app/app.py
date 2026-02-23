from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware
from pydantic import BaseModel
import requests

from src.core.recommendation.interpretation import interpret_fhir_bundle_text
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware to allow requests from specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Allow only the frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

@app.get("/")
def read_root():
    return {"message": "FHIR-RAG-MED Backend Running"}

# Send a FHIR Bundle for textual medical interpretation
@app.post("/interpret_fhir")
async def interpret_fhir_bundle_endpoint(fhir_bundle: str = Form(...)):
    # Interpret the FHIR bundle directly from the text
    try:
        # Switch from local and remote (with orai)
        interpretation = interpret_fhir_bundle_text(fhir_bundle)
        logger.info(f"✅ Interpretation:\n {interpretation}")

        return JSONResponse(content={"interpretation": interpretation})

    except Exception as e:
        logging.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

class TokenRequest(BaseModel):
    access_token: str
    patient_id: str
    fhir_server: str  # Dynamic FHIR server selection

from src.core.utils.fhir_util import fetch_fhir_resource, process_fhir_observations, clean_fhir_bundle #, remove_sensitive_data

class TokenRequest(BaseModel):
    access_token: str
    patient_id: str
    fhir_server: str  # FHIR server URL

from fastapi import HTTPException
import requests
import logging

@app.post("/fetch-fhir-data")
def fetch_fhir_data(request_data: TokenRequest):
    """
    Fetches patient details, observations (vital signs & lab), medications, and conditions.
    Generates a FHIR-compliant Bundle on the backend before returning data.
    """
    try:
        fhir_server = request_data.fhir_server
        access_token = request_data.access_token
        patient_id = request_data.patient_id

        logging.info(f"🔵 Received request for Patient ID: {patient_id} on FHIR Server: {fhir_server}")

        # Fetch Patient
        patient_url = f"{fhir_server}/Patient/{patient_id}"
        logging.info(f"Requesting Patient details from {patient_url}")

        patient_response = requests.get(patient_url, headers={"Authorization": f"Bearer {access_token}"})
        if patient_response.status_code != 200:
            logging.error(f"❌ Failed to fetch Patient data - HTTP {patient_response.status_code}")
            raise HTTPException(status_code=patient_response.status_code, detail="Failed to fetch Patient data")

        patient = patient_response.json()
        logging.info(f"✅ Successfully fetched Patient data")

        # Fetch Observations (Vital Signs & Lab)
        vital_signs = fetch_fhir_resource(fhir_server, "Observation", patient_id, access_token, {"category": "vital-signs"})
        lab_observations = fetch_fhir_resource(fhir_server, "Observation", patient_id, access_token, {"category": "laboratory"})
        medications = fetch_fhir_resource(fhir_server, "MedicationStatement", patient_id, access_token)
        conditions = fetch_fhir_resource(fhir_server, "Condition", patient_id, access_token)

        logging.info(f"🔵 Fetched Observations: {len(vital_signs.get('entry', []))} vital signs, {len(lab_observations.get('entry', []))} labs")
        logging.info(f"🔵 Fetched Medications: {len(medications.get('entry', []))}")
        logging.info(f"🔵 Fetched Conditions: {len(conditions.get('entry', []))}")

        # Process observations
        processed_vital_signs = process_fhir_observations(vital_signs, category_name="Vital Signs", exclude_code="8716-3")
        processed_lab_observations = process_fhir_observations(lab_observations, category_name="Laboratory")

        # ✅ Generate a valid FHIR R4 Bundle
        fhir_bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": []
        }

        # ✅ Fix the patient entry (must be wrapped in a dictionary inside "entry")
        fhir_bundle["entry"].append({"resource": patient})

        # ✅ Extend with lists safely
        fhir_bundle["entry"].extend(processed_vital_signs)  # List of dictionaries
        fhir_bundle["entry"].extend(processed_lab_observations)  # List of dictionaries
        fhir_bundle["entry"].extend(medications.get("entry", []))  # List of dictionaries
        fhir_bundle["entry"].extend(conditions.get("entry", []))  # List of dictionaries

        # ✅ Ensure a valid FHIR R4 Bundle structure
        cleaned_bundle = clean_fhir_bundle(fhir_bundle)

        logging.info(f"✅ Successfully generated FHIR Bundle with {len(cleaned_bundle['entry'])} entries.")

        return cleaned_bundle  # Return the final FHIR Bundle

    except Exception as e:
        logging.error(f"❌ An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Start the FastAPI application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

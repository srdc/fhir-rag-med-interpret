import requests
from fastapi import HTTPException

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def fetch_fhir_resource(fhir_server, resource_type, patient_id, access_token, additional_params=None):
    """
    Fetches a specific FHIR resource by sending a direct request to the FHIR server.
    Logs API calls for debugging.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"subject": f"Patient/{patient_id}"}

    if additional_params:
        params.update(additional_params)

    url = f"{fhir_server}/{resource_type}"
    logging.info(f"Requesting {resource_type} from {url} with params {params}")

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        logging.info(f"✅ Successfully fetched {resource_type} from {fhir_server}")
        return response.json()
    else:
        logging.error(f"❌ Failed to fetch {resource_type} from {fhir_server} - HTTP {response.status_code}")
        raise HTTPException(status_code=response.status_code, detail=f"Failed to fetch {resource_type}")
    
import uuid
from typing import List, Dict, Any, Optional

def clean_fhir_bundle(bundle):
    """ Ensures that each entry in the FHIR bundle is properly formatted. """
    for entry in bundle.get("entry", []):
        if "resource" in entry and isinstance(entry["resource"], dict) and "resource" in entry["resource"]:
            entry["resource"] = entry["resource"]["resource"]  # Remove extra 'resource' nesting
    return bundle

def process_fhir_observations(
    observations_bundle: Dict[str, Any],
    category_name: str,
    exclude_code: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filters, groups, and extracts the most recent FHIR R4 observations.
    Ensures the returned observations match the expected FHIR Bundle format.

    :param observations_bundle: FHIR Bundle (JSON) containing Observation resources.
    :param category_name: Category name for logging (e.g., "Vital Signs", "Laboratory").
    :param exclude_code: Optional LOINC code to filter out (e.g., '8716-3' for vital signs).
    :return: List of processed Observation entries (matching FHIR Bundle format).
    """
    mapping: Dict[str, str] = {}
    grouped: Dict[str, List[Dict[str, Any]]] = {}

    if "entry" not in observations_bundle:
        logger.warning(f"⚠️ No 'entry' found in the {category_name} bundle. Returning empty list.")
        return []

    logger.info(f"🔵 Processing {len(observations_bundle['entry'])} {category_name.lower()} observations from FHIR bundle.")

    for entry in observations_bundle["entry"]:
        observation = entry.get("resource")
        if not observation or observation["resourceType"] != "Observation":
            logger.debug(f"Skipping non-Observation entry: {entry}")
            continue

        # Extract codings and optionally filter out a specific code
        codings = observation.get("code", {}).get("coding", [])
        if exclude_code:
            codings = [coding for coding in codings if coding.get("code") != exclude_code]

        if not codings:
            logger.debug(f"Skipping Observation {observation.get('id', 'unknown')} - No valid codings found.")
            continue  # Skip observations with no valid codings

        # Assign a unique group ID based on codes
        code_id = next((mapping[coding["code"]] for coding in codings if coding["code"] in mapping), str(uuid.uuid4()))
        for coding in codings:
            mapping[coding["code"]] = code_id

        grouped.setdefault(code_id, []).append(entry)

    if not grouped:
        logger.warning(f"⚠️ No valid {category_name.lower()} observations found after filtering.")
        return []

    logger.info(f"✅ Grouped {sum(len(g) for g in grouped.values())} observations into {len(grouped)} groups.")

    # Sort each group by effectiveDateTime in descending order (most recent first)
    for group_id, group in grouped.items():
        group.sort(key=lambda obs: obs["resource"].get("effectiveDateTime", ""), reverse=True)
        logger.debug(f"Sorted {len(group)} observations in group {group_id} by effectiveDateTime.")

    # Extract only the most recent observation from each group, keeping the full entry format
    processed_observations = [group[0] for group in grouped.values()]
    logger.info(f"✅ Extracted {len(processed_observations)} most recent {category_name.lower()} observations from each group.")

    return processed_observations

import argparse, time
from langchain.prompts import PromptTemplate
from langchain_community.llms.ollama import Ollama
from src.core.utils.llm_util import call_orai
import logging
from src.config import RUN_BUNDLE_INTERPRETATION_LOCAL
from src.config import BUNDLE_INTERPRETATION_MODEL_NAME

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

FHIR_PROMPT_TEMPLATE = """
Your task is to summarize HL7 FHIR JSON resources of the patient only from medical perspective in one paragraph only.
Just convert the FHIR resources to a medical summary. 
Don't put your interpretation. 
Don't use bullets, lists or titles in your interpretation.
Don't mention about technical details like JSON, FHIR resources, and other implementation details of the underlying data resources. 
Don't explain the FHIR Bundle elements one by one.
Don't mention about the patient's contact, address, id and personal details. Only mention about medical conditions.
Explain the relevant medical context in a language understandable by a medical professional. 
When presenting the patient, calculate the age of the patient. Don't mention about the birth date. 
You should provide factual and precise information. 
If there is information about medications, tell about the count of the medications, ATC parent names of the medications (like ARB, diuretics, beta-blocker, etc.) next to the medications.
Don't interpret general condition of the patient. Don't ask additional requests. Just respond and finish. Don't make introduction like "here is the interpretation".
If there is no information about medication in the fhir bundle, state that the patient does not use drugs or medications. 
If there is no information about observation or condition in the fhir bundle, state that there is no mentioned observation or condition. 
Summarize all the lab results and vital sign observations.
Mention also about the patient race.
Write each sentence in a new line. Don't put empty lines between the sentences.
Only talk about what is available. Don't talk what is not available.
Don't mention about FHIR. 
---
Interpret the following HL7 FHIR Bundle based on the above context: 
{question}
"""

def main():
    # Create CLI.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bundle_file", "-b", type=str, help="The FHIR bundle file path."
    )

    args = parser.parse_args()

    bundle_file = args.bundle_file

    # Interpret the fhir bundle
    start = time.time()
    patient_medical_condition = interpret_fhir_bundle(bundle_file)
    logger.info(patient_medical_condition)
    execution_time = time.time() - start
    logger.info(f"Interpretation time: {execution_time} sec.")

def interpret_fhir_bundle_text(bundle_text: str):
    prompt_template = PromptTemplate.from_template(FHIR_PROMPT_TEMPLATE)
    prompt = prompt_template.format(question=bundle_text)

    if RUN_BUNDLE_INTERPRETATION_LOCAL:
        llm_model = Ollama(model=BUNDLE_INTERPRETATION_MODEL_NAME)
        response_text = llm_model.invoke(prompt)
    else:
        response_text = call_orai(prompt, BUNDLE_INTERPRETATION_MODEL_NAME)

    return response_text

def interpret_fhir_bundle(bundle_file_path: str):
    file = open(bundle_file_path, "r")
    content = file.read()
    file.close()

    response_text = interpret_fhir_bundle_text(content)

    return response_text

if __name__ == "__main__":
    main()

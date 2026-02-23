from langchain.evaluation import load_evaluator
import logging
import requests, json, time
from src.config import OPENROUTERAI_API_KEY

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def call_orai(formatted_prompt: str, model: str):
    model_mapping = {
        "llama3.1": "meta-llama/llama-3.1-8b-instruct",
        #"llama3.3:70b": "meta-llama/llama-3.3-70b-instruct",
        "llama3.3:70b": "meta-llama/llama-3.3-70b-instruct:free",
        "llama3.1:70b": "meta-llama/llama-3.1-70b-instruct",
        "llama3.1:405b": "meta-llama/llama-3.1-70b-instruct",
    }
    model_name = model_mapping.get(model)
    logger.info(f"Calling OpenRouterAI with model: {model_name}")

    retries = 10  # Number of retries
    retry_delay = 10  # Delay between retries in seconds

    for attempt in range(retries):
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTERAI_API_KEY}"},
                data=json.dumps(
                    {
                        "model": model_name,
                        "messages": [{"role": "user", "content": formatted_prompt}],
                    }
                ),
                timeout=30,
            )

            # Check if the response status code indicates a failure
            if response.status_code == 429:
                logger.warning(
                    f"Rate limit hit. Attempt {attempt + 1}/{retries}. Retrying in {retry_delay} seconds..."
                )
                time.sleep(retry_delay)
                continue

            response_json = response.json()

            # Check if the response contains the expected keys
            if "choices" not in response_json:
                logger.error(f"Unexpected response format: {response_json}")
                raise KeyError("Missing 'choices' in response JSON.")

            response_text = response_json["choices"][0]["message"]["content"]

            return response_text

        except requests.RequestException as e:
            logger.error(f"Request error on attempt {attempt + 1}/{retries}: {e}")
            if attempt < retries - 1:
                time.sleep(retry_delay)
            else:
                raise

        except KeyError as e:
            logger.error(
                f"Response processing error on attempt {attempt + 1}/{retries}: {e}"
            )
            if attempt < retries - 1:
                time.sleep(retry_delay)
            else:
                raise

    # If all retries fail, raise an exception or return a default value
    raise RuntimeError("All attempts to call the API have failed.")

import os

from anthropic import Anthropic
from dotenv import load_dotenv

from licenseflow_ai.models.deal_request import DealRequest


load_dotenv()

MODEL_NAME = os.getenv(
    "LICENSEFLOW_LLM_MODEL",
    "claude-sonnet-5-5",
)

WORKSPACE_ID = os.getenv("ANTHROPIC_WORKSPACE_ID")

client = Anthropic(
    default_headers={
        "anthropic-workspace-id": WORKSPACE_ID
    }
)

SYSTEM_PROMPT = """
You extract structured information from commercial licensing requests.

Rules:
- Extract only information explicitly stated by the user.
- Do not infer or invent missing information.
- If a value is not provided, return null.
- Keep customer and product names as written.
- Convert explicit contract durations into years.
- For discounts, return the numeric percentage only.
"""


def extract_deal_request(text: str)  -> DealRequest:
    response = client.messages.parse(
        model=MODEL_NAME,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                'role': 'user',
                'content': text,
            }
        ],
        output_format=DealRequest,
    )

    result = response.parsed_output

    if result is None:
        raise ValueError(
            'Claude response could not be parsed into DealRequest.'
        )
    
    return result
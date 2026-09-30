import os

from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()


MODEL_NAME = os.getenv(
    "LICENSEFLOW_LLM_MODEL",
    "claude-sonnet-5-5",
)

WORKSPACE_ID = os.getenv(
    "ANTHROPIC_WORKSPACE_ID"
)

headers = {}

if WORKSPACE_ID:
    headers["anthropic-workspace-id"] = WORKSPACE_ID

client = Anthropic(
    default_headers=headers,
)


class LegalDecision(BaseModel):
    legal_review_required: bool | None
    rationale: str


SYSTEM_PROMPT = """
You analyse internal company policies for licensing deals.

Use ONLY the policy excerpts provided by the application.

Do not use outside knowledge.

If the provided policies explicitly require Legal review,
return legal_review_required=true.

If they explicitly say Legal review is not required,
return false.

If the supplied policies are insufficient to determine this,
return null.

Give a short rationale based only on the supplied policy.
"""


def analyse_legal_policy(
    deal_description: str,
    policy_chunks: list[dict],
) -> LegalDecision:

    context = "\n\n---\n\n".join(
        (
            f"SOURCE: {chunk['source']}\n"
            f"{chunk['content']}"
        )
        for chunk in policy_chunks
    )

    user_message = f"""
DEAL:
{deal_description}

INTERNAL POLICY EXCERPTS:
{context}
"""

    response = client.messages.parse(
        model=MODEL_NAME,
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": user_message,
            }
        ],
        output_format=LegalDecision,
    )

    result = response.parsed_output

    if result is None:
        raise ValueError(
            "Legal policy analysis could not be parsed."
        )

    return result
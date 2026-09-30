import json
from pathlib import Path

from licenseflow_ai.models.audit import AuditEvent


AUDIT_LOG_PATH = Path(
    "logs/audit.jsonl"
)


def log_audit_event(
    event: AuditEvent,
) -> None:
    AUDIT_LOG_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with AUDIT_LOG_PATH.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(
                event.model_dump(
                    mode="json"
                ),
                ensure_ascii=False,
            )
            + "\n"
        )
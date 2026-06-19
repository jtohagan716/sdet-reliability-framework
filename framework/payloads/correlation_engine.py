DYNAMIC_FIELD_NAMES = {
    "sessionId",
    "appointmentId",
    "encounterId",
    "patientId",
    "timestamp",
    "requestId",
    "transactionId",
}

STATIC_FIELD_NAMES = {
    "transactionType",
    "facilityNcid",
    "workflow",
    "action",
    "resourceType",
}


def analyze_transaction_fields(transaction: dict) -> dict:
    dynamic_fields = []
    static_fields = []
    unknown_fields = []

    for field_name in transaction.keys():
        if field_name in DYNAMIC_FIELD_NAMES:
            dynamic_fields.append(field_name)
        elif field_name in STATIC_FIELD_NAMES:
            static_fields.append(field_name)
        else:
            unknown_fields.append(field_name)

    return {
        "dynamicFields": dynamic_fields,
        "staticFields": static_fields,
        "unknownFields": unknown_fields,
        "correlationCandidates": dynamic_fields,
        "replaySafe": len(dynamic_fields) > 0,
    }


def generate_correlation_report(transaction: dict) -> str:
    analysis = analyze_transaction_fields(transaction)

    return f"""
========================================
ENTERPRISE TRANSACTION CORRELATION REPORT
========================================

Transaction Type: {transaction.get("transactionType")}
Facility NCID:    {transaction.get("facilityNcid")}

----------------------------------------
STATIC FIELDS
----------------------------------------
{_format_field_list(analysis["staticFields"])}

----------------------------------------
DYNAMIC FIELDS
----------------------------------------
{_format_field_list(analysis["dynamicFields"])}

----------------------------------------
CORRELATION CANDIDATES
----------------------------------------
{_format_field_list(analysis["correlationCandidates"])}

----------------------------------------
UNKNOWN FIELDS
----------------------------------------
{_format_field_list(analysis["unknownFields"])}

Replay Safe: {analysis["replaySafe"]}

========================================
""".strip()


def _format_field_list(fields: list[str]) -> str:
    if not fields:
        return "None"

    return "\n".join(f"- {field}" for field in fields)
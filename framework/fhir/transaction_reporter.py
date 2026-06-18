from framework.fhir.transaction_inspector import inspect_transaction


def generate_transaction_report(transaction: dict) -> str:
    inspection = inspect_transaction(transaction)

    return f"""
========================================
HEALTHCARE TRANSACTION INSPECTION REPORT
========================================

Transaction Type: {transaction.get("transactionType")}
Facility NCID:    {transaction.get("facilityNcid")}
Appointment ID:   {transaction.get("appointmentId")}
Encounter ID:     {transaction.get("encounterId")}
User ID:          {transaction.get("userId")}
Workstation ID:   {transaction.get("workstationId")}

----------------------------------------
PAYLOAD SIZE ANALYSIS
----------------------------------------

UTF-8 Size:        {inspection["utf8_size_bytes"]} bytes
Compressed Size:  {inspection["compressed_size_bytes"]} bytes
Base64 Size:      {inspection["base64_size_bytes"]} bytes

Compression Savings: {inspection["compression_savings_percent"]}%
Base64 Overhead:     {inspection["transport_overhead_percent"]}%
Net Savings:         {inspection["net_savings_percent"]}%

----------------------------------------
TRANSPORT RECOMMENDATION
----------------------------------------

{inspection["recommendation"]}

----------------------------------------
TRANSPORT PAYLOAD
----------------------------------------

{inspection["base64_payload"]}

========================================
""".strip()
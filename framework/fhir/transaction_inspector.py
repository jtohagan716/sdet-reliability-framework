import base64
import json
import zlib


def inspect_transaction(transaction: dict) -> dict:
    serialized_json = json.dumps(transaction, separators=(",", ":"))
    utf8_bytes = serialized_json.encode("utf-8")
    compressed_bytes = zlib.compress(utf8_bytes)
    base64_payload = base64.b64encode(compressed_bytes).decode("utf-8")

    original_size = len(utf8_bytes)
    compressed_size = len(compressed_bytes)
    base64_size = len(base64_payload.encode("utf-8"))

    compression_savings_percent = round(
        ((original_size - compressed_size) / original_size) * 100,
        2,
    )

    transport_overhead_percent = round(
        ((base64_size - compressed_size) / compressed_size) * 100,
        2,
    )

    net_savings_percent = round(
        ((original_size - base64_size) / original_size) * 100,
        2,
    )

    recommendation = _build_transport_recommendation(
        original_size=original_size,
        compressed_size=compressed_size,
        base64_size=base64_size,
        net_savings_percent=net_savings_percent,
    )

    return {
        "business_object": transaction,
        "serialized_json": serialized_json,
        "utf8_size_bytes": original_size,
        "compressed_size_bytes": compressed_size,
        "base64_payload": base64_payload,
        "base64_size_bytes": base64_size,
        "compression_savings_percent": compression_savings_percent,
        "transport_overhead_percent": transport_overhead_percent,
        "net_savings_percent": net_savings_percent,
        "recommendation": recommendation,
    }


def decode_transaction_payload(base64_payload: str) -> dict:
    compressed_bytes = base64.b64decode(base64_payload.encode("utf-8"))
    utf8_bytes = zlib.decompress(compressed_bytes)
    serialized_json = utf8_bytes.decode("utf-8")

    return json.loads(serialized_json)


def _build_transport_recommendation(
    original_size: int,
    compressed_size: int,
    base64_size: int,
    net_savings_percent: float,
) -> str:
    if base64_size >= original_size:
        return (
            "DO NOT COMPRESS FOR TRANSPORT: "
            "Base64 transport size is larger than the original UTF-8 payload."
        )

    if net_savings_percent < 10:
        return (
            "COMPRESSION BENEFIT IS MARGINAL: "
            "Net transport savings are low after Base64 overhead."
        )

    return (
        "COMPRESSION IS BENEFICIAL: "
        "Compressed/Base64 transport size is smaller than the original UTF-8 payload."
    )
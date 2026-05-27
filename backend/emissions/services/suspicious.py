"""
Rule-based suspicious flags (utility spike detection).
"""
from decimal import Decimal

from django.db.models import Avg

from emissions.models import NormalizedEmissionRecord


def check_utility_usage_spike(
    *,
    tenant_id: int,
    meter_id: str,
    kwh_usage: Decimal,
    rolling_periods: int = 6,
    spike_multiplier: Decimal = Decimal("2"),
) -> tuple[bool, str]:
    """
    Flag usage if current kWh > spike_multiplier × rolling average for this meter.
    Uses prior approved/pending normalized records with same meter_id in raw_payload.
    """
    prior = NormalizedEmissionRecord.objects.filter(
        tenant_id=tenant_id,
        category="purchased_electricity",
        raw_record__raw_payload__meter_id=meter_id,
    ).order_by("-activity_date")[:rolling_periods]

    if not prior.exists():
        return False, ""

    avg_usage = prior.aggregate(avg=Avg("normalized_quantity"))["avg"]
    if avg_usage is None or avg_usage <= 0:
        return False, ""

    threshold = Decimal(str(avg_usage)) * spike_multiplier
    if kwh_usage > threshold:
        return True, (
            f"Usage {kwh_usage} kWh exceeds {spike_multiplier}× rolling average "
            f"({Decimal(str(avg_usage)).quantize(Decimal('0.01'))} kWh over {prior.count()} periods)."
        )
    return False, ""

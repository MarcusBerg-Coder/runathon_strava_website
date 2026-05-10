from datetime import datetime, timezone
from decimal import Decimal

from app.services.campaign import calculate_totals, is_activity_eligible, meters_to_miles


def test_calculate_totals_from_donations_and_miles() -> None:
    totals = calculate_totals(Decimal("250"), Decimal("10"), Decimal("12.4"))

    assert totals.dollarsRaised == 250
    assert totals.milesPledged == 25
    assert totals.milesCompleted == 12.4
    assert totals.milesRemaining == 12.6
    assert totals.completionPercent == 49.6


def test_activity_eligibility_requires_allowed_sport_and_campaign_window() -> None:
    starts = datetime(2026, 5, 1, tzinfo=timezone.utc)
    ends = datetime(2026, 6, 1, tzinfo=timezone.utc)

    assert is_activity_eligible("Run", datetime(2026, 5, 9, tzinfo=timezone.utc), starts, ends)
    assert is_activity_eligible("Walk", datetime(2026, 5, 9, tzinfo=timezone.utc), starts, ends)
    assert not is_activity_eligible("Ride", datetime(2026, 5, 9, tzinfo=timezone.utc), starts, ends)
    assert not is_activity_eligible("Run", datetime(2026, 6, 2, tzinfo=timezone.utc), starts, ends)


def test_meters_to_miles_rounds_to_thousandth() -> None:
    assert meters_to_miles(1609.344) == Decimal("1.000")


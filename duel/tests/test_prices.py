from datetime import date

import pytest

from duel_core import Price, PriceSchedule


def test_schedule_picks_the_price_in_force():
    s = PriceSchedule.parse("2026-09-30:0.75/3.75,2027-01-01:1.50/7.50")
    assert s.at(date(2026, 10, 2)).input_per_million == 0.75
    assert s.at(date(2027, 1, 1)).output_per_million == 7.50
    assert s.next_after(date(2026, 10, 2)).effective_from == "2027-01-01"


def test_a_day_before_the_first_entry_is_an_error_not_free():
    s = PriceSchedule.parse("2026-09-30:0.75/3.75")
    with pytest.raises(ValueError, match="2026-09-30"):
        s.at(date(2026, 9, 1))


def test_empty_schedule_is_free_and_undated_price_always_applies():
    assert PriceSchedule().at() == Price.free()
    assert PriceSchedule.single(Price(1.0, 2.0)).at(date(2000, 1, 1)).input_per_million == 1.0

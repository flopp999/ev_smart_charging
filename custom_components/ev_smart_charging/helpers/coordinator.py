"""Helpers for coordinator"""

from datetime import datetime, timedelta
import logging
from math import ceil
from homeassistant.util import dt

_LOGGER = logging.getLogger(__name__)


class Raw:
    """Class to handle raw data

    Array of item = {
        "start": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "end": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "value": float,
    }"""

    def __init__(self, raw) -> None:

        self.data = []
        for item in raw:
            if item["value"] is not None:
                self.data.append(item)
        self.valid = len(self.data) > 0

    def get_raw(self):
        """Get raw data"""
        return self.data

    def is_valid(self) -> bool:
        """Get valid"""
        return self.valid

    def copy(self):
        """Get a copy of Raw"""
        return Raw(self.data)

    def extend(self, raw2):
        """Extend raw data with data from raw2."""
        if self.valid and raw2.is_valid():
            self.data.extend(raw2.get_raw())

    def max_value(self) -> float:
        """Return the largest value"""
        largest = None
        for item in self.data:
            if largest is None:
                largest = item["value"]
                continue
            if item["value"] > largest:
                largest = item["value"]
        return largest

    def get_value(self, time: datetime) -> float:
        """Get the value at time dt"""
        for item in self.data:
            if item["start"] <= time < item["end"]:
                return item["value"]
        return None


def get_lowest_hours(ready_hour: int, raw_two_days: Raw, hours: int):
    """From the two-day prices, calculate the cheapest hours

    A continues range of hours will be choosen."""
    # TODO: Make this work with daylight saving time

    _LOGGER.debug("ready_hour = %s", ready_hour)

    if hours == 0:
        return []

    price = []
    for item in raw_two_days.get_raw():
        price.append(item["value"])
    lowest_index = None
    lowest_price = None
    time_now = dt.now()
    time_end = dt.now().replace(
        hour=ready_hour, minute=0, second=0, microsecond=0
    ) + timedelta(days=1)
    time_now_index = None
    time_end_index = None
    for index in range(len(price)):
        item = raw_two_days.get_raw()[index]
        if item["end"] > time_now and time_now_index is None:
            time_now_index = index
        if item["start"] < time_end:
            time_end_index = index

    if (time_end_index - time_now_index) < hours:
        return list(range(time_now_index, time_end_index + 1))

    for index in range(time_now_index, time_end_index - hours + 2):
        if lowest_index is None:
            lowest_index = index
            lowest_price = sum(price[index : (index + hours)])
            continue
        new_price = sum(price[index : (index + hours)])
        if new_price < lowest_price:
            lowest_index = index
            lowest_price = new_price

    res = list(range(lowest_index, lowest_index + hours))
    return res


def get_charging_initial() -> list:
    """Create initial charging information"""

    start_time = dt.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)
    result = []
    for hour in range(48):  # pylint: disable=unused-variable
        item = {
            "start": start_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "end": end_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "value": 0.0,
        }
        result.append(item)
        start_time = start_time + timedelta(hours=1)
        end_time = end_time + timedelta(hours=1)

    return result


def get_charging_original(lowest_hours: list[int], raw_two_days: Raw) -> list:
    """Calculate charging information"""

    start_time = dt.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)
    result = []
    for hour in range(48):
        value = 0
        if hour in lowest_hours:
            value = raw_two_days.get_value(start_time)
        item = {
            "start": start_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "end": end_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "value": value,
        }
        result.append(item)
        start_time = start_time + timedelta(hours=1)
        end_time = end_time + timedelta(hours=1)

    return result


def get_charging_update(
    charging_original: list, active: bool, ignore_limit: bool, max_price: float
):
    """Update the charging schedule"""

    if max_price is not None and max_price > 0.0:
        value_on = max_price
    else:
        value_on = Raw(charging_original).max_value()

    result = []
    for item in charging_original:
        if item["value"] == 0.0:
            pass
        elif not active:
            item["value"] = 0.0
        elif not ignore_limit and item["value"] > max_price:
            item["value"] = 0.0
        else:
            item["value"] = value_on
        result.append(item)

    return result


def get_charging_hours(
    ev_soc: float, ev_target_soc: float, charing_pct_per_hour: float
):
    """Calculate the number of charging hours"""
    charging_hours = ceil(
        min(max(((ev_target_soc - ev_soc) / charing_pct_per_hour), 0), 24)
    )
    return charging_hours


def get_charging_value(charging):
    """Get value for charging now"""
    time_now = dt.now()
    for item in charging:
        if (
            datetime.strptime(item["start"], "%Y-%m-%dT%H:%M:%S%z")
            <= time_now
            < datetime.strptime(item["end"], "%Y-%m-%dT%H:%M:%S%z")
        ):
            return item["value"]
    return None


def main():
    """Main function to test code."""

    result = []
    value = [1, 4, 6, 6, 5, 3, 2, 2, 4, 4]
    start_time = dt.now().replace(minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)
    for nnnn in range(10):
        item = {
            "start": start_time,
            "end": end_time,
            "value": value[nnnn],
        }
        result.append(item)
    raw2 = Raw(result)
    print("r2.raw = " + str(raw2.get_raw()))
    lowest = get_lowest_hours(start_time.hour, raw2, 3)
    print("lowest = " + str(lowest))


if __name__ == "__main__":
    main()
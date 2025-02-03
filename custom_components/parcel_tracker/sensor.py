import logging
from homeassistant.components.sensor import SensorEntity
import aiohttp
import asyncio
import json
from datetime import datetime
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CARRIER_MAP = {
    "amzluk": "Amazon",
    "ups": "UPS",
    "dpdie": "DPD Ireland",
    "anpost": "An Post",
    "sypo": "Synergy",
    "fedex": "FedEx"
}

class ParcelTrackerSensor(SensorEntity):
    """Sensor to track parcel information."""

    def __init__(self, config):
        self._name = "Parcel Tracker 📦"
        self._url = config["url"]
        self._token = config["token"]
        self._state = "Initializing"
        self._data = []
        self._attr_unique_id = f"parcel_tracker_{self._token}"
        self._attr_icon = "mdi:package-variant-closed"

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def state(self):
        """Return the number of pending deliveries."""
        pending_deliveries = sum(1 for order in self._data if order["status"].lower() != "delivered")
        return f"{pending_deliveries} pending deliveries"

    @property
    def extra_state_attributes(self):
        """Return the extra attributes with detailed parcel data."""
        return {"orders": self._data}

    async def async_update(self):
        """Fetch the latest data from the API."""
        headers = {
            "Cookie": f"account_token={self._token}",
            "User-Agent": "Home Assistant Custom Component",
            "Accept-Encoding": "gzip, deflate, br"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self._url, headers=headers) as response:
                    response.raise_for_status()
                    raw_data = await response.text()

                    if raw_data.startswith("jQuery"):
                        json_start = raw_data.find("(") + 1
                        json_end = raw_data.rfind(")")
                        raw_data = raw_data[json_start:json_end]

                    try:
                        data = json.loads(raw_data)
                        if not isinstance(data, list) or not data[0]:
                            _LOGGER.error("Unexpected API response format")
                            self._state = "Invalid Data"
                            return
                    except json.JSONDecodeError as e:
                        _LOGGER.error(f"Failed to parse JSON: {e}")
                        self._state = "Data Error"
                        return

                    self._data = []
                    today = datetime.now()

                    for order in data[0]:
                        number = order[0]
                        name = order[1]
                        carrier = CARRIER_MAP.get(order[2], order[2])
                        status = order[4][0][0] if order[4] else "Unknown"
                        delivery_date = order[5]

                        if "delivered" in status.lower():
                            status_label = "Delivered"
                        else:
                            status_label = "Unknown"

                        if delivery_date and status_label != "Delivered":
                            try:
                                delivery_date_obj = datetime.strptime(delivery_date, "%Y-%m-%d %H:%M:%S")
                                days_until = (delivery_date_obj.date() - today.date()).days
                                
                                if days_until > 0:
                                    day_label = "day" if days_until == 1 else "days"
                                    status_label = f"{days_until} {day_label}"
                            except ValueError:
                                _LOGGER.warning(f"Invalid date format for order {number} ({name}): {delivery_date}")

                        self._data.append({
                            "number": number,
                            "name": name,
                            "carrier": carrier,
                            "status": status_label
                        })

        except aiohttp.ClientError as e:
            _LOGGER.error(f"Network error fetching data: {e}")
            self._state = "Network Error"
        except Exception as e:
            _LOGGER.exception(f"Unexpected error: {e}")
            self._state = "Unknown Error"

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform."""
    config = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ParcelTrackerSensor(config)], True)

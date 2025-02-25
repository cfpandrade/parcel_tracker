import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import aiohttp
import asyncio
import json
from datetime import datetime
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STATUS_MAP = {
    0: "Delivered",
    1: "Frozen",
    2: "In Transit",
    3: "Awaiting Pickup",
    4: "Out for Delivery",
    5: "Not Found",
    6: "Failed Attempt",
    7: "Delivery Exception",
    8: "Info Received"
}

class ParcelTrackerSensor(SensorEntity):
    """Sensor to track parcel information."""

    def __init__(self, config):
        self._name = "Parcel Tracker 📦"
        self._api_key = config["api_key"]
        self._state = "Initializing"
        self._data = []
        self._attr_unique_id = f"parcel_tracker_{self._api_key}"  # Unique ID based on API key
        self._attr_icon = "mdi:package-variant-closed"  # Home Assistant package icon

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID for this sensor."""
        return self._attr_unique_id

    @property
    def state(self):
        return self._state  # Could be "Updated" or an error message

    @property
    def extra_state_attributes(self):
        """Return the extra attributes with only relevant parcel data."""
        return {"deliveries": self._data}

    async def async_update(self):
        """Fetch the latest data from the API."""
        headers = {
            "api-key": self._api_key,
            "User-Agent": "Home Assistant Custom Component",
            "Accept-Encoding": "gzip, deflate, br"
        }

        params = {
            "filter_mode": "active"  # Or "recent", depending on your needs
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.parcel.app/external/deliveries/", headers=headers, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()

                    if not data.get("success", False):
                        _LOGGER.error(f"API error: {data.get('error_message', 'No error message provided')}")
                        self._state = "API Error"
                        return

                    self._data = []
                    for delivery in data.get("deliveries", []):
                        tracking_number = delivery.get("tracking_number")
                        description = delivery.get("description")
                        carrier_code = delivery.get("carrier_code")
                        status_code = delivery.get("status_code")
                        status = STATUS_MAP.get(status_code, "Unknown Status")
                        date_expected = delivery.get("date_expected")

                        self._data.append({
                            "tracking_number": tracking_number,
                            "description": description,
                            "carrier": carrier_code,
                            "status": status,
                            "date_expected": date_expected
                        })

                    self._state = "Updated"
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Network error fetching data: {e}")
            self._state = "Network Error"
        except Exception as e:
            _LOGGER.exception(f"Unexpected error: {e}")
            self._state = "Unknown Error"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Parcel Tracker sensor platform from a config entry."""
    config = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ParcelTrackerSensor(config)], True)

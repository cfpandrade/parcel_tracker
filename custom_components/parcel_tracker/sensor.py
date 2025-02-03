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
        return self._state  

    @property
    def extra_state_attributes(self):
        return {"orders": self._data}

    async def async_update(self):
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

                        days_until_delivery = "Delivered" if "delivered" in status.lower() else "Unknown"

                        if delivery_date and days_until_delivery != "Delivered":
                            try:
                                delivery_date_obj = datetime.strptime(delivery_date, "%Y-%m-%d %H:%M:%S")
                                days_until = (delivery_date_obj.date() - today.date()).days
                                
                                if days_until > 0:
                                    day_label = "day" if days_until == 1 else "days"
                                    days_until_delivery = f"{days_until} {day_label}"
                            except ValueError:
                                _LOGGER.warning(f"Invalid date format for order {number} ({name}): {delivery_date}")

                        self._data.append({
                            "number": number,
                            "name": name,
                            "carrier": carrier,
                            "status": days_until_delivery
                        })

                    self._state = "Updated"
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Network error fetching data: {e}")
            self._state = "Network Error"
        except Exception as e:
            _LOGGER.exception(f"Unexpected error: {e}")
            self._state = "Unknown Error"


class ParcelTrackerStatusSensor(SensorEntity):
    """Sensor to count pending parcel deliveries."""

    def __init__(self, tracker_sensor):
        self._name = "Parcel Tracker Status 📦"
        self._tracker_sensor = tracker_sensor
        self._state = None
        self._attr_unique_id = f"{tracker_sensor.unique_id}_status"
        self._attr_icon = "mdi:truck-delivery"

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def state(self):
        return self._state

    async def async_update(self):
        if not self._tracker_sensor.extra_state_attributes:
            return
        
        orders = self._tracker_sensor.extra_state_attributes.get("orders", [])
        pending_deliveries = sum(1 for order in orders if order["status"] not in ["Delivered", "Unknown"])

        self._state = f"{pending_deliveries} pending deliveries"

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform."""
    config = hass.data[DOMAIN][entry.entry_id]
    tracker_sensor = ParcelTrackerSensor(config)
    status_sensor = ParcelTrackerStatusSensor(tracker_sensor)
    
    async_add_entities([tracker_sensor, status_sensor], True)

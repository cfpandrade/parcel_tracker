import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import aiohttp
from datetime import timedelta
from homeassistant.helpers.event import async_track_time_interval
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
        self._attr_unique_id = f"parcel_tracker_{self._api_key}"
        self._attr_icon = "mdi:package-variant-closed"

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID for this sensor."""
        return self._attr_unique_id

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        """Return extra attributes with parcel data including events."""
        return {"deliveries": self._data}

    @property
    def should_poll(self):
        """Disable automatic polling; updates are scheduled manually."""
        return False

    async def async_update(self, now=None):
        """Fetch the latest data from the API."""
        headers = {
            "api-key": self._api_key,
            "User-Agent": "Home Assistant Custom Component"
        }

        params = {
            "filter_mode": "active"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.parcel.app/external/deliveries/",
                    headers=headers,
                    params=params
                ) as response:
                    response.raise_for_status()
                    # Force JSON decoding even if the content type is not application/json
                    data = await response.json(content_type=None)

                    if not data.get("success", False):
                        _LOGGER.error("API error: %s", data.get("error_message", "No error message provided"))
                        self._state = "API Error"
                        return

                    # Process deliveries
                    self._data = []
                    for delivery in data.get("deliveries", []):
                        tracking_number = delivery.get("tracking_number")
                        description = delivery.get("description")
                        carrier_code = delivery.get("carrier_code")
                        status_code = delivery.get("status_code")
                        status = STATUS_MAP.get(status_code, "Unknown Status")
                        date_expected = delivery.get("date_expected")
                        extra_information = delivery.get("extra_information")
                        
                        # Include events history
                        events = delivery.get("events", [])
                        
                        # Get the latest event for simple display
                        latest_event = events[0].get("event") if events else "No events"
                        latest_date = events[0].get("date") if events else ""
                        latest_location = events[0].get("location", "") if events else ""
                        
                        delivery_data = {
                            "tracking_number": tracking_number,
                            "description": description,
                            "carrier": carrier_code,
                            "status": status,
                            "latest_event": latest_event,
                            "latest_date": latest_date,
                            "events": events  # Include all tracking events
                        }
                        
                        # Add optional fields if they exist
                        if date_expected:
                            delivery_data["date_expected"] = date_expected
                        if extra_information:
                            delivery_data["extra_information"] = extra_information
                        if latest_location:
                            delivery_data["latest_location"] = latest_location
                            
                        self._data.append(delivery_data)

                    # Update the sensor's main state with the count of active deliveries
                    self._state = f"{len(self._data)} Active"
                    
        except aiohttp.ClientError as e:
            _LOGGER.error("Network error fetching data: %s", e)
            self._state = "Network Error"
        except Exception as e:
            _LOGGER.exception("Unexpected error: %s", e)
            self._state = "Unknown Error"

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Parcel Tracker sensor platform from a config entry."""
    config = hass.data[DOMAIN][entry.entry_id]
    sensor = ParcelTrackerSensor(config)
    async_add_entities([sensor], True)

    # Trigger an initial update so that the entity shows current data promptly.
    hass.async_create_task(sensor.async_update())

    # Get the scan_interval (in minutes) from the configuration, defaulting to 20 minutes.
    scan_interval = int(config.get("scan_interval", 20))
    async_track_time_interval(hass, sensor.async_update, timedelta(minutes=scan_interval))

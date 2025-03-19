import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import aiohttp
from datetime import timedelta
import random
import math
import asyncio
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
        # Backoff settings
        self._retry_count = 0
        self._max_retries = 5
        self._base_wait_time = 60  # Base wait time in seconds
        self._last_successful_update = None

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
        attributes = {
            "deliveries": self._data
        }
        if self._last_successful_update:
            attributes["last_successful_update"] = self._last_successful_update
        if self._retry_count > 0:
            attributes["rate_limit_retries"] = self._retry_count
        return attributes

    @property
    def should_poll(self):
        """Disable automatic polling; updates are scheduled manually."""
        return False
    
    def _calculate_backoff_time(self):
        """Calculate exponential backoff time with jitter."""
        # Calculate base exponential backoff
        backoff = min(600, self._base_wait_time * (2 ** self._retry_count))  # Max 10 minutes
        # Add random jitter (±25%)
        jitter = random.uniform(-0.25 * backoff, 0.25 * backoff)
        return max(60, math.floor(backoff + jitter))  # Ensure at least 60 seconds
    
    async def _handle_rate_limit(self):
        """Handle rate limiting by implementing exponential backoff."""
        if self._retry_count < self._max_retries:
            self._retry_count += 1
            wait_time = self._calculate_backoff_time()
            
            _LOGGER.warning(
                "Rate limited by API (429). Retry %d/%d after %d seconds.", 
                self._retry_count, self._max_retries, wait_time
            )
            
            self._state = f"Rate limited (retry {self._retry_count}/{self._max_retries})"
            self.async_write_ha_state()
            
            # Schedule a retry after the backoff period
            await asyncio.sleep(wait_time)
            return True
        else:
            _LOGGER.error(
                "Maximum retries reached (%d) after rate limit errors. Will try again on next scheduled update.",
                self._max_retries
            )
            self._state = "Rate limit exceeded"
            self._retry_count = 0  # Reset for next regular update
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
                    # Check for rate limiting
                    if response.status == 429:
                        _LOGGER.warning("Received 429 Too Many Requests from API")
                        retry_after = response.headers.get('Retry-After')
                        
                        if retry_after:
                            try:
                                # If Retry-After header is present, use that value
                                wait_seconds = int(retry_after)
                                _LOGGER.info("API provided Retry-After: %d seconds", wait_seconds)
                                await asyncio.sleep(wait_seconds)
                                # Try once more immediately after waiting
                                return await self.async_update()
                            except (ValueError, TypeError):
                                pass  # If we can't parse Retry-After, use our backoff mechanism
                        
                        # Use our exponential backoff mechanism
                        should_retry = await self._handle_rate_limit()
                        if should_retry:
                            return await self.async_update()
                        return
                    
                    # Reset retry count on successful status
                    if response.status == 200:
                        if self._retry_count > 0:
                            _LOGGER.info("API request successful after %d retries", self._retry_count)
                        self._retry_count = 0
                    
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
                    self._last_successful_update = now.isoformat() if now else None
                    
                    # Log successful update
                    _LOGGER.debug("Successfully updated Parcel Tracker data: %d active deliveries", len(self._data))
                    
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
    # Combine data and options for the sensor
    config = {**entry.data}
    if entry.options:
        config.update(entry.options)
    
    _LOGGER.debug("Setting up Parcel Tracker with scan_interval: %s minutes", 
                 config.get("scan_interval", 20))
    
    sensor = ParcelTrackerSensor(config)
    async_add_entities([sensor], True)

    # Trigger an initial update so that the entity shows current data promptly
    await sensor.async_update()

    # Get the scan_interval (in minutes) from the configuration, defaulting to 20 minutes
    scan_interval = int(config.get("scan_interval", 20))
    
    # Store the cancel function so we can clean it up on unload
    cancel_interval = async_track_time_interval(
        hass, sensor.async_update, timedelta(minutes=scan_interval)
    )
    
    # Make sure we have the structure to store cancel functions
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if "unsub_interval" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["unsub_interval"] = {}
    
    # Store the cancel function in hass.data so we can cancel it later
    hass.data[DOMAIN]["unsub_interval"][entry.entry_id] = cancel_interval
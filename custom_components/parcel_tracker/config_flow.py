import voluptuous as vol
from homeassistant import config_entries
import logging
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class ParcelTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Parcel Tracker."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        # The schema now enforces scan_interval between 10 and 60 minutes.
        data_schema = vol.Schema({
            vol.Required("api_key"): str,
            vol.Required("scan_interval", default=20): vol.All(vol.Coerce(int), vol.Range(min=10, max=60)),
        })

        if user_input is not None:
            api_key = user_input.get("api_key")

            if not api_key:
                errors["api_key"] = "API key is required"
            else:
                # Verify the API key by making a test request.
                valid = await self._test_api_key(api_key)
                if not valid:
                    errors["api_key"] = "Invalid API key"

            if errors:
                # Re-show the form with error messages if needed.
                return self.async_show_form(
                    step_id="user",
                    data_schema=data_schema,
                    errors=errors,
                    description_placeholders={
                        "api_info": "Enter your Parcel.app API key and update interval (in minutes, between 10 and 60)."
                    }
                )
            return self.async_create_entry(title="Parcel Tracker", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "api_info": "Enter your Parcel.app API key and update interval (in minutes, between 10 and 60). 20 minutes is recommended."
            }
        )
    
    async def _test_api_key(self, api_key):
        """Test if the API key is valid by making a request to the ParcelTracker API."""
        headers = {
            "api-key": api_key,
            "User-Agent": "Home Assistant Custom Component"
        }
        
        params = {
            "filter_mode": "active"
        }
        
        session = async_get_clientsession(self.hass)
        
        try:
            async with session.get(
                "https://api.parcel.app/external/deliveries/",
                headers=headers,
                params=params
            ) as response:
                if response.status != 200:
                    _LOGGER.error("ParcelTracker API returned non-200 status: %s", response.status)
                    return False
                
                # Force JSON decoding even if the content type isn't application/json.
                data = await response.json(content_type=None)
                if not data.get("success", False):
                    _LOGGER.error("API response indicates failure: %s", data)
                return data.get("success", False)
                    
        except Exception as e:
            _LOGGER.exception("Error testing ParcelTracker API key: %s", e)
            return False

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ParcelTrackerOptionsFlow(config_entry)

class ParcelTrackerOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Parcel Tracker."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options for the integration."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Retrieve the current scan_interval from options or data, defaulting to 20 minutes.
        current_scan_interval = self.config_entry.options.get(
            "scan_interval", self.config_entry.data.get("scan_interval", 20)
        )

        data_schema = vol.Schema({
            vol.Required("scan_interval", default=current_scan_interval): vol.All(vol.Coerce(int), vol.Range(min=10, max=60)),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            description_placeholders={
                "info": "Set the update interval in minutes (between 10 and 60). 20 minutes is recommended."
            }
        )

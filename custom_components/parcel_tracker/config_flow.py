import voluptuous as vol
from homeassistant import config_entries
import aiohttp
import logging
from homeassistant.core import callback
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class ParcelTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Parcel Tracker."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            api_key = user_input.get("api_key")
            
            if not api_key:
                errors["api_key"] = "API key is required"
            else:
                # Verify the API key is valid by making a test request
                valid = await self._test_api_key(api_key)
                if not valid:
                    errors["api_key"] = "Invalid API key"
            
            if not errors:
                return self.async_create_entry(title="Parcel Tracker", data=user_input)

        data_schema = vol.Schema({
            vol.Required("api_key"): str,
        })

        return self.async_show_form(
            step_id="user", 
            data_schema=data_schema, 
            errors=errors,
            description_placeholders={
                "api_info": "Enter your Parcel.app API key. You can find it in your account settings."
            }
        )
    
    async def _test_api_key(self, api_key):
        """Test if the API key is valid."""
        headers = {
            "api-key": api_key,
            "User-Agent": "Home Assistant Custom Component"
        }
        
        params = {
            "filter_mode": "active"
        }
        
        try:
            async with aiohttp.ClientSession(compress=True) as session:
                async with session.get(
                    "https://api.parcel.app/external/deliveries/",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status != 200:
                        _LOGGER.error("ParcelTracker API returned non-200 status: %s", response.status)
                        return False
                    
                    data = await response.json()
                    if not data.get("success", False):
                        _LOGGER.error("ParcelTracker API response indicates failure: %s", data)
                    return data.get("success", False)
                    
        except Exception as e:
            _LOGGER.exception("Error testing ParcelTracker API key: %s", e)
            return False
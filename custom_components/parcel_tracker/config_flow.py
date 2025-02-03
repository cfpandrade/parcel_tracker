import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN
import aiohttp

class ParcelTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Parcel Tracker."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            url = user_input.get("url")
            token = user_input.get("token")
            
            if not url.startswith("https://"):
                errors["url"] = "Invalid URL"
            elif not token:
                errors["token"] = "Token is required"
            
            if not errors:
                return self.async_create_entry(title="Parcel Tracker", data=user_input)

        data_schema = vol.Schema({
            vol.Required("url"): str,
            vol.Required("token"): str,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

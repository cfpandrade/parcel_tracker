import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class ParcelTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Maneja el flujo de configuración para Parcel Tracker."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Maneja el paso inicial."""
        errors = {}
        if user_input is not None:
            api_key = user_input.get("api_key")
            
            if not api_key:
                errors["api_key"] = "Se requiere la clave API"
            
            if not errors:
                return self.async_create_entry(title="Parcel Tracker", data=user_input)

        data_schema = vol.Schema({
            vol.Required("api_key"): str,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
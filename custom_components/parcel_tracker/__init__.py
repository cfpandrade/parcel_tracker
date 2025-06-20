import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Parcel Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data
    
    # Forward the setup to the sensor platform.
    # CORRECCIÓN: Usar await aquí para esperar a que se complete la configuración
    await hass.config_entries.async_forward_entry_setup(entry, "sensor")
    
    # Listen for options updates so we can reload when the scan_interval is changed.
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    # Cancel the update timer if it exists
    if DOMAIN in hass.data and "unsub_interval" in hass.data[DOMAIN] and entry.entry_id in hass.data[DOMAIN]["unsub_interval"]:
        cancel = hass.data[DOMAIN]["unsub_interval"].pop(entry.entry_id)
        cancel()
    
    # Unload the sensor platform
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    
    # Remove entry data
    if entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update by reloading the integration."""
    _LOGGER.debug("Reloading Parcel Tracker configuration due to options update")
    await hass.config_entries.async_reload(entry.entry_id)

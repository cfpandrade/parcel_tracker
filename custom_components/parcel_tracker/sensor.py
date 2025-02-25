import logging
from homeassistant.components.sensor import SensorEntity
import aiohttp
import asyncio
import json
from datetime import datetime
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STATUS_MAP = {
    0: "Entregado",
    1: "Congelado",
    2: "En tránsito",
    3: "Esperando recogida",
    4: "En camino para entrega",
    5: "No encontrado",
    6: "Intento de entrega fallido",
    7: "Excepción en la entrega",
    8: "Información recibida por el transportista"
}

class ParcelTrackerSensor(SensorEntity):
    """Sensor para rastrear información de paquetes."""

    def __init__(self, config):
        self._name = "Parcel Tracker 📦"
        self._api_key = config["api_key"]
        self._state = "Inicializando"
        self._data = []
        self._attr_unique_id = f"parcel_tracker_{self._api_key}"  # ID único basado en la clave API
        self._attr_icon = "mdi:package-variant-closed"  # Icono de paquete de HA

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        """Devuelve un ID único para este sensor."""
        return self._attr_unique_id

    @property
    def state(self):
        return self._state  # Podría ser "Actualizado" o un mensaje de error

    @property
    def extra_state_attributes(self):
        """Devuelve los atributos adicionales con solo los datos relevantes del paquete."""
        return {"deliveries": self._data}

    async def async_update(self):
        """Obtiene los datos más recientes de la API."""
        headers = {
            "api-key": self._api_key,
            "User-Agent": "Home Assistant Custom Component",
            "Accept-Encoding": "gzip, deflate, br"
        }

        params = {
            "filter_mode": "active"  # O "recent", según tus necesidades
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.parcel.app/external/deliveries/", headers=headers, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()

                    if not data.get("success", False):
                        _LOGGER.error(f"Error en la API: {data.get('error_message', 'Mensaje de error no proporcionado')}")
                        self._state = "Error en la API"
                        return

                    self._data = []
                    for delivery in data.get("deliveries", []):
                        tracking_number = delivery.get("tracking_number")
                        description = delivery.get("description")
                        carrier_code = delivery.get("carrier_code")
                        status_code = delivery.get("status_code")
                        status = STATUS_MAP.get(status_code, "Estado desconocido")
                        date_expected = delivery.get("date_expected")

                        self._data.append({
                            "tracking_number": tracking_number,
                            "description": description,
                            "carrier": carrier_code,
                            "status": status,
                            "date_expected": date_expected
                        })

                    self._state = "Actualizado"
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error de red al obtener datos: {e}")
            self._state = "Error de red"
        except Exception as e:
            _LOGGER.exception(f"Error inesperado: {e}")
            self._state = "Error desconocido"
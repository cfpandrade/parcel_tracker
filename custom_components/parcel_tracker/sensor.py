import logging
from homeassistant.components.sensor import SensorEntity
import aiohttp
import json
from datetime import datetime, timedelta
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CARRIER_MAP = {
    "amzluk": "Amazon"
}

class ParcelTrackerSensor(SensorEntity):
    """Sensor para rastrear información de paquetes."""

    def __init__(self, config):
        self._name = "Parcel Tracker 📦"
        self._url = config["url"]
        self._token = config["token"]
        self._state = "Inicializando"
        self._data = []
        self._attr_unique_id = f"parcel_tracker_{self._token}"  # ID único basado en el token
        self._attr_icon = "mdi:package-variant-closed"  # Icono de paquete de Home Assistant

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        """Devuelve un ID único para este sensor."""
        return self._attr_unique_id

    @property
    def state(self):
        """Devuelve el estado del sensor."""
        # Contar la cantidad de paquetes en tránsito
        in_transit_count = sum(1 for order in self._data if order["status"] not in ["Entregado", "Desconocido"])
        return f"{in_transit_count} paquetes en tránsito"

    @property
    def extra_state_attributes(self):
        """Devuelve los atributos adicionales con solo los datos relevantes de los paquetes."""
        return {"orders": self._data}

    async def async_update(self):
        """Obtiene los datos más recientes de la API."""
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

                    # Detectar JSONP y limpiarlo
                    if raw_data.startswith("jQuery"):
                        json_start = raw_data.find("(") + 1
                        json_end = raw_data.rfind(")")
                        raw_data = raw_data[json_start:json_end]

                    try:
                        data = json.loads(raw_data)  # Convertir a JSON estructurado
                        if not isinstance(data, list) or not data[0]:
                            _LOGGER.error("Formato de respuesta de API inesperado")
                            self._state = "Datos inválidos"
                            return
                    except json.JSONDecodeError as e:
                        _LOGGER.error(f"Error al analizar JSON: {e}")
                        self._state = "Error de datos"
                        return

                    # Extraer solo los datos necesarios
                    self._data = []
                    today = datetime.now()

                    for order in data[0]:
                        number = order[0]
                        name = order[1]
                        carrier = CARRIER_MAP.get(order[2], order[2])
                        status = order[4][0][0] if order[4] else "Desconocido"
                        delivery_date = order[5]
                        
                        days_until_delivery = "Entregado" if "delivered" in status.lower() else "Desconocido"
                        
                        if delivery_date and days_until_delivery != "Entregado":
                            try:
                                delivery_date_obj = datetime.strptime(delivery_date, "%Y-%m-%d %H:%M:%S")
                                days_until = (delivery_date_obj - today).days
                                if days_until > 0:
                                    days_until_delivery = f"{days_until} días"
                            except ValueError:
                                _LOGGER.warning(f"Formato de fecha inválido: {delivery_date}")

                        self._data.append({
                            "number": number,
                            "name": name,
                            "carrier": carrier,
                            "status": days_until_delivery
                        })

                    self._state = "Actualizado"
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error de red al obtener datos: {e}")
            self._state = "Error de red"
        except Exception as e:
            _LOGGER.exception(f"Error inesperado: {e}")
            self._state = "Error desconocido"

"""
Adax heaters - https://adax.no/
Open API: https://adax.no/om-adax/api-development/
"""
import logging
import aiohttp
import json
import voluptuous as vol
from datetime import timedelta
import requests
import math

from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.exceptions import PlatformNotReady
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
)

_LOGGER = logging.getLogger(__name__)

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
    API_URL,
    DATA_ADAX,
)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=10)

async def async_setup(hass, config):
    """Set up the Adax platform."""
    return True


async def async_setup_entry(hass, entry):
    """Set up the Adax heater."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    adax_data = AdaxHub(username, password)
    await adax_data.async_update()
    hass.data[DATA_ADAX] = adax_data

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "climate")
    )
    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(
        config_entry, "climate"
    )
    return unload_ok




class AdaxHub(object):

    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._heaters = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        data = {'username': self._username,
                'password': self._password,
                'grant_type': 'password'}

        ACCESS_TOKEN_URL = API_URL + '/auth/token'

        async with aiohttp.ClientSession() as session:
            async with session.post(ACCESS_TOKEN_URL, data=data) as response:

                if response.status != 200:
                    _LOGGER.info("Adax: Failed to update information: %d", response.status)
                    return False
                res = await response.text()
                _LOGGER.debug("Adax: Response token: %s", res)
                res2 = json.loads(res)
                token = res2['access_token']

            headers = { "Authorization": "Bearer " + token }
            async with session.get(API_URL + "/rest/v1/content/", headers = headers) as response:
                output = await response.json()
                self._heaters = output['rooms']

        return True

    async def set_update(self, id, type, info, info2):

        for room in self._heaters:
            if room['id'] == id:
                if type == "hvac":
                    room['heatingEnabled'] = info
                    room['targetTemperature'] = info2
                elif type == "settemp":
                    room['targetTemperature'] = info2

    @property
    def target(self):

        info = {}
        for room in self._heaters:
            if room['heatingEnabled'] == True:
                #item = {room['id']: str(int(room['targetTemperature'] / 100.0))}
                info[room['id']] = int(room['targetTemperature'] / 100.0)
        return info

    @property
    def temperature(self):
        info = {
                room['id']: float(room['temperature'] / 100.0)
                for room in self._heaters
                }
        return info

    @property
    def hvac(self):
        info = {
                room['id']: room['heatingEnabled']
                for room in self._heaters
                }
        return info

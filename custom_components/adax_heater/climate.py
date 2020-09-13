"""Support for Adax wifi-enabled heaters."""
import logging

import voluptuous as vol
from datetime import timedelta
import aiohttp
import json
import math

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_PASSWORD,
    CONF_USERNAME,
    TEMP_CELSIUS,
)
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

import custom_components.adax_heater as adax_heater

from .const import (
    ATTR_ROOM_TEMP,
    ATTR_ROOM_NAME,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    MAX_TEMP,
    MIN_TEMP,
    SERVICE_SET_ROOM_TEMP,
    API_URL,
    DATA_ADAX,
)

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE

SET_ROOM_TEMP_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ROOM_NAME): cv.string,
        vol.Required(ATTR_ROOM_TEMP): cv.positive_int,
    }
)

SCAN_INTERVAL = timedelta(seconds=15)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Adax climate."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    data = {'username': username,
            'password': password,
            'grant_type': 'password'}

    ACCESS_TOKEN_URL = API_URL + '/auth/token'

    async with aiohttp.ClientSession() as session:
        async with session.post(ACCESS_TOKEN_URL, data=data) as response:

            if response.status != 200:
                _LOGGER.info("Adax: Failed to update information: %d", response.status)
                raise ConfigEntryNotReady
                return False
            res = await response.text()
            _LOGGER.debug("Adax: Response token: %s", res)
            res2 = json.loads(res)
            token = res2['access_token']

        headers = { "Authorization": "Bearer " + token }
        async with session.get(API_URL + "/rest/v1/content/", headers = headers) as response:
            if response.status != 200:
                _LOGGER.info("Adax: Failed to update information: %d", response.status)
                raise ConfigEntryNotReady
                return False
            res = await response.json()

    adax_hub = hass.data[adax_heater.DATA_ADAX]

    dev = []
    for heater in res['rooms']:
        dev.append(AdaxHeater(heater, username, password, adax_hub))
    async_add_entities(dev)

    """SAVED FOR LATER USAGE WHEN POSSIBLE THROUGH API
    async def set_room_temp(service):
        #Set room temp.
        room_name = service.data.get(ATTR_ROOM_NAME)
        room_temp = service.data.get(ATTR_ROOM_TEMP)

        data = {'username': username,
                'password': password,
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
                if response.status != 200:
                    _LOGGER.info("Adax: Failed to update information: %d", response.status)
                    return False
                res = await response.json()

            for room in res['rooms']:
                if room_name == room['name']:
                    headers = { "Authorization": "Bearer " + token }
                    if room_temp == 0:
                        jsontext = { 'rooms': [{ 'id': room['id'], 'heatingEnabled': False }] }
                    else:
                        jsontext = { 'rooms': [{ 'id': room['id'], 'heatingEnabled': True, 'targetTemperature': str(int(room_temp*100.0)) }] }
                    _LOGGER.debug("Adax: Set temp json: %s", jsontext)
                    async with session.post(API_URL + "/rest/v1/control/", json = jsontext, headers = headers) as response:
                        return True


    hass.services.async_register(
        DOMAIN, SERVICE_SET_ROOM_TEMP, set_room_temp, schema=SET_ROOM_TEMP_SCHEMA
    )
    """

class AdaxHeater(ClimateEntity):
    """Representation of a Adax Thermostat device."""

    def __init__(self, heater, username, password, hub):
        """Initialize the thermostat."""
        self._hub = hub
        self._heater = heater
        self._settemp = 0.0
        self._username = username
        self._password = password
        self._hvac = False

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def available(self):
        """Return True if entity is available."""
        return True

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._heater['id']

    @property
    def name(self):
        """Return the name of the entity."""
        return "Adax " + str(self._heater['name'])

    @property
    def device_state_attributes(self):
        """Return the state attributes."""

        heating = self._hvac
        res = {
            "heating": heating,
            "room": self._heater['name'],
            "id": self._heater['id']
        }
        return res

    @property
    def temperature_unit(self):
        """Return the unit of measurement which this thermostat uses."""
        return TEMP_CELSIUS

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._settemp

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return 1

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._hub.temperature[self._heater['id']]

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return MIN_TEMP

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return MAX_TEMP

    @property
    def hvac_action(self):
        """Return current hvac i.e. heat, cool, idle.
        if self._hub.hvac[self._heater['id']] == True:
            return CURRENT_HVAC_HEAT
        return CURRENT_HVAC_IDLE
        """
        if self._hvac == True:
            return CURRENT_HVAC_HEAT
        return CURRENT_HVAC_IDLE

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode.

        Need to be one of HVAC_MODE_*.

        if self._hub.hvac[self._heater['id']] == True:
            return HVAC_MODE_HEAT
        return HVAC_MODE_OFF
        """
        if self._hvac == True:
            return HVAC_MODE_HEAT
        return HVAC_MODE_OFF

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes.

        Need to be a subset of HVAC_MODES.
        """
        return [HVAC_MODE_HEAT, HVAC_MODE_OFF]

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        newtemp = str(int(temperature * 100.0))
        self._settemp = newtemp

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
            jsontext = { 'rooms': [{ 'id': self.device_id, 'heatingEnabled': True, 'targetTemperature': str(newtemp) }] }
            _LOGGER.debug("Adax: Set temp json: %s", jsontext)
            async with session.post(API_URL + "/rest/v1/control/", json = jsontext, headers = headers) as response:
                self._hvac = True
                self._settemp = temperature
                await self._hub.set_update(self.device_id, "settemp", 0, self._settemp)
                return True

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""

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
            if self._settemp == 0.0:
                newtemp = int(math.ceil(self._heater['temperature']/100.0) * 100.0)
            else:
                newtemp = int(self._settemp * 100.0)
            _LOGGER.debug("Adax: newtemp = %s", newtemp)

            if hvac_mode == HVAC_MODE_HEAT:
                jsontext = { 'rooms': [{ 'id': self.device_id, 'heatingEnabled': True, 'targetTemperature': str(newtemp) }] }
                _LOGGER.debug("Adax: HEAT with json: %s", jsontext)
                async with session.post(API_URL + "/rest/v1/control/", json = jsontext, headers = headers) as response:
                    self._hvac = True
                    self._settemp = newtemp / 100.0
                    await self._hub.set_update(self.device_id, "hvac", True, int(newtemp/100.0))
                    _LOGGER.debug("Adax: hvac on: id %s hvac %s settemp %s", self.device_id, self._hvac, self._settemp)
                    return True

            elif hvac_mode == HVAC_MODE_OFF:
                jsontext = { 'rooms': [{ 'id': self.device_id, 'heatingEnabled': False }] }
                _LOGGER.debug("Adax: HEAT OFF with json: %s", jsontext)
                async with session.post(API_URL + "/rest/v1/control/", json = jsontext, headers = headers) as response:
                    self._hvac = False
                    await self._hub.set_update(self.device_id, "hvac", False, int(newtemp/100.0))
                    _LOGGER.debug("Adax: hvac off: id %s hvac %s", self.device_id, self._hvac)
                    return True


    async def async_update(self):
        """Retrieve latest state."""

        update = await self._hub.async_update()
        if self._hub.hvac[self._heater['id']] == True:
            _LOGGER.debug("Adax: Heater %s update hvac true, settemp = %s", self._heater['id'], self._hub.target[self._heater['id']])
            self._hvac = True
            self._settemp = self._hub.target[self._heater['id']]
        else:
            self._hvac = False

        return True

    @property
    def device_id(self):
        """Return the ID of the physical device this sensor is part of."""
        return self._heater['id']

    @property
    def device_info(self):
        """Return the device_info of the device."""
        device_info = {
            "identifiers": {(DOMAIN, self.device_id)},
            "name": self.name,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }
        return device_info

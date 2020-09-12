"""Support for Adax wifi-enabled heaters."""
import logging

import voluptuous as vol
from datetime import timedelta
import requests

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
)

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE

SET_ROOM_TEMP_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ROOM_NAME): cv.string,
        vol.Optional(ATTR_ROOM_TEMP): cv.positive_int,
    }
)

SCAN_INTERVAL = timedelta(seconds=60)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Adax climate."""

    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    data = {'username': username,
            'password': password,
            'grant_type': 'password'}

    ACCESS_TOKEN_URL = API_URL + '/auth/token'

    response = requests.post(ACCESS_TOKEN_URL, data=data)

    if response.status_code != 200:
        _LOGGER.info("Adax: Failed to login to retrieve token: %d", response.status_code)
        raise ConfigEntryNotReady
    res = response.json()
    token = res['access_token']

    headers = { "Authorization": "Bearer " + token }
    response = requests.get(API_URL + "/rest/v1/content/", headers = headers)
    res = response.json()

    dev = []
    for heater in res['rooms']:
        dev.append(AdaxHeater(heater, username, password))
    async_add_entities(dev)

    async def set_room_temp(service):
        """Set room temp."""
        room_name = service.data.get(ATTR_ROOM_NAME)
        sleep_temp = service.data.get(ATTR_ROOM_TEMP)
        """ TO FIX
        await mill_data_connection.set_room_temperatures_by_name(
            room_name, sleep_temp, comfort_temp, away_temp
        )
        """
    hass.services.async_register(
        DOMAIN, SERVICE_SET_ROOM_TEMP, set_room_temp, schema=SET_ROOM_TEMP_SCHEMA
    )


class AdaxHeater(ClimateEntity):
    """Representation of a Adax Thermostat device."""

    def __init__(self, heater, username, password):
        """Initialize the thermostat."""
        self._heater = heater
        self._settemp = 0.0
        self._username = username
        self._password = password

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
        res = {
            "heating": self._heater['heatingEnabled'],
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
        if self._heater['heatingEnabled'] == True:
            self._settemp = self._heater['targetTemperature'] / 100.0
            return self._settemp
        return None

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return 1

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._heater['temperature'] / 100.0

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
        """Return current hvac i.e. heat, cool, idle."""
        if self._heater['heatingEnabled'] == True:
            return CURRENT_HVAC_HEAT
        return CURRENT_HVAC_IDLE

    @property
    def hvac_mode(self) -> str:
        """Return hvac operation ie. heat, cool mode.

        Need to be one of HVAC_MODE_*.
        """
        if self._heater['heatingEnabled'] == True:
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

        newtemp = temperature * 100.0

        data = {'username': self._username,
                'password': self._password,
                'grant_type': 'password'}

        ACCESS_TOKEN_URL = API_URL + '/auth/token'

        response = requests.post(ACCESS_TOKEN_URL, data=data)

        if response.status_code != 200:
            _LOGGER.info("Adax: Failed to set new temperature: %d", response.status_code)
            return False
        res = response.json()
        token = res['access_token']

        headers = { "Authorization": "Bearer " + token }
        json = { 'rooms': [{ 'id': self.device_id, 'targetTemperature': str(newtemp) }] }
        requests.post(API_URL + '/rest/v1/control/', json = json, headers = headers)

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""

        data = {'username': self._username,
                'password': self._password,
                'grant_type': 'password'}

        ACCESS_TOKEN_URL = API_URL + '/auth/token'

        response = requests.post(ACCESS_TOKEN_URL, data=data)

        if response.status_code != 200:
            _LOGGER.info("Adax: Failed to update hvac_mode: %d", response.status_code)
            return False
        res = response.json()
        token = res['access_token']

        headers = { "Authorization": "Bearer " + token }
        newtemp = self._settemp * 100.0

        if hvac_mode == HVAC_MODE_HEAT:
            json = { 'rooms': [{ 'id': self.device_id, 'targetTemperature': str(newtemp) }] }
            requests.post(API_URL + '/rest/v1/control/', json = json, headers = headers)

        elif hvac_mode == HVAC_MODE_OFF:
            json = { 'rooms': [{ 'id': self.device_id, 'targetTemperature': str(0.0) }] }
            requests.post(API_URL + '/rest/v1/control/', json = json, headers = headers)

    async def async_update(self):
        """Retrieve latest state."""

        data = {'username': self._username,
                'password': self._password,
                'grant_type': 'password'}

        ACCESS_TOKEN_URL = API_URL + '/auth/token'

        response = requests.post(ACCESS_TOKEN_URL, data=data)

        if response.status_code != 200:
            _LOGGER.info("Adax: Failed to update information: %d", response.status_code)
            return False
        res = response.json()
        token = res['access_token']

        headers = { "Authorization": "Bearer " + token }
        response = requests.get(API_URL + "/rest/v1/content/", headers = headers)
        res = response.json()
        for room in res['rooms']:
            if self.device_id == room['id']:
                self._heater = room

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

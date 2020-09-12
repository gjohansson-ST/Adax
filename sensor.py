"""
A sensor created to read temperature from Adax radiators
For more details about this platform, please refer to the documentation at
https://github.com/kayjei/adax_wifi
"""
import logging
import json
import requests
from datetime import timedelta
import voluptuous as vol
from .connect import Adax
from .parameters import set_param

from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import (PLATFORM_SCHEMA)
from homeassistant.const import (TEMP_CELSIUS)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=60)

DEVICE_URL = 'https://heater.azurewebsites.net/sheater-client-api/rest/heaters/list/' + set_param("account_id")



def setup_platform(hass, config, add_devices, discovery_info=None):
    _LOGGER.debug("Adding sensor component: adax wifi ...")
    """Set up the sensor platform"""

    params = {"signature": set_param("device_signature"), "appVersion": set_param("appVersion"), "device": set_param("device"),
        "os": set_param("os"), "timeOffset": set_param("timeOffset"), "timeZone": set_param("timeZone")}

    devices_json = Adax.do_api_request(DEVICE_URL, params)

    for device in devices_json[1]:
        device_id = int(device["id"])
        name = device["name"]
        zone_name = device["zoneName"]
        state = round(float(device["currentTemperature"]) / 100, 2)
        target = round(float(device["targetTemperature"]) / 100, 2)
        FirmwareUpdate = device["hasFirmwareUpdate"]

        add_devices([AdaxDevice(device_id, zone_name, name, state, target, FirmwareUpdate)], True)


class AdaxDevice(Entity):
    def __init__(self, device_id, zone_name, name, temperature, target, FirmwareUpdate):
        self._device_id = device_id
        self._entity_id = "sensor.adax_" + str(self._device_id)
        self._zone_name = zone_name
        self._name = "Adax_" + name
        self._temperature = temperature
        self._target = target
        self._FirmwareUpdate = FirmwareUpdate

    @property
    def entity_id(self):
        """Return the id of the sensor"""
        return self._entity_id

    @property
    def name(self):
        """Return the name of the sensor"""
        return self._name

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return '°C'

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def state(self):
        """Return the state of the sensor"""
        return self._temperature

    @property
    def icon(self):
        """Return the icon of the sensor"""
        return 'mdi:radiator'

    @property
    def device_class(self):
        """Return the device class of the sensor"""
        return 'temperature'


    @property
    def device_state_attributes(self):
        """Return the attribute(s) of the sensor"""
        return {
            "targetTemperature": self._target,
            "zone": self._zone_name,
            "FirmwareUpdate": self._FirmwareUpdate
        }

    @Throttle(SCAN_INTERVAL)
    def update(self):
        DEVICE_URL = 'https://heater.azurewebsites.net/sheater-client-api/rest/heaters/list/' + set_param("account_id")
        params = {"signature": set_param("device_signature"), "appVersion": set_param("appVersion"), "device": set_param("device"),
        "os": set_param("os"), "timeOffset": set_param("timeOffset"), "timeZone": set_param("timeZone")}

        devices_json = Adax.do_api_request(DEVICE_URL, params)

        for device in devices_json[1]:
            if(self._device_id == int(device["id"])):
                self._temperature = round(float(device["currentTemperature"]) / 100, 2)

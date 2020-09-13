[![Adax heaters](https://github.com/gjohansson-ST/adax/blob/master/logo/logo.svg)](https://adax.no/)

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge&cacheSeconds=3600)](https://github.com/custom-components/hacs)
[![size_badge](https://img.shields.io/github/repo-size/gjohansson-ST/adax?style=for-the-badge&cacheSeconds=3600)](https://github.com/gjohansson-ST/adax)
[![version_badge](https://img.shields.io/github/v/release/gjohansson-ST/adax?label=Latest%20release&style=for-the-badge&cacheSeconds=3600)](https://github.com/gjohansson-ST/adax)


# Adax heater

---
**Title:** "Adax heaters"

**Description:** "Support for Adax heaters integration with Homeassistant."

**Date created:** 2020-09-13

**Last update:** 2020-09-13

---

Integrates with Adax heaters in your home.
Current support by API is on/off, read temperatures and set temperatures.
As per Adax design all settings are per room (as configured in the Adax phone app) and not per device.

#

This integration does not use account credentials. Read below instructions to enable service access to API

## Retrieve username & password

1. Logon to your Adax app on your phone
2. Username is the "Account ID" which is listed in the bottom part of the Account section
3. In same section below "THIRD PARTY INTEGRATIONS" Press "Remote user client API"
4. Press "Add credentials"
5. Give the service a name and copy the Password, this will be used as "Password" in this integration

## Installation

Option1:
Use [HACS](https://hacs.xyz/) to install

Option2:
Create a new folder under `custom_components` called `adax`. Upload the `***.py`-files in `custom_components/adax_heater` to the newly created folder.

In both Options you need to restart your Home Assistant to pick up the new integration before proceeding.

## Activate integration in HA

1. Go to Integrations in your installation
2. Click "+" for new integration and find Adax
3. Configure the new integration with your "username" & "password" as you have them per instructions above.

### Issues

Turn on debug logging as per instructions below and report new issue on Github.

```
Add debug logging
```python
 logger:
   logs:
     custom_components.adax_heater: debug
```

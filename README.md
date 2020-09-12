# Adax_heater

# First test

Modified from kayjei / adax_wifi
- Removed control, kept only read-only sensors

This integration does not use your account credentials. To be able to use it, the following paramters need to be extracted from the API calls.
The integration has been tested with 1 home and 1 zone only. To use multiple zones, use my dev-branch.

Guide:
1. Configure an SSL-proxy. In this example mitmproxy has been used in a docker container, but other installation may work as well. Mitmproxy listen on port 8080 for traffic and port 8081 for web-gui. https://medium.com/testvagrant/intercept-ios-android-network-calls-using-mitmproxy-4d3c94831f62
2. Configure your phone to use the proxy (covered in the same guide)
3. On your phone, open your Adax wifi app. Make sure you can see traffic in the mitmproxy gui
4. To be able to use the integration, you must extract from the API calls:
- ```account_id```: Passed in the URL in every call, i.e. zone list https://heater.azurewebsites.net/sheater-client-api/rest/zones/list/{account_id} Can also be found in your Adax app, under Account
- ```device_signature```: Signature passed as parameter with URL: https://heater.azurewebsites.net/sheater-client-api/rest/zones/list/{account_id}
You also need to extract the following values, from any call (fixed values in all calls):
- ```appVersion```
- ```device```
- ```os```
- ```timeOffset```
- ```timeZone```
5. Update the parameter section in the files
- parameters.py
	- ```account_id```
	- ```appVersion```
	- ```device```
	- ```os```
	- ```timeOffset```
	- ```timeZone```
	- ```device_signature``` (signature from zone URL)
6. Put the folder adax_wifi/ in $CONFIG/custom_components/
7. Add parameters in your configuration.yaml
```python
 sensor:
   - platform: Adax_heater
```
```python
 climate:
   - platform: Adax_heater
```
8. Add debug logging
```python
 logger:
   logs:
     custom_components.Adax_heater: debug
```
9. Restart Home Assistant

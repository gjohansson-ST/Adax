"""Parameter file for Adax integration"""

def set_param(api_call):
    switcher= {
    "account_id": '51647',
    "appVersion": 'iOS-adax-2.4.0',
    "device": 'iPhone10,4',
    "os": 'iOS%2013.4',
    "timeOffset": '120',
    "timeZone": 'Europe%2FStockholm',
    "device_signature": '302C02140F1F9EAAE375C195D55247205C4DEAEB0EF517AC021472EE20525E5798E08EE465C227B1C446209ED341'
    }
    return switcher.get(api_call,"Key missing")

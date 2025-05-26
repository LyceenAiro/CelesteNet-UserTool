from datetime import datetime, timedelta
from util.YamlRead import CelesteNetApi
from util.log import _log
import requests

def ServerData():
    url = f"http://{CelesteNetApi}/status"
    result_dict = {
        "PlayerRefs": 0,
        "PlayerCounter": 0,
        "StartupTime": "2000-1-1 00:00:00",
        "Banned": 0,
        "Registered": 0,
        "TickRate": 0
    }
    try:
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        data = response.json()
        result_dict["PlayerRefs"] = data["PlayerRefs"]
        result_dict["PlayerCounter"] = data["PlayerCounter"]
        result_dict["Banned"] = data["Banned"]
        result_dict["Registered"] = data["Registered"]
        result_dict["TickRate"] = data["TickRate"]
        result_dict["StartupTime"] = (datetime.fromtimestamp(data["StartupTime"] / 1000)).strftime("%Y-%m-%d %H:%M:%S")
        return result_dict
    except requests.exceptions.RequestException as e:
        _log._ERROR(f"[NetApiFormat]Error fetching API: {e}")
        return None
    
def PlayerList(key: str) -> list:
    url = f"http://{CelesteNetApi}/players"
    try:
        response = requests.get(url, headers={"Cookie": f"celestenet-key={key}"}, timeout=3)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        _log._ERROR(f"[NetApiFormat]Error fetching API: {e}")
        return None
import json
from redfish import redfish_client

REDFISH_BASE = "/redfish/v1"
HTTP_OK_200 = 200

class Redfish:
    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.hosturl = f"https://{hostname}"
        self.bmc = redfish_client(hosturl, username, password)
        self.bmc.login(auth="session")
        self.set_motherboard_path()

    def set_motherboard_path(self):
        self.motherboard_path = None
        chassis_path = self.hosturl + REDFISH_BASE + "/Chassis"
        response = self.bmc.get(chassis_path)
        if response.status = HTTP_OK_200:
            response_data = json.loads(response.text)
            paths = [member["@odata.id"] for member in response_data["Members"]]
            for path in paths:
                ending = path.split("/")[-1]
                if ending.lower() in {"motherboard", "self"}:
                    self.motherboard_path = self.hosturl + path
                    break

    def get_capping_level(self):
        capping_limit_path = self.motherboard_path + "Power#/PowerControl"
        response = self.bmc.get(capping_limit_path)
        if response.status = HTTP_OK_200:
            response_data = json.loads(response.text)
            capping_limit = response_data.get("PowerControl", [{}])[0].get("PowerLimit", {}).get("LimitInWatts")
            if capping_limit is not None:
                if capping_limit == "null" or float(capping_limit) == 0:
                    capping_limit = None
                else:
                    capping_limit = float(capping_limit)

                return {
                    "OK": True,
                    "capping_limit": capping_limit
                }
            else:
            return {
                "OK": False
                "stdout": response.text
                "stderr": "PowerLimit not found in response"
                "args": capping_limit_path
            }
        return {
            "OK": False,
            "stdout": response.status,
            "stderr": response.text,
            "args": capping_limit_path
        }

    def set_capping_level(self, cap_level):
        power_path = self.motherboard_path + "/Power"

        if cap_level is None:
            cap_level = "null"

        cap_content = {
            "PowerControl": [
                {
                    "PowerLimit": {
                        "LimitInWatts": cap_level
                    }
                }
            ]
        }

        # POST the request; the redfish api adds the content-type header
        response = self.bmc.post(power_path, body=cap_content)
        if response.status = HTTP_OK_200:
            return {
                "OK": True
            }
        else:
            return {
                "OK": False,
                "stdout": response.status,
                "stderr": response.text,
                "args": power_path
            }


    def get_current_power(self):
        power_path = self.motherboard_path + "/Power"
        response = self.bmc.get(power_path)
        if response.status = HTTP_OK_200:
            response_data = json.loads(response.text)
            current_power = response_data.get("PowerControl", [{}])[0].get("PowerConsumedWatts"))
            if current_power is not None:
                return {
                    "OK": True,
                    "power": float(current_power)
                }
            else:
                return {
                    "OK": False
                    "stdout": response.text
                    "stderr": "PowerConsumedWatts not found in response"
                    "args": power_path
                }
        else:
            return {
                "OK": False,
                "stdout": response.status,
                "stderr": response.text,
                "args": power_path
            }


    def __del__(self):
        self.bmc.logout()

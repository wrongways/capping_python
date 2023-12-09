from .ipmi import IPMI
from .redfish import Redfish

class BMC:
    def __init__(self, hostname, username, password, interface="REDFISH"):
        self.interface = Redfish(hostname, username, password) if interface == "REDFISH" else IPMI(hostname, username, password)

from datetime import datetime
from pathlib import Path
from threading import Thread


import time

from flask import Flask, request, jsonify

from helpers.utils import run_command, os_name, hostname, cpu_info, hw_info, run_firestarter

RAPL_PATH = "/sys/devices/virtual/powercap/intel-rapl/"
MAX_ENERGY_PATH = "intel-rapl:0/max_energy_range_uj"
RAPL_SAMPLE_TIME_SECS = 0.25
HTTP_202_ACCEPTED = 202




class CappingAgent(Flask):
    def __init__(self):
        super().__init__("CappingAgent")

        self.add_url_rule("/", view_func=self.time)
        self.add_url_rule("/rapl_stats", view_func=self.rapl_stats)
        self.add_url_rule("/system_info", view_func=self.system_info)
        self.add_url_rule("/firestarter", view_func=self.firestarter, methods=["POST"])

        rapl_path = Path(RAPL_PATH)
        rapl_packages = rapl_path.glob("intel-rapl:[0-9]*")
        self.sockets = {p: p.joinpath("name").read_text().strip() for p in rapl_packages}

        # ASSUMPTION: all sockets have the same max_energy_range_uj value
        max_uj_path = rapl_path.joinpath(MAX_ENERGY_PATH)
        self.max_uj = int(max_uj_path.read_text().strip())
        assert self.max_uj is not None and (self.max_uj > 0)

        self.firestarter_path = "/home_nfs/wainj/local/bin/firestarter"


    def time(self):
        now = datetime.now().astimezone().replace(microsecond=0).isoformat()
        return jsonify({'timestamp': now})

    def rapl_stats(self):

        # collect the initial values and timestamps for each socket/package
        start_values = {path: {
                'energy_uj': int(path.joinpath('energy_uj').read_text().strip()),
                'timestamp': time.time_ns(),
            } for path, name in self.sockets.items()
        }
        # wait a while for the counters to increment
        time.sleep(RAPL_SAMPLE_TIME_SECS)

        # calculate the power of each socket
        package_powers = {}
        for path, name in self.sockets.items():
            start_energy_uj = start_values[path]['energy_uj']
            start_timestamp = start_values[path]['timestamp']

            # read current energy consumption
            energy_uj = int(path.joinpath('energy_uj').read_text().strip())
            timestamp = time.time_ns()

            # check for counter wrap-around
            energy_delta_uj = (
                energy_uj - start_energy_uj if energy_uj > start_energy_uj
                else self.max_uj - start_energy_uj + energy_uj
            )

            time_delta_ns = timestamp - start_timestamp
            power_watts = energy_delta_uj / time_delta_ns * 1000
            package_powers[name] = power_watts

            print(f"{time_delta_ns=}")
            print(f"{energy_delta_uj=}")
            print(f"{power_watts=}")

        return jsonify(package_powers)

    def system_info(self):
        return jsonify(
            hw_info()  |
            cpu_info() |
            hostname() |
            os_name()
        )


    def firestarter(self):
        params = request.json
        t = Thread(
            target=run_firestarter,
            args=[
                self.firestarter_path,
                params.get("timeout", 10),
                params.get("load", 100),
                params.get("threads", 0)
            ]
        )
        t.start()

        return jsonify({}), HTTP_202_ACCEPTED


if __name__ == "__main__":
    a = CappingAgent()
    a.run(debug=True)

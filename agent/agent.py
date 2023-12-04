from pathlib import Path
from datetime import datetime
import shlex
import subprocess
import time

from flask import Flask, jsonify


RAPL_PATH = "/sys/devices/virtual/powercap/intel-rapl/"
MAX_ENERGY_PATH = "intel-rapl:0/max_energy_range_uj"


def run_command(command):
    return subprocess.run(
        shlex.split(command),
        encoding="utf8",
        text=True,
        capture_output=True,
        env={
            "LANG": "en_US.UTF-8",
        }
    )


def os_name():
    os_data = Path("/etc/os-release").read_text().splitlines()
    os_data = {d[0]: d[1] for d in [e.strip().split('=') for e in os_data] if len(d) == 2}
    os_name = os_data.get("PRETTY_NAME") or f"{os_data.get('NAME')} {os_data.get('VERSION')}"
    return {"os_name": os_name.strip('"')}


def hostname():
    return {"hostname": run_command("hostname -s").stdout.strip()}


def cpu_info():
    CPU_KEYS = [
        "Architecture",
        "CPU(s)",
        "Thread(s) per core",
        "Core(s) per socket",
        "Socket(s)",
        "Vendor ID",
        "Model name",
        "CPU MHz",
        "CPU max MHz",
        "CPU min MHz",
    ]

    cpu_data = run_command("lscpu").stdout
    # Transform each line into dictionary entry, split on colon ':'
    cpu_data = {d[0]: d[1] for d in [line.strip().split(":") for line in cpu_data.splitlines()]}
    return {k.lower().replace(" ", "_"): cpu_data[k].strip() for k in CPU_KEYS}


def hw_info():
    DMI_PATH = Path("/sys/devices/virtual/dmi/id")
    DMI_FILES = [
       "bios_date",
       "bios_vendor",
       "bios_version",
       "board_name",
       "board_vendor",
       "board_version",
       "sys_vendor",
    ]

    return {
       f: DMI_PATH.joinpath(f).read_text().strip() for f in DMI_FILES
    }


class CappingAgent(Flask):
    def __init__(self):
        super().__init__("CappingAgent")

        self.add_url_rule("/", view_func=self.time)
        self.add_url_rule("/rapl_stats", view_func=self.rapl_stats)
        self.add_url_rule("/system_info", view_func=self.system_info)

        rapl_path = Path(RAPL_PATH)
        rapl_packages = rapl_path.glob("intel-rapl:[0-9]*")
        self.sockets = {p: p.joinpath("name").read_text().strip() for p in rapl_packages}

        # ASSUMPTION: all sockets have the same max_energy_range_uj value
        max_uj_path = rapl_path.joinpath(MAX_ENERGY_PATH)
        self.max_uj = int(max_uj_path.read_text().strip())
        assert self.max_uj is not None and (self.max_uj > 0)

    def time(self):
        now = datetime.now().astimezone().replace(microsecond=0).isoformat()
        return jsonify({'timestamp': now})

    def rapl_stats(self):

        # collect the initial values and timestamps for each socket/package
        start_values = {path: {
                'energy_uj': int(path.join_path('energy_uj').read_text().strip()),
                'timestamp': time.time_ns(),
            } for path, name in self.sockets.items()
        }
        # wait a while for the counters to increment
        time.sleep(0.25)

        # calculate the power of each socket
        package_powers = {}
        for path, name in self.sockets.items():
            start_energy_uj = start_values[path]['energy_uj']
            start_timestamp = start_values[path]['timestamp']

            # read current energy consumption
            energy_uj = int(path.join_path('energy_uj').read_text().strip())
            timestamp = time.time_ns()

            # check for counter wrap-around
            energy_delta_uj = (
                energy_uj - start_energy_uj if energy_uj > start_energy_uj
                else self.max_uj - start_energy_uj + energy_uj
            )

            time_delta = timestamp - start_timestamp
            power_watts = energy_delta_uj / time_delta / 1_000_000

            package_powers[name] = power_watts

        return jsonify(package_powers)

    def system_info(self):
        return jsonify(
            hw_info()  |
            cpu_info() |
            hostname() |
            os_name()
        )


if __name__ == "__main__":
    a = CappingAgent()
    a.run(debug=True)

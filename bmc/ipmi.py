from capping.helpers import run_command


class IPMI:
    def __init__(self, hostname, username, password, ipmitool_path="/usr/bin/ipmitool"):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.ipmitool_path = ipmitool_path

    def get_capping_state(self):
        ipmi_cmd = ipmi_cmd = f"{self.ipmitool_path} dcmi power get limit"
        result = run_command(ipmi_cmd)
        if result.returncode == 0 and result.stderr is None:
            lines = result.stdout.splitlines()
            capping_fields = [line.split(":") for line in lines]
            capping_dict = {f[0]: f[1] for f in capping_fields if len(f) == 2}

            print(f"{capping_dict=}")

            capping_limit = (
                None if capping_dict["Current Limit State"] == "No Active Power Limit"
                else int(capping_dict["Power Limit"].split()[0])
            )

            return {
                "OK": True,
                "capping_limit": capping_limit
            }

        else:
            return {
                "OK": False,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "args": result.args
            }

    def set_capping_level(self, cap_level):
        if cap_level:
            ipmi_cmd = f"{self.ipmitool_path} dcmi power set_limit limit {cap_level}"
            result = run_command(ipmi_cmd)
            if result.returncode == 0 and result.stderr is None:
                ipmi_cmd = f"{self.ipmitool_path} dcmi power activate"
                result = run_command(ipmi_cmd)
        else:
            ipmi_cmd = f"{self.ipmitool_path} dcmi power deactivate"
            result = run_command(ipmi_cmd)

        if result.returncode == 0 and result.stderr is None:
            return {
                "OK": True
            }
        else:
            return {
                "OK": False,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "args": result.args
            }

    def get_current_power(self):
        ipmi_cmd = f"{self.ipmitool_path} dcmi power reading"
        result = run_command(ipmi_cmd)
        if result.returncode == 0 and result.stderr is None:
            for line in result.stdout.splitlines():
                if line.startswith("Instantaneous"):
                    power = int(line.split(":")[1].split()[0])
                    return {
                        "OK": True,
                        "power": power
                    }
        else:
            return {
                "OK": False,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "args": result.args
            }

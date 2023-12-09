from capping.helpers import run_command


class IPMI:
    def __init__(self, hostname, username, password, ipmitool_path="/usr/bin/ipmitool"):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.ipmitool_path = ipmitool_path
        self.ipmi_prefix = f"{ipmitool_path} -H {hostname} -U {username} -P {password}"

    def run_ipmi_command(self, command):
        ipmi_cmd = f"{self.ipmi_prefix} {command}"
        result = run_command(ipmi_cmd)
        if result["OK"]:
            ipmi_dict = None
            if result.stdout is not None:
                ipmi_fields = [line.split(":") for line in result.stdout.splitlines()]
                impi_dict = {f[0]: f[1] for f in capping_fields if len(f) == 2}

                print(f"{ipmi_dict=}")

            return {
                "OK": True,
                "ipmi_dict": ipmi_dict
            }
        else:
            return {
                "OK": False,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "args": result.args
            }


    def get_capping_level(self):
        ipmi_cmd = "dcmi power get limit"
        result = run_ipmi_command(ipmi_cmd)
        if result["OK"]:
            capping_limit = (
                None if result["ipmi_dict"]["Current Limit State"] == "No Active Power Limit"
                else float(result["ipmi_dict"]["Power Limit"].split()[0])
            )

            return {
                "OK": True,
                "capping_limit": capping_limit
            }

        else:
            return result

    def set_capping_level(self, cap_level):
        result = None
        if cap_level:
            ipmi_cmd = f"dcmi power set_limit limit {cap_level}"
            result = run_ipmi_command(ipmi_cmd)
            if result["OK"]:
                ipmi_cmd = "dcmi power activate"
                result = run_ipmi_command(ipmi_cmd)
        else:
            ipmi_cmd = f"{self.ipmitool_path} dcmi power deactivate"
            result = run_ipmi_command(ipmi_cmd)

        if result["OK"]:
            return {
                "OK": True
            }
        else:
            return result

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

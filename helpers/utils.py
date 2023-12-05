from pathlib import Path
import shlex
import subprocess

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

def run_firestarter(path, runtime_secs, load_pct, n_threads):
    assert load_pct > 0 and load_pct <= 100
    args = f"--timeout {runtime_secs} --load {load_pct} --threads {n_threads} --quiet"
    command_line = f"{path} {args}"
    _ = run_command(command_line)

import pathlib
import argparse
import subprocess


global ARGS


CFG_DIR = pathlib.Path("/etc/haproxy")
CFG_FILE = CFG_DIR / "haproxy.cfg"

MAP_DIR = CFG_DIR / "map"
MAP_301_FILE = MAP_DIR / "301"
MAP_BACKEND_FILE = MAP_DIR / "backend"

BACKEND_CONF = "        server {name} {host}:{port}"
BACKEND_FILE = "/etc/haproxy/x_{sni}.cfg"


def prepare():
    MAP_DIR.mkdir(exist_ok=True)
    MAP_301_FILE.touch(exist_ok=True)
    MAP_BACKEND_FILE.touch(exist_ok=True)


def parse_args():

    global ARGS

    parser = argparse.ArgumentParser()

    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        "--add",
        "-a",
        action="store_true",
        help="Add a backend",
    )
    action_group.add_argument(
        "--del",
        "-d",
        action="store_true",
        help="Del a backend",
    )

    parser.add_argument(
        "--sni",
        "-s",
        required=True,
        help="Server name indicator mapped to its backend",
    )
    parser.add_argument(
        "--host",
        "-H",
        required=False,
        help="Backend server host (required with --add)",
    )
    parser.add_argument(
        "--port",
        "-p",
        required=False,
        help="Backend server port (required with --add)",
    )
    parser.add_argument(
        "--transparent",
        "-t",
        default=False,
        action="store_true",
        help="Enable transparent bind",
    )

    args = parser.parse_args()

    # Validate conditional requirements
    if args.add and (not args.host or not args.port):
        parser.error("--host and --port are required when using --add")

    ARGS = args


def map_301():
    line = f"{ARGS.sni} 301"
    cmd = f"grep -qxF '{ARGS.sni} 301' {MAP_301_FILE} || echo '{ARGS.sni} 301' >> {MAP_301_FILE}" if ARGS.add else \
      f"sed -i '/{line}/d' {MAP_301_FILE}"
    subprocess.getstatusoutput(cmd)


def map_backend():
    line = f"{ARGS.sni} B_{ARGS.sni}"
    cmd = f"grep -qxF '{line}' {MAP_BACKEND_FILE} || echo '{line}' >> {MAP_BACKEND_FILE}" if ARGS.add else \
      f"sed -i '/{line}/d' {MAP_BACKEND_FILE}"
    subprocess.getstatusoutput(cmd)


def cfg_backend():
    backend_file = BACKEND_FILE.format(sni=ARGS.sni)
    if ARGS.add:
        backend_head = f"backend B_{ARGS.sni}"
        backend_conf = BACKEND_CONF.format(name=ARGS.sni, host=ARGS.host, port=ARGS.port)
        lines = [backend_head, backend_conf]
        with open(backend_file, "w") as f:
            for line in lines:
                f.write(line + "\n")
        return
    cmd = f"rm -f {backend_file}"
    subprocess.getstatusoutput(cmd)


def cfg_main():
    transparent_wildcard = "bind 0.0.0.0:443 transparent"
    transparent_wildcard_v6 = "bind :::443 v6only transparent"

    non_transparent_wildcard = "bind 0.0.0.0:443"
    non_transparent_wildcard_v6 = "bind :::443 v6only"

    source = "        source 0.0.0.0 usesrc clientip"
    default_web_ssl = "server default_web_ssl"

    ensure_transparent_wildcard = f"grep -qF '{transparent_wildcard}' {CFG_FILE} || sed -i 's/{non_transparent_wildcard}*/{transparent_wildcard}/' {CFG_FILE}"
    ensure_transparent_wildcard_v6 = f"grep -qF '{transparent_wildcard_v6}' {CFG_FILE} || sed -i 's/{non_transparent_wildcard_v6}*/{transparent_wildcard_v6}/' {CFG_FILE}"

    ensure_non_transparent_wildcard = f"grep -qF '{transparent_wildcard}' {CFG_FILE} && sed -i 's/{transparent_wildcard}*/{non_transparent_wildcard}/' {CFG_FILE}"
    ensure_non_transparent_wildcard_v6 = f"grep -qF '{transparent_wildcard_v6}' {CFG_FILE} && sed -i 's/{transparent_wildcard_v6}*/{non_transparent_wildcard_v6}/' {CFG_FILE}"

    ensure_source = f"grep -qF '{source}' {CFG_FILE} || sed -i '/{default_web_ssl}/i \{source}' {CFG_FILE}"
    ensure_non_source = f"grep -qF '{source}' {CFG_FILE} && sed -i '/{source}/d' {CFG_FILE}"

    cmd_list = [ensure_transparent_wildcard, ensure_transparent_wildcard_v6, ensure_source] if ARGS.transparent else \
        [ensure_non_transparent_wildcard, ensure_non_transparent_wildcard_v6, ensure_non_source]
    for cmd in cmd_list:
        subprocess.getstatusoutput(cmd)


def main():

    parse_args()

    prepare()
    cfg_main()
    cfg_backend()
    map_backend()
    map_301()


if __name__ == "__main__":
    main()

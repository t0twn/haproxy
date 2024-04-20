import sys
import re

import template


section_domain_backend = "B_{domain}"

sections = {
    "global": {},
    "defaults": {},
    "F_tcp_80": {
        "acl": "acl is_{domain} hdr_dom(host) -i -m beg {domain}",
        "use_backend": "use_backend B_redirect if is_{domain}"
    },
    "F_tcp_443": {
        "acl": "acl is_{domain} req_ssl_sni -i {domain}",
        "use_backend": "use_backend B_{domain} if is_{domain}"
    },
    "B_redirect": {
        "redirect": "redirect scheme https if {{ hdr(Host) -i {domain} }}"
    },
    "B_default_web": {},
    section_domain_backend: "server {server_name} {localhost}:{server_port_local}"
}


def generate(servers_info):
    ha_conf_content = ""
    indent_space = "        "
    line_terminate = "\n"

    for section in sections:
        if section == section_domain_backend:
            continue
        ha_conf_content += getattr(template, f"section_{section}")
        for partition in sections[section]:
            ha_conf_content += line_terminate
            for server_info in servers_info:
                domain = server_info[1]
                ha_conf_content += indent_space + sections[section][partition].format(domain=domain) + line_terminate

        ha_conf_content += line_terminate + line_terminate

    for server_info in servers_info:
        server_name, domain, server_port_local = server_info
        section_name = "backend " + section_domain_backend.format(domain=domain) + line_terminate
        section_content = indent_space + sections[section_domain_backend].format(
            server_name=server_name, localhost=template.localhost, server_port_local=server_port_local) + line_terminate
        ha_conf_content += section_name + section_content
        ha_conf_content += line_terminate + line_terminate

    return ha_conf_content


def main():
    script = sys.argv.pop(0)
    regex = "(?P<server_name>.+),(?P<domain>.+):(?P<server_port_local>.+)"
    pattern = re.compile(regex)
    servers_info = [pattern.match(server_info).groups() for server_info in sys.argv if pattern.match(server_info)]

    if not servers_info:
        print(f"Usage: python {script} server_name,domain:server_port_local")
    else:
        print(generate(servers_info))

if __name__ == "__main__":
    main()

localhost = "127.0.0.1"
default_web = [localhost, 81]

section_global = \
"""\
global
        daemon
        chroot /var/lib/haproxy
        log /dev/log local2 debug
"""


section_defaults = \
"""\
defaults
        log global
        mode tcp
        option tcplog
        option dontlognull
        option http-server-close
        timeout connect 24h
        timeout client 24h
        timeout server 24h
"""


section_F_tcp_80 = \
"""\
frontend F_tcp_80
        bind :::80

        tcp-request inspect-delay 2s
        tcp-request content accept if HTTP
        default_backend B_default_web
"""


section_F_tcp_443 = \
"""\
frontend F_tcp_443
        bind :::443

        tcp-request inspect-delay 5s
        tcp-request content accept if { req_ssl_hello_type 1 }
        default_backend B_default_web
"""


section_B_redirect = \
"""\
backend B_redirect
        mode http
        option forwardfor header Client-IP
"""


section_B_default_web = \
"""\
backend B_default_web
        mode http
        option forwardfor header Client-IP
        server default_web %s:%s
""" % (default_web[0], default_web[1])

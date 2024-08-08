openssl req -batch -new -x509 -newkey rsa:4096 -nodes -sha256 \
    -subj /CN=room.dhcn.vn/O=room.dhcn.vn -days 3650 \
    -keyout room.dhcn.vn.key \
    -out room.dhcn.vn.crt
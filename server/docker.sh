docker build -t blkb:dev . && docker run --name blkb  -v /var/run/dbus:/var/run/dbus --rm --network host --privileged blkb:dev

#sudo setcap 'cap_net_raw,cap_net_admin+eip' `which hcitool`
#sudo setcap 'cap_net_raw,cap_net_admin+eip' `which hciconfig`

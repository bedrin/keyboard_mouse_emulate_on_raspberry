FROM python:3-alpine

RUN apk add py3-pip g++ make pkgconfig dbus glib dbus-glib-dev dbus-dev dbus-glib cairo cairo-dev gobject-introspection-dev bluez bluez-deprecated

RUN pip3 install dbus-python PyGObject

WORKDIR /usr/src/app

ADD ./btk_server.py /usr/src/app/btk_server.py
ADD ./keymap.py /usr/src/app/keymap.py
ADD ./sdp_record.xml /usr/src/app/sdp_record.xml

CMD ["/usr/local/bin/python3", "/usr/src/app/btk_server.py"]

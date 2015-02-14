# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 GNS3 Technologies Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Interface for Dynamips virtual ATM switch module ("atmsw").
http://github.com/GNS3/dynamips/blob/master/README.hypervisor#L593
"""

import asyncio

from .device import Device
from ..dynamips_error import DynamipsError

import logging
log = logging.getLogger(__name__)


class ATMSwitch(Device):
    """
    Dynamips ATM switch.

    :param name: name for this switch
    :param node_id: Node instance identifier
    :param project: Project instance
    :param manager: Parent VM Manager
    :param hypervisor: Dynamips hypervisor instance
    """

    def __init__(self, name, node_id, project, manager, hypervisor=None):

        super().__init__(name, node_id, project, manager)
        self._nios = {}
        self._mapping = {}

    @asyncio.coroutine
    def create(self):

        if self._hypervisor is None:
            self._hypervisor = yield from self.manager.start_new_hypervisor()

        yield from self._hypervisor.send('atmsw create "{}"'.format(self._name))
        log.info('ATM switch "{name}" [{id}] has been created'.format(name=self._name, id=self._id))
        self._hypervisor.devices.append(self)

    @asyncio.coroutine
    def set_name(self, new_name):
        """
        Renames this ATM switch.

        :param new_name: New name for this switch
        """

        yield from self._hypervisor.send('atm rename "{name}" "{new_name}"'.format(name=self._name, new_name=new_name))
        log.info('ATM switch "{name}" [{id}]: renamed to "{new_name}"'.format(name=self._name,
                                                                              id=self._id,
                                                                              new_name=new_name))
        self._name = new_name


    @property
    def nios(self):
        """
        Returns all the NIOs member of this ATM switch.

        :returns: nio list
        """

        return self._nios

    @property
    def mapping(self):
        """
        Returns port mapping

        :returns: mapping list
        """

        return self._mapping

    @asyncio.coroutine
    def delete(self):
        """
        Deletes this ATM switch.
        """

        yield from self._hypervisor.send('atmsw delete "{}"'.format(self._name))
        log.info('ATM switch "{name}" [{id}] has been deleted'.format(name=self._name, id=self._id))
        self._hypervisor.devices.remove(self)
        self._instances.remove(self._id)

    def has_port(self, port):
        """
        Checks if a port exists on this ATM switch.

        :returns: boolean
        """

        if port in self._nios:
            return True
        return False

    def add_nio(self, nio, port_number):
        """
        Adds a NIO as new port on ATM switch.

        :param nio: NIO instance to add
        :param port_number: port to allocate for the NIO
        """

        if port_number in self._nios:
            raise DynamipsError("Port {} isn't free".format(port_number))

        log.info('ATM switch "{name}" [id={id}]: NIO {nio} bound to port {port}'.format(name=self._name,
                                                                                        id=self._id,
                                                                                        nio=nio,
                                                                                        port=port_number))

        self._nios[port_number] = nio

    def remove_nio(self, port_number):
        """
        Removes the specified NIO as member of this ATM switch.

        :param port_number: allocated port number
        """

        if port_number not in self._nios:
            raise DynamipsError("Port {} is not allocated".format(port_number))

        nio = self._nios[port_number]
        log.info('ATM switch "{name}" [{id}]: NIO {nio} removed from port {port}'.format(name=self._name,
                                                                                         id=self._id,
                                                                                         nio=nio,
                                                                                         port=port_number))

        del self._nios[port_number]
        return nio

    @asyncio.coroutine
    def map_vp(self, port1, vpi1, port2, vpi2):
        """
        Creates a new Virtual Path connection.

        :param port1: input port
        :param vpi1: input vpi
        :param port2: output port
        :param vpi2: output vpi
        """

        if port1 not in self._nios:
            raise DynamipsError("Port {} is not allocated".format(port1))

        if port2 not in self._nios:
            raise DynamipsError("Port {} is not allocated".format(port2))

        nio1 = self._nios[port1]
        nio2 = self._nios[port2]

        yield from self._hypervisor.send('atmsw create_vpc "{name}" {input_nio} {input_vpi} {output_nio} {output_vpi}'.format(name=self._name,
                                                                                                                              input_nio=nio1,
                                                                                                                              input_vpi=vpi1,
                                                                                                                              output_nio=nio2,
                                                                                                                              output_vpi=vpi2))

        log.info('ATM switch "{name}" [{id}]: VPC from port {port1} VPI {vpi1} to port {port2} VPI {vpi2} created'.format(name=self._name,
                                                                                                                          id=self._id,
                                                                                                                          port1=port1,
                                                                                                                          vpi1=vpi1,
                                                                                                                          port2=port2,
                                                                                                                          vpi2=vpi2))

        self._mapping[(port1, vpi1)] = (port2, vpi2)

    @asyncio.coroutine
    def unmap_vp(self, port1, vpi1, port2, vpi2):
        """
        Deletes a new Virtual Path connection.

        :param port1: input port
        :param vpi1: input vpi
        :param port2: output port
        :param vpi2: output vpi
        """

        if port1 not in self._nios:
            raise DynamipsError("Port {} is not allocated".format(port1))

        if port2 not in self._nios:
            raise DynamipsError("Port {} is not allocated".format(port2))

        nio1 = self._nios[port1]
        nio2 = self._nios[port2]

        yield from self._hypervisor.send('atmsw delete_vpc "{name}" {input_nio} {input_vpi} {output_nio} {output_vpi}'.format(name=self._name,
                                                                                                                              input_nio=nio1,
                                                                                                                              input_vpi=vpi1,
                                                                                                                              output_nio=nio2,
                                                                                                                              output_vpi=vpi2))

        log.info('ATM switch "{name}" [{id}]: VPC from port {port1} VPI {vpi1} to port {port2} VPI {vpi2} deleted'.format(name=self._name,
                                                                                                                          id=self._id,
                                                                                                                          port1=port1,
                                                                                                                          vpi1=vpi1,
                                                                                                                          port2=port2,
                                                                                                                          vpi2=vpi2))

        del self._mapping[(port1, vpi1)]

    @asyncio.coroutine
    def map_pvc(self, port1, vpi1, vci1, port2, vpi2, vci2):
        """
        Creates a new Virtual Channel connection (unidirectional).

        :param port1: input port
        :param vpi1: input vpi
        :param vci1: input vci
        :param port2: output port
        :param vpi2: output vpi
        :param vci2: output vci
        """

        if port1 not in self._nios:
            raise DynamipsError("Port {} is not allocated".format(port1))

        if port2 not in self._nios:
            raise DynamipsError("Port {} is not allocated".format(port2))

        nio1 = self._nios[port1]
        nio2 = self._nios[port2]

        yield from self._hypervisor.send('atmsw create_vcc "{name}" {input_nio} {input_vpi} {input_vci} {output_nio} {output_vpi} {output_vci}'.format(name=self._name,
                                                                                                                                                       input_nio=nio1,
                                                                                                                                                       input_vpi=vpi1,
                                                                                                                                                       input_vci=vci1,
                                                                                                                                                       output_nio=nio2,
                                                                                                                                                       output_vpi=vpi2,
                                                                                                                                                       output_vci=vci2))

        log.info('ATM switch "{name}" [{id}]: VCC from port {port1} VPI {vpi1} VCI {vci1} to port {port2} VPI {vpi2} VCI {vci2} created'.format(name=self._name,
                                                                                                                                                id=self._id,
                                                                                                                                                port1=port1,
                                                                                                                                                vpi1=vpi1,
                                                                                                                                                vci1=vci1,
                                                                                                                                                port2=port2,
                                                                                                                                                vpi2=vpi2,
                                                                                                                                                vci2=vci2))

        self._mapping[(port1, vpi1, vci1)] = (port2, vpi2, vci2)

    @asyncio.coroutine
    def unmap_pvc(self, port1, vpi1, vci1, port2, vpi2, vci2):
        """
        Deletes a new Virtual Channel connection (unidirectional).

        :param port1: input port
        :param vpi1: input vpi
        :param vci1: input vci
        :param port2: output port
        :param vpi2: output vpi
        :param vci2: output vci
        """

        if port1 not in self._nios:
            raise DynamipsError("Port {} is not allocated".format(port1))

        if port2 not in self._nios:
            raise DynamipsError("Port {} is not allocated".format(port2))

        nio1 = self._nios[port1]
        nio2 = self._nios[port2]

        yield from self._hypervisor.send('atmsw delete_vcc "{name}" {input_nio} {input_vpi} {input_vci} {output_nio} {output_vpi} {output_vci}'.format(name=self._name,
                                                                                                                                                       input_nio=nio1,
                                                                                                                                                       input_vpi=vpi1,
                                                                                                                                                       input_vci=vci1,
                                                                                                                                                       output_nio=nio2,
                                                                                                                                                       output_vpi=vpi2,
                                                                                                                                                       output_vci=vci2))

        log.info('ATM switch "{name}" [{id}]: VCC from port {port1} VPI {vpi1} VCI {vci1} to port {port2} VPI {vpi2} VCI {vci2} deleted'.format(name=self._name,
                                                                                                                                                id=self._id,
                                                                                                                                                port1=port1,
                                                                                                                                                vpi1=vpi1,
                                                                                                                                                vci1=vci1,
                                                                                                                                                port2=port2,
                                                                                                                                                vpi2=vpi2,
                                                                                                                                                vci2=vci2))
        del self._mapping[(port1, vpi1, vci1)]

    @asyncio.coroutine
    def start_capture(self, port_number, output_file, data_link_type="DLT_ATM_RFC1483"):
        """
        Starts a packet capture.

        :param port_number: allocated port number
        :param output_file: PCAP destination file for the capture
        :param data_link_type: PCAP data link type (DLT_*), default is DLT_ATM_RFC1483
        """

        if port_number not in self._nios:
            raise DynamipsError("Port {} is not allocated".format(port_number))

        nio = self._nios[port_number]

        data_link_type = data_link_type.lower()
        if data_link_type.startswith("dlt_"):
            data_link_type = data_link_type[4:]

        if nio.input_filter[0] is not None and nio.output_filter[0] is not None:
            raise DynamipsError("Port {} has already a filter applied".format(port_number))

        yield from nio.bind_filter("both", "capture")
        yield from nio.setup_filter("both", "{} {}".format(data_link_type, output_file))

        log.info('ATM switch "{name}" [{id}]: starting packet capture on {port}'.format(name=self._name,
                                                                                        id=self._id,
                                                                                        port=port_number))

    @asyncio.coroutine
    def stop_capture(self, port_number):
        """
        Stops a packet capture.

        :param port_number: allocated port number
        """

        if port_number not in self._nios:
            raise DynamipsError("Port {} is not allocated".format(port_number))

        nio = self._nios[port_number]
        yield from nio.unbind_filter("both")
        log.info('ATM switch "{name}" [{id}]: stopping packet capture on {port}'.format(name=self._name,
                                                                                        id=self._id,
                                                                                        port=port_number))
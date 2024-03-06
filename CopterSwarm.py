#!/usr/bin/env python
import json
import os.path
import signal
import sys
from copy import deepcopy
from threading import Lock
from typing import List

import numpy as np
import quaternion
from time import sleep
from AbstractVirtualCapability import AbstractVirtualCapability, VirtualCapabilityServer, formatPrint, \
    SubDeviceRepresentation


class CopterSwarm(AbstractVirtualCapability):

    def __init__(self, server):
        super().__init__(server)
        self.uri = "CopterSwarm"
        self.copters: List[SubDeviceRepresentation] = []
        self.__locks = []
        self.initialized = False

    def AddCopter(self, params: dict):
        self.copters.append(json.loads(params["Device"]))
        self.__locks.append(Lock())
        return {"DeviceList": self.copters}

    def GetAvaiableCopter(self, params: dict):
        while self.running and len(self.copters) > 0:
            for i, l in enumerate(self.__locks):
                if not l.locked():
                    l.acquire()
                    return {"Device": self.copters[i]}
        raise ValueError("No copter in this swarm!")

    def FreeCopter(self, params: dict):
        copter = SubDeviceRepresentation(params["Device"], self, None)
        for i, c in enumerate(self.copters):
            if copter.ood_id == c.ood_id and copter.json["requirements"] == c.json["requirements"]:
                self.__locks[i].release()
                return {"Device": c}
        raise ValueError(f"Device not found {copter}")

    def InitializeSwarm(self, params: dict):
        count = params["int"]
        for i in range(count - len(self.copters)):
            self.copters.append(self.query_sync("VirtualCopter"))
            self.__locks.append(Lock())
        self.initialized = True
        return {"DeviceList": self.copters}

    def loop(self):
        if self.initialized:
            for i, copter in enumerate(self.copters):
                battery_lvl = copter.invoke_sync("GetBatteryChargeLevel", {})["BatteryChargeLevel"]
                if battery_lvl < 15.:
                    formatPrint(self, f"Loading Copter: {copter.ood_id}")
                    self.__locks[i].acquire()
                    copter.invoke_sync("SetBatteryChargeLevel", {"BatteryChargeLevel": 100})
                    self.__locks[i].release()
        sleep(.0001)


if __name__ == '__main__':
    # Needed for properly closing when process is being stopped with SIGTERM signal
    def handler(signum, frame):
        print("[Main] Received SIGTERM signal")
        listener.kill()
        quit(1)


    try:
        port = None
        ip = None
        if len(sys.argv[1:]) > 0:
            port = int(sys.argv[1])
        if len(sys.argv[2:]) > 0:
            ip = str(sys.argv[2])
        server = VirtualCapabilityServer(port, ip)
        listener = CopterSwarm(server)
        listener.uri = "CopterSwarm"
        listener.start()
        signal.signal(signal.SIGTERM, handler)
        listener.join()
    # Needed for properly closing, when program is being stopped wit a Keyboard Interrupt
    except KeyboardInterrupt:
        print("[Main] Received KeyboardInterrupt")
        server.kill()
        listener.kill()

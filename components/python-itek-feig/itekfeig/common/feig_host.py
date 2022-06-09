#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from binascii import hexlify, unhexlify

from ..common.feig_base import FeigBase
from ..common.feig_errors import FeigError

TR_TYPE_BARCODE = 0xC2
TR_TYPE_EPC_C1G2 = 0x84

IDDT_EPC = 0x00
IDDT_EPC_TID = 0x02


class FeigHost(FeigBase):

    DB_SIZE = 2

    KILL_UNLOCK = 0x800000
    KILL_UNLOCK_PERMANENT = 0xC01000
    KILL_LOCK = 0x802000
    KILL_LOCK_PERMANENT = 0xC03000

    ACCESS_UNLOCK = 0x200000
    ACCESS_UNLOCK_PERMANENT = 0x300400
    ACCESS_LOCK = 0x200800
    ACCESS_LOCK_PERMANENT = 0x300C00

    EPC_UNLOCK = 0x080000
    EPC_UNLOCK_PERMANENT = 0x0C0100
    EPC_LOCK = 0x080200
    EPC_LOCK_PERMANENT = 0x0C03000

    TID_UNLOCK = 0x020000
    TID_UNLOCK_PERMANENT = 0x030040
    TID_LOCK = 0x020080
    TID_LOCK_PERMANENT = 0x0300C0

    USER_UNLOCK = 0x008000
    USER_UNLOCK_PERMANENT = 0x00C010
    USER_LOCK = 0x008020
    USER_LOCK_PERMANENT = 0x00C030

    def __init__(self, interface, lastError):
        """This class implements HOST mode functionality of Feig reader.

        Args:
            interface: This the interface on which communication will happen.
            lastError: This parameter is shared for reporting error
        """
        super().__init__()
        FeigBase._interface = interface
        FeigBase._last_error = lastError

    def _write_block(self, uid, bank, addr, db_size, wdata, access):
        uid_lng = len(uid)

        cmd = [0xB0, 0x24, 0x31, uid_lng] + uid
        if isinstance(access, list):
            bank = bank + 0x80
            cmd.append(bank)
            cmd.append(len(access))
            cmd = cmd + access
        else:
            cmd.append(bank)

        # DB-ADR
        cmd.append((addr >> 8) & 0xFF)
        cmd.append((addr >> 0) & 0xFF)

        # DB-N
        cmd.append(len(wdata) // db_size)

        # DB-SIZE
        cmd.append(db_size)

        # Data
        cmd = cmd + wdata

        data = FeigBase._interface.transfer(2.0, cmd)
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0xB0:
            FeigBase._last_error = self._feig_status_parser(data[1])
            return FeigBase._last_error is FeigError.OK

    def _read_block(self, uid, bank, addr, count, access):
        uid_lng = len(uid)

        cmd = [0xB0, 0x23, 0x31, uid_lng] + uid
        if isinstance(access, list):
            bank = bank + 0x80
            cmd.append(bank)
            cmd.append(len(access))
            cmd = cmd + access
        else:
            cmd.append(bank)

        # DB-ADR
        cmd.append((addr >> 8) & 0xFF)
        cmd.append((addr >> 0) & 0xFF)

        cmd.append(count)

        data = FeigBase._interface.transfer(1.0, cmd)
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return

        rblock = None
        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0xB0:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                if data[2] == count:
                    block_size = data[3]
                    offset = 4
                    rblock = list()
                    for _ in range(0, count):
                        if data[offset] != 0:
                            rblock.clear()
                            rblock = None
                            FeigBase._last_error = FeigError.INVALID_RESPONSE
                            break  # invalid block data

                        # copy
                        for j in range(0, block_size):
                            rblock.append(data[offset + j + 1])

                        offset = offset + 1 + block_size

        return rblock

    def _get_epc_len_from_protocol_bits(self, pc):
        epclen = int(pc[0])
        epclen = epclen >> 3
        return epclen * 2

    def _inventory(self, tags: list, ant_sel, more=False):
        mode = 0
        if more is True:
            mode = mode + 0x80
        more = False

        if ant_sel > 0:
            mode = mode + 0x10
            cmd = [0xB0, 0x01, mode, ant_sel]
        else:
            cmd = [0xB0, 0x01, mode]

        data = FeigBase._interface.transfer(2.0, cmd)
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return

        more = False
        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0xB0:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if (
                FeigBase._last_error is FeigError.MORE_DATA
                or FeigBase._last_error is FeigError.OK
            ):
                data_sets = data[2]
                data = data[3:]
                for _ in range(0, data_sets):
                    tag = {}
                    offset = 0
                    if ant_sel > 0:
                        #flags = data[0]
                        offset = 1

                    tr_type = data[offset + 0]
                    iddib = data[offset + 1]
                    iddlen = data[offset + 2]

                    # extract IDD consits of PC+EPC+TID
                    idd_start = offset + 3
                    idd_end = idd_start + iddlen
                    idd = data[idd_start:idd_end]

                    if tr_type == TR_TYPE_BARCODE:
                        tag["barcode"] = idd.decode("ascii")

                    elif tr_type == TR_TYPE_EPC_C1G2:
                        # extract PC(2bytes)
                        pc_len = 2
                        pc_start = 0
                        pc_end = pc_start + pc_len
                        pc = idd[pc_start:pc_end]

                        # get EPC
                        epc_len = self._get_epc_len_from_protocol_bits(pc)
                        epc_start = pc_end
                        epc_end = epc_start + epc_len
                        epc = hexlify(idd[epc_start:epc_end]).decode("ascii")

                        # get TID only when IDDIB = 02 i.e EPC+TID
                        tid = ""
                        if iddib == IDDT_EPC_TID:
                            tid_len = iddlen - epc_len - 2
                            tid_start = epc_end
                            tid_end = tid_start + tid_len
                            tid = hexlify(idd[tid_start:tid_end]).decode("ascii")

                        tag["epc"] = epc
                        tag["tid"] = tid

                        offset = offset + 3 + iddlen
                        if ant_sel > 0:
                            # Extracrt Antennas
                            tag["antennas"] = []
                            ant_cnt = data[offset]
                            for _ in range(0, ant_cnt):
                                ant_nr = data[offset + 1]
                                ant_stat = data[offset + 2]
                                rssi = data[offset + 3]
                                phase = data[offset + 4] * 256 + data[offset + 5]
                                phase = (phase * 360) // 4096
                                tag["antennas"].append(
                                    {
                                        "ant_no": ant_nr,
                                        "ant_stat": ant_stat,
                                        "rssi": rssi,
                                        "angle": phase,
                                    }
                                )
                                offset = offset + 7
                            offset = offset + 1

                    data = data[offset:]
                    tags.append(tag)
            more = FeigBase._last_error is FeigError.MORE_DATA

        return more

    def inventory(self, antennas=None):
        """Perform Inventory"""
        ant_sel = 0
        if antennas is not None and isinstance(antennas, list):
            for ant in antennas:
                ant_sel |= ant

        tags = []
        done = False
        more = False
        while not done:  # loop till MORE is set
            rsp = self._inventory(tags, ant_sel, more)
            if rsp is None:
                break

            more = rsp
            if more is False:
                done = True

        return tags

    def read_tid_memory(self, epc: str, tid: str, addr: int, count: int, access=None):
        """Read TID memory of the TAG"""
        if tid:
            uid = list(unhexlify(tid))
        else:
            uid = list(unhexlify(epc))

        if isinstance(access, str):
            access = list(unhexlify(access))  # convert to LIST
        else:
            access = None

        data = self._read_block(uid, self.BANK_TID, addr, count, access)
        if data:
            data = hexlify(bytes(data)).decode("ascii")

        return data

    def read_epc_memory(self, epc: str, tid: str, addr: int, count: int, access=None):
        """Read EPC memory of the TAG"""
        if tid:
            uid = list(unhexlify(tid))
        else:
            uid = list(unhexlify(epc))

        if isinstance(access, str):
            access = list(unhexlify(access))  # convert to LIST
        else:
            access = None

        data = self._read_block(uid, self.BANK_EPC, addr, count, access)
        if data:
            data = hexlify(bytes(data)).decode("ascii")

        return data

    def write_epc_memory(self, epc: str, tid: str, newepc: str, access=None):
        """Write epc to EPC memory of the TAG"""
        if tid:
            uid = list(unhexlify(tid))
        else:
            uid = list(unhexlify(epc))

        if isinstance(access, str):
            access = list(unhexlify(access))  # convert to LIST
        else:
            access = None

        data = self._write_block(
            uid, self.BANK_EPC, 2, self.DB_SIZE, list(unhexlify(newepc)), access
        )
        return data

    def read_user_memory(self, epc: str, tid: str, addr: int, count: int, access=None):
        """Read USER memory of the TAG"""
        if tid:
            uid = list(unhexlify(tid))
        else:
            uid = list(unhexlify(epc))

        if isinstance(access, str):
            access = list(unhexlify(access))  # convert to LIST
        else:
            access = None

        data = self._read_block(uid, self.BANK_USER, addr, count, access)
        if data:
            data = hexlify(bytes(data)).decode("ascii")

        return data

    def write_user_memory(self, epc: str, tid: str, addr: int, wdata: str, access=None):
        """Write data to USER memory of the TAG"""
        if tid:
            uid = list(unhexlify(tid))
        else:
            uid = list(unhexlify(epc))

        if isinstance(access, str):
            access = list(unhexlify(access))  # convert to LIST
        else:
            access = None

        data = self._write_block(
            uid, self.BANK_USER, addr, 1, list(unhexlify(wdata)), access
        )
        return data

    def read_access_password(self, epc: str, tid: str, access=None):
        """Read ACCESS PASSWWORD of the TAG"""
        if tid:
            uid = list(unhexlify(tid))
        else:
            uid = list(unhexlify(epc))

        if isinstance(access, str):
            access = list(unhexlify(access))  # convert to LIST
        else:
            access = None

        data = self._read_block(uid, self.BANK_RESERVED, 2, 2, access)
        if data:
            data = hexlify(bytes(data)).decode("ascii")

        return data

    def write_access_password(self, epc: str, tid: str, newpass: str, access=None):
        """Write Access password"""
        if tid:
            uid = list(unhexlify(tid))
        else:
            uid = list(unhexlify(epc))

        if isinstance(access, str):
            access = list(unhexlify(access))  # convert to LIST
        else:
            access = None

        data = self._write_block(
            uid, self.BANK_RESERVED, 2, self.DB_SIZE, list(unhexlify(newpass)), access
        )
        return data

    def read_kill_password(self, epc: str, tid: str, access=None):
        """Read KILL PASSWWORD of the TAG"""
        if tid:
            uid = list(unhexlify(tid))
        else:
            uid = list(unhexlify(epc))

        if isinstance(access, str):
            access = list(unhexlify(access))  # convert to LIST
        else:
            access = None

        data = self._read_block(uid, self.BANK_RESERVED, 0, 2, access)
        if data:
            data = hexlify(bytes(data)).decode("ascii")

        return data

    def write_kill_password(self, epc: str, tid: str, killpass: str, access=None):
        """Write Kill password"""
        if tid:
            uid = list(unhexlify(tid))
        else:
            uid = list(unhexlify(epc))

        if isinstance(access, str):
            access = list(unhexlify(access))  # convert to LIST
        else:
            access = None

        data = self._write_block(
            uid, self.BANK_RESERVED, 0, self.DB_SIZE, list(unhexlify(killpass)), access
        )
        return data

    def lock(self, epc: str, tid: str, flags: int, access: str):
        """Lock/unlock tag memory region"""
        if tid:
            uid = list(unhexlify(tid))
        else:
            uid = list(unhexlify(epc))

        uid_lng = len(uid)

        cmd = [0xB3, 0x22, 0x11, uid_lng] + uid + [0x84, 0x03]
        cmd += list(flags.to_bytes(3, "big"))

        access = list(unhexlify(access))  # convert to LIST
        cmd.append(len(access))
        cmd += access

        FeigBase._last_error = FeigError.COMM_TIMEOUT
        data = FeigBase._interface.transfer(1.0, cmd)
        if data:
            FeigBase._last_error = FeigError.INVALID_RESPONSE
            if data[0] == 0xB3:
                FeigBase._last_error = self._feig_status_parser(data[1])
                if FeigBase._last_error is FeigError.OK:
                    return True

        return False

    def permalock(self, epc, tid, access=None):
        raise NotImplementedError

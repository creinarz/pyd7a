#!/usr/bin/env python
#
# Copyright (c) 2015-2019 University of Antwerp, Aloxy NV.
#
# This file is part of pyd7a
# (see https://github.com/MOSAIC-LoPoW/pyd7a).
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

import argparse
import sys
import logging

from d7a.phy.channel_id import ChannelID
from d7a.system_files.engineering_mode import EngineeringModeFile, EngineeringModeMode
from d7a.alp.command import Command
from d7a.dll.access_profile import AccessProfile
from d7a.dll.sub_profile import SubProfile
from d7a.phy.channel_header import ChannelHeader, ChannelBand, ChannelCoding, ChannelClass
from d7a.phy.subband import SubBand
from d7a.system_files.access_profile import AccessProfileFile
from d7a.system_files.dll_config import DllConfigFile
from d7a.types.ct import CT

from modem.modem import Modem

from util.logger import configure_default_logger


def received_command_callback(cmd):
  logging.info(cmd)
  if cmd.execution_completed:
      sys.exit(0)

argparser = argparse.ArgumentParser()
argparser.add_argument("-d", "--device", help="serial device /dev file modem",
                            default="/dev/ttyUSB0")
argparser.add_argument("-r", "--rate", help="baudrate for serial device", type=int, default=115200)
argparser.add_argument("-v", "--verbose", help="verbose", default=False, action="store_true")
argparser.add_argument("-c", "--channel-id", help="for example 868LP000 ; format FFFRCIII where FFF={433, 868, 915}, R={L, N, H, R (LORA)}, C={P (PN9), F (FEC), C (CW)} III=000...280", default="868LP000")
argparser.add_argument("-e", "--eirp", help="EIRP in dBm", type=int, default=0)
argparser.add_argument("-sp", "--scan-automation-period", help="period in ms of scanning (786 ~ total 1 sec), 0 is continuous scan ", default=0)
argparser.add_argument("-sb", "--subband_bitmap", help="subband bitmap of subprofiles, 0 is default, 1 is scanning", default=0)
config = argparser.parse_args()
configure_default_logger(config.verbose)

ch = ChannelID.from_string(config.channel_id)
print("Using mode {} for channel {} with TX EIRP {} dBm".format(config.mode, config.channel_id, config.eirp))
mode = EngineeringModeMode.from_string(config.mode)

modem = Modem(config.device, config.rate, unsolicited_response_received_callback=received_command_callback)
modem.connect()

channel_header = ChannelHeader(
  channel_class=ch.channel_header.channel_class,
  channel_coding=ch.channel_header.channel_coding,
  channel_band=ch.channel_header.channel_band
)

access_profile = AccessProfile(
  channel_header=channel_header,
  sub_profiles=[SubProfile(subband_bitmap=0x00, scan_automation_period=CT.compress(0))] * 4,
  sub_bands=[SubBand(eirp=config.eirp, channel_index_start=ch.channel_index, channel_index_end=ch.channel_index)] * 8
)

modem.execute_command(
  alp_command=Command.create_with_write_file_action_system_file(
    file=AccessProfileFile(access_profile=access_profile, access_specifier=config.specifier)
  )
)


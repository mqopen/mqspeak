# Copyright (C) Ivo Slanina <ivo.slanina@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse

def create_parser():
    parser = argparse.ArgumentParser(
        description="MQTT to ThingSpeak bridge",
        epilog="Copyright (C) Ivo Slanina <ivo.slanina@gmail.com> https://github.com/buben19/mqspeak",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--config',
                        help='path to configuration file',
                        default="/etc/mqttbridge.conf")

    # TODO: add verbose flag

    return parser

def parse_args():
    parser = create_parser()
    return parser.parse_args()

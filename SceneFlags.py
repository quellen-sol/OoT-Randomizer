from __future__ import annotations
from math import ceil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Location import Location
    from World import World


# Create a dict of dicts of the format:
# {
#   scene_number_n : {
#       room_setup_number: max_flags
#   }
# }
# where room_setup_number defines the room + scene setup as ((setup << 6) + room) for scene n
# and max_flags is the highest used enemy flag for that setup/room
def get_collectible_flag_table(world: World) -> tuple[dict[int, dict[int, int]], list[tuple[Location, tuple[int, int, int], tuple[int, int, int]]]]:
    scene_flags = {}
    alt_list = []
    for i in range(0, 101):
        scene_flags[i] = {}
        for location in world.get_locations():
            if location.scene == i and location.type in ["Freestanding", "Pot", "FlyingPot", "Crate", "SmallCrate", "Beehive", "RupeeTower", "SilverRupee"]:
                default = location.default
                if isinstance(default, list):  # List of alternative room/setup/flag to use
                    primary_tuple = default[0]
                    for c in range(1, len(default)):
                        alt_list.append((location, default[c], primary_tuple))
                    default = primary_tuple  # Use the first tuple as the primary tuple
                if isinstance(default, tuple):
                    room, setup, flag = default
                    room_setup = room + (setup << 6)
                    if room_setup in scene_flags[i].keys():
                        curr_room_max_flag = scene_flags[i][room_setup]
                        if flag > curr_room_max_flag:
                            scene_flags[i][room_setup] = flag
                    else:
                        scene_flags[i][room_setup] = flag
        if len(scene_flags[i].keys()) == 0:
            del scene_flags[i]
    return scene_flags, alt_list


# Create a byte array from the scene flag table created by get_collectible_flag_table
def get_collectible_flag_table_bytes(scene_flag_table: dict[int, dict[int, int]]) -> tuple[bytearray, int]:
    num_flag_bytes = 0
    bytes = bytearray()
    bytes.append(len(scene_flag_table.keys()))
    for scene_id in scene_flag_table.keys():
        rooms = scene_flag_table[scene_id]
        room_count = len(rooms.keys())
        bytes.append(scene_id)
        bytes.append(room_count)
        for room in rooms:
            bytes.append(room)
            bytes.append((num_flag_bytes & 0xFF00) >> 8)
            bytes.append(num_flag_bytes & 0x00FF )
            num_flag_bytes += ceil((rooms[room] + 1) / 8)

    return bytes, num_flag_bytes


def get_alt_list_bytes(alt_list: list[tuple[Location, tuple[int, int, int], tuple[int, int, int]]]) -> bytearray:
    bytes = bytearray()
    for entry in alt_list:
        location, alt, primary = entry
        room, scene_setup, flag = alt
        if location.scene is None:
            continue

        alt_override = (room << 8) + (scene_setup << 14) + flag
        room, scene_setup, flag = primary
        primary_override = (room << 8) + (scene_setup << 14) + flag
        bytes.append(location.scene)
        bytes.append(0x06)
        bytes.append((alt_override & 0xFF00) >> 8)
        bytes.append(alt_override & 0xFF)
        bytes.append(location.scene)
        bytes.append(0x06)
        bytes.append((primary_override & 0xFF00) >> 8)
        bytes.append(primary_override & 0xFF)
    return bytes

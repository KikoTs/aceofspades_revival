import glob, os, math
from shared.common import *
from shared.constants import DEFAULT_PREFAB_HEALTH, PREFAB_LISTS
from shared.constants_prefabs import DEFAULT_PREFAB_TAGS_BY_MAP, PREFABS_NAMES_WITH_TAGS
from shared.glm import Vector3

class PrefabManager:

    def __init__(self, owner=None):
        self.prefab_palette = {}
        self.create_prefab_palette()
        self.map_prefabs = []
        self.owner = owner

    def unload_model(self, model):
        if model:
            model.destroy_kv6()

    def create_prefab_palette(self):
        import sys
        prefab_path = get_relative_path(['.', '../common', '../../common'], 'prefabs')
        id = 0
        for filename in glob.glob(os.path.join(prefab_path, '*.png')):
            name = os.path.splitext(os.path.basename(filename))[0]
            self.prefab_palette[id] = {'name': name, 'image_path': (os.path.splitext(filename)[0]), 'model': None, 'noof_blocks': 0, 'image': None}
            id += 1

        self.prefab_count = self.non_ugc_prefab_count = id
        return

    def create_ugc_prefab_palette(self, prefab_sets=[]):
        prefab_path = get_relative_path(['./ugc', '../common/ugc', '../../common/ugc'], 'prefabs')
        id = self.non_ugc_prefab_count
        PREFAB_LISTS[A476] = []
        if prefab_sets is not None and len(prefab_sets) > 0:
            map_tags = set(prefab_sets)
            for filename in glob.glob(os.path.join(prefab_path, '*.png')):
                name = os.path.splitext(os.path.basename(filename))[0]
                if name in PREFABS_NAMES_WITH_TAGS and len(map_tags.intersection(PREFABS_NAMES_WITH_TAGS[name])) > 0:
                    self.prefab_palette[id] = {'name': name, 'image_path': (os.path.splitext(filename)[0]), 'model': None, 'noof_blocks': 0, 'image': None}
                    PREFAB_LISTS[A476].append(name)
                    id += 1

        else:
            for filename in glob.glob(os.path.join(prefab_path, '*.png')):
                name = os.path.splitext(os.path.basename(filename))[0]
                self.prefab_palette[id] = {'name': name, 'image_path': (os.path.splitext(filename)[0]), 'model': None, 'noof_blocks': 0, 'image': None}
                PREFAB_LISTS[A476].append(name)
                id += 1

        self.prefab_count = id
        return

    def delete_ugc_prefab_palette(self):
        if self.non_ugc_prefab_count == self.prefab_count:
            return
        for id in xrange(self.non_ugc_prefab_count, self.prefab_count):
            self.unload_model(self.prefab_palette[id]['model'])
            del self.prefab_palette[id]

        self.prefab_count = self.non_ugc_prefab_count
        PREFAB_LISTS[A476] = []

    def get_prefab_image(self, prefab_name):
        prefab_name = prefab_name.lower()
        for key, value in self.prefab_palette.iteritems():
            name = self.prefab_palette[key]['name'].lower()
            if prefab_name.find('prefab_') == -1:
                name = name.split('prefab_', 1)[1]
            if name == prefab_name:
                return self.prefab_palette[key]['image']

        return

    def get_prefab_model(self, id):
        if id not in self.prefab_palette:
            return
        return self.prefab_palette[id]['model']

    def get_prefab_id_by_name(self, prefab_name):
        prefab_name = prefab_name.lower()
        for key, value in self.prefab_palette.iteritems():
            name = self.prefab_palette[key]['name'].lower()
            if prefab_name.find('prefab_') == -1:
                name = name.split('prefab_', 1)[1]
            if name == prefab_name:
                return key

        return

    def get_prefab_block_count(self, id):
        if id not in self.prefab_palette:
            return 0
        return self.prefab_palette[id]['noof_blocks']

    def get_prefab_string(self, prefab_name):
        try:
            return strings.get_by_id_or_except(prefab_name.upper())
        except KeyError:
            print ('WARNING; Failed to find string for {0}.').format(prefab_name)
            return prefab_name

    def build_prefab(self, block_manager, player, player_id, prefab_name, position, map, infinite_blocks, callback_owner=None, player_block_count=1000, color=None, check_world_touch=True, check_visible=True, check_beach_layer=True, add_to_user_blocks=True, game_mode=A2441, prefab_yaw=0, prefab_pitch=0, prefab_roll=0, from_block_index=0, to_block_index=0, time_limit=0):
        if position is None or prefab_yaw is None or prefab_name is None or block_manager is None:
            return 0
        if self.owner:
            if player is None:
                return 0
        model = self.find_prefab(player, prefab_name)
        if model is None:
            return 0
        else:
            if check_beach_layer and map and not self.allowed_on_beach_layer(model, position, map, prefab_yaw):
                return 0
            if check_world_touch and map and not self.touches_world(model=model, position_tuple=position, map=map, prefab_yaw=prefab_yaw, prefab_pitch=prefab_pitch, prefab_roll=prefab_roll, check_world_bounds=game_mode != A2447):
                return 0
            if self.owner:
                for server_player in self.owner.players.values():
                    if server_player.world_object is not None and server_player.class_id != A87:
                        colliding = self.prefab_collide_with_player(server_player.world_object.position, server_player.is_crouching(), position, model, prefab_yaw, prefab_pitch, prefab_roll)
                        if colliding:
                            return 0

                if check_visible and player is not None:
                    if not self.prefab_is_visible(self.owner.world, player.world_object.position, position, model, prefab_yaw, prefab_pitch, prefab_roll):
                        return 0
            model_points = model.get_points()
            if len(model_points) > player_block_count and not infinite_blocks:
                return 0
            placed_blocks = 0
            if not add_to_user_blocks:
                placed_blocks = map.place_prefab_in_world(model, position[0], position[1], position[2], prefab_yaw, prefab_pitch, prefab_roll, from_block_index=from_block_index, to_block_index=to_block_index, time_limit=time_limit)
                if placed_blocks <= 0:
                    return 0
            else:
                for x, y, z, r, g, b in model_points:
                    model_color = (
                     r, g, b)
                    point = rotate_y_axis(math.floor(x), math.floor(y), math.floor(z), prefab_roll)
                    point = rotate_x_axis(math.floor(point[0]), math.floor(point[1]), math.floor(point[2]), prefab_pitch)
                    point = rotate_z_axis(math.floor(point[0]), math.floor(point[1]), math.floor(point[2]), prefab_yaw)
                    if player is not None and game_mode == A2447:
                        prefab_color = model_color
                    else:
                        if color != None:
                            prefab_color = color
                        else:
                            prefab_color = player.team.color
                        prefab_color = blend_color(prefab_color, model_color, 0.5)
                    block_manager.add_user_block(player_id, point[0] + position[0], point[1] + position[1], point[2] + position[2], prefab_color + (255, ), DEFAULT_PREFAB_HEALTH, replace_solids=True)
                    placed_blocks += 1
                    if callback_owner is not None and not game_mode == A2447:
                        max_size_z = model.get_max_z_size()
                        x_size, y_size, z_size = model.get_sizes()
                        if z == max_size_z:
                            callback_owner.create_smoke_ring((point[0] + position[0], point[1] + position[1], point[2] + position[2] + 1.0), (x_size - 1.0) / 2.0)

            if self.owner:
                for server_player in self.owner.players.values():
                    if server_player.world_object is not None and game_mode == A2447:
                        colliding = is_player_in_solid_block(server_player.world_object.position, server_player.is_crouching(), map)
                        if colliding:
                            x = int(server_player.world_object.position.x)
                            y = int(server_player.world_object.position.y)
                            z = int(server_player.world_object.position.z)
                            safe_found = False
                            while z <= A2215 and map.get_solid(x, y, z) or z + 1 <= A2215 and map.get_solid(x, y, z + 1) or z + 2 <= A2215 and map.get_solid(x, y, z + 2):
                                z -= 1

                            server_player.world_object.set_position(x + 0.5, y + 0.5, z + 2.0 - A253, True)

            return placed_blocks

    def erase_prefab(self, block_manager, player, player_id, prefab_name, position, map, callback_owner=None, prefab_yaw=0, prefab_pitch=0, prefab_roll=0, from_block_index=0, to_block_index=0, time_limit=0):
        if position is None or prefab_yaw is None or prefab_name is None or block_manager is None or player is None:
            return 0
        model = self.find_prefab(player, prefab_name)
        if model is None:
            return 0
        else:
            return map.erase_prefab_from_world(model, position[0], position[1], position[2], prefab_yaw=prefab_yaw, prefab_pitch=prefab_pitch, prefab_roll=prefab_roll, from_block_index=from_block_index, to_block_index=to_block_index, time_limit=time_limit)

    def find_prefab(self, player, prefab_name):
        if prefab_name is None:
            return
        else:
            if self.owner:
                if player is None:
                    return
                if player.class_id is None:
                    return
                prefab_exists_in_class = False
                for item in A554[player.class_id][A519]:
                    prefab_list = PREFAB_LISTS[item]
                    for prefab in prefab_list:
                        if prefab_name.lower() == prefab.lower():
                            prefab_exists_in_class = True

                if not prefab_exists_in_class:
                    return
            id = self.get_prefab_id_by_name(prefab_name)
            if id is None:
                return
            model = self.get_prefab_model(id)
            return model

    def get_prefab_ghost_position(self, player_position, player_orientation, player_crouching, map, prefab_model, check_world_intersect=True, check_world_touch=True, use_player_orientation=True, prefab_yaw=0, prefab_pitch=0, prefab_roll=0, check_world_bounds=False):
        z_to_feet = A254 if player_crouching else A253
        player_floor_z = math.floor(player_position.z + z_to_feet)
        size_x, size_y, size_z = prefab_model.get_sizes()
        world_size_x, world_size_y, world_size_z = rotate_y_axis(size_x, size_y, size_z, prefab_roll)
        world_size_x, world_size_y, world_size_z = rotate_x_axis(world_size_x, world_size_y, world_size_z, prefab_pitch)
        world_size_x, world_size_y, world_size_z = rotate_z_axis(world_size_x, world_size_y, world_size_z, prefab_yaw)
        prefab_sq_radius = (world_size_x * world_size_x + world_size_y * world_size_y + world_size_z * world_size_z) / 4.0
        prefab_radius = math.sqrt(prefab_sq_radius)
        prefab_distances = A2253[prefab_radius] if prefab_radius in A2253 else A2253[min(A2253.keys(), key=(lambda k: abs(k - prefab_radius)))]
        prefab_constant_distance_from_player = prefab_distances[A2249]
        prefab_scaled_distance_from_player = prefab_distances[A2250]
        prefab_min_distance_from_player = prefab_distances[A2251]
        prefab_max_distance_from_player = prefab_distances[A2252]
        distance = prefab_radius * prefab_scaled_distance_from_player + prefab_constant_distance_from_player
        if distance < prefab_min_distance_from_player:
            distance = prefab_min_distance_from_player
        if distance > prefab_max_distance_from_player:
            distance = prefab_max_distance_from_player
        x = player_position.x + distance * player_orientation[0]
        y = player_position.y + distance * player_orientation[1]
        z = player_position.z + distance * player_orientation[2]
        if z >= A2214 - 1:
            z = A2214 - 1
        scan_position = Vector3(math.floor(x), math.floor(y), math.floor(z))
        (x_lo, y_lo, z_lo), (x_hi, y_hi, z_hi) = prefab_model.get_bounds()
        scan_position.x -= int(world_size_x / 2.0)
        scan_position.y -= int(world_size_y / 2.0)
        scan_position.z -= int(world_size_z / 2.0)
        player_relative_offset = Vector3(0, 0, 0)
        if use_player_orientation:
            player_direction = get_facing(player_orientation[0], player_orientation[1])
            prefab_prefab_yaw_override = (prefab_yaw + A2227 - player_direction) % A2227
            player_relative_offset = Vector3(0, 0, 0)
            if size_x & 1 == 0:
                if prefab_prefab_yaw_override == A2226:
                    player_relative_offset.y += 1
                if prefab_prefab_yaw_override == A2225:
                    player_relative_offset.x -= 1
            if size_y & 1 == 0:
                if prefab_prefab_yaw_override == A2223:
                    player_relative_offset.y += 1
                if prefab_prefab_yaw_override == A2226:
                    player_relative_offset.x -= 1
            world_offset_x, world_offset_y, world_offset_z = rotate_z_axis(player_relative_offset.x, player_relative_offset.y, player_relative_offset.z, player_direction)
            scan_position.x += world_offset_x
            scan_position.y += world_offset_y
            scan_position.z += world_offset_z
        else:
            player_direction = 0
        scan_position.z += int(A2255 * size_z / 2.0)
        if check_world_touch:
            can_place = self.touches_world(model=prefab_model, position_tuple=(
             scan_position.x, scan_position.y, scan_position.z), map=map, prefab_yaw=prefab_yaw, prefab_pitch=prefab_pitch, prefab_roll=prefab_roll, check_world_bounds=check_world_bounds)
        else:
            can_place = True
        if check_world_intersect:
            looking_down = math.floor(player_orientation.z) >= 0.0
            while self.intersects_with_world(prefab_model, scan_position, map, prefab_yaw) and (looking_down and scan_position.z + z_hi > player_floor_z or scan_position.z - z_lo >= A2214 - 1):
                move_point_towards_face(scan_position, A24, 1.0)

        prefab_center = scan_position + Vector3(int(world_size_x / 2.0), int(world_size_y / 2.0), int(world_size_z / 2.0))
        return (can_place, scan_position, prefab_center)

    def intersects_with_world(self, model, position, map, prefab_yaw=0, prefab_pitch=0, prefab_roll=0):
        points = model.get_points()
        for x, y, z, r, g, b in points:
            rx, ry, rz = rotate_y_axis(x, y, z, prefab_roll)
            rx, ry, rz = rotate_x_axis(rx, ry, rz, prefab_pitch)
            rx, ry, rz = rotate_z_axis(rx, ry, rz, prefab_yaw)
            if map.get_solid(int(position.x + rx), int(position.y + ry), int(position.z + rz)):
                return True

        return False

    def touches_world(self, model, position_tuple, map, prefab_yaw=0, prefab_pitch=0, prefab_roll=0, check_world_bounds=False):
        px, py, pz = position_tuple
        return map.get_prefab_touches_world(model, px, py, pz, prefab_yaw, prefab_pitch, prefab_roll, check_world_bounds)

    def allowed_on_beach_layer(self, model, position_tuple, map, prefab_yaw):
        max_modifiable_z = map.get_max_modifiable_z()
        px, py, pz = position_tuple
        (x_lo, y_lo, z_lo), (x_hi, y_hi, z_hi) = model.get_bounds()
        return z_hi + pz <= max_modifiable_z

    def prefab_collide_with_player(self, player_position, player_is_crouching, prefab_position, model, prefab_yaw, prefab_pitch, prefab_roll):
        position = (
         int(player_position.x), int(player_position.y), int(player_position.z))
        for x, y, z, r, g, b in model.get_points():
            colour = (r, g, b)
            x, y, z = rotate_y_axis(x, y, z, prefab_roll)
            x, y, z = rotate_x_axis(x, y, z, prefab_pitch)
            x, y, z = rotate_z_axis(x, y, z, prefab_yaw)
            point = (int(x) + prefab_position[0], int(y) + prefab_position[1], int(z) + prefab_position[2])
            if is_block_in_player_space(point, player_position, player_is_crouching):
                return True

        return False

    def prefab_is_visible(self, world, player_position, prefab_position, model, prefab_yaw, prefab_pitch, prefab_roll):
        for x, y, z, r, g, b in model.get_points():
            colour = (r, g, b)
            x, y, z = rotate_y_axis(x, y, z, prefab_roll)
            x, y, z = rotate_x_axis(x, y, z, prefab_pitch)
            x, y, z = rotate_z_axis(x, y, z, prefab_yaw)
            point = Vector3(int(x) + prefab_position[0] + 0.5, int(y) + prefab_position[1] + 0.5, int(z) + prefab_position[2] + 0.5)
            direction = point - player_position
            ret = world.hitscan(player_position, direction)
            if ret is None:
                return True
            hit_distance = distance_vector_3d(player_position, ret[0])
            point_distance = distance_vector_3d(player_position, point)
            if hit_distance > point_distance:
                return True

        return False

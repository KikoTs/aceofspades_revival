from aoslib import image
from shared.common import hitscan_model, distance_vector_3d, to_pitch_yaw
from aoslib.world import is_centered
from shared.constants import *
from shared.glm import Vector3
from shared.constants_DLC import get_tool_dlc_Name

def load_weapon_image(name):
    return image.load_texture(['weapons', name], center=True)


TOOL_IMAGES = {}
for tool_id, tool_name in TOOL_FILE_NAMES.items():
    has_image = TOOL_HAS_IMAGE[tool_id]
    if has_image == 2:
        TOOL_IMAGES[tool_id] = (
         load_weapon_image(tool_name + '_blue'), load_weapon_image(tool_name + '_green'), load_weapon_image(tool_name + '_neutral'))
    elif has_image:
        TOOL_IMAGES[tool_id] = load_weapon_image(tool_name)

def load_weapon_icon(name):
    return image.load(['icons', 'weapons', name], center=True)


def hitscan_player(pos, orientation, victim):
    victim_pos = victim.world_object.position
    victim_orientation = victim.world_object.orientation
    victim_pitch, victim_yaw = to_pitch_yaw(victim_orientation.x, victim_orientation.y, victim_orientation.z)
    victim_pos = victim.world_object.position
    hit = hitscan_model(pos, orientation, victim.torso, victim_pos, victim_yaw)
    if hit:
        return (PART_TORSO, hit)
    else:
        hit = hitscan_model(pos, orientation, victim.head, victim_pos, victim_yaw)
        if hit:
            return (PART_HEAD, hit)
        hit = hitscan_model(pos, orientation, victim.arms, victim_pos, victim_yaw)
        if hit:
            return (PART_ARMS, hit)
        hit = hitscan_model(pos, orientation, victim.left_leg, victim_pos, victim_yaw)
        if hit:
            return (PART_LEFT_LEG, hit)
        hit = hitscan_model(pos, orientation, victim.right_leg, victim_pos, victim_yaw)
        if hit:
            return (PART_RIGHT_LEG, hit)
        return (None, None)


def make_blood_particles(scene, position):
    from aoslib.gfx.particleEffectManager import ParticleEffectManager
    scene.particle_effect_manager.create_particle_effect(None, position, None, (127,
                                                                                0,
                                                                                0), 5, 0.25, size=2.0)
    return


def shoot_bullet(shooter, position, orientation, damage, penetration, affect_shooter, random_seed):
    scene = shooter.scene
    if shooter.main:
        scene.send_shoot_packet(shooter.parent, position, orientation, damage, penetration, affect_shooter, random_seed)
    scenery_hit = scene.world.hitscan(position, orientation)
    if scenery_hit is not None:
        scenery_hit_position, face = scenery_hit
        scene.media.play_pitched(BULLET_HIT_SCENERY_SOUND, 1.0, (scenery_hit_position.x, scenery_hit_position.y, scenery_hit_position.z))
    return

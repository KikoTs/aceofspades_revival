from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from aoslib.shaders import *
from aoslib.draw import DisplayList
from pyglet.gl import *
from shared.constants import *
from aoslib import media, strings
from aoslib.animations.animThrowGrenade import *

class StickyGrenadeWeapon(Weapon):
    name = strings.STICKY_GRENADE
    damage = None
    sight = None
    shoot_sound = None
    tracer = None
    model = [STICKY_GRENADE_MODEL]
    model_size = 0.04
    view_model_size = 0.04
    view_model = [STICKY_GRENADE_VIEW_MODEL]
    ammo = (A1677, A1678, None, None, A1679)
    shoot_interval = A1680
    image = TOOL_IMAGES[STICKY_GRENADE_TOOL]
    delay = True
    empty_fire_sound_ready = True
    show_crosshair = HAS_AMMO_CROSSHAIR
    show_crosshair_centre = True
    accuracy_spread_min = A1690
    accuracy_spread = accuracy_spread_min
    accuracy_spread_max = accuracy_spread_min + A1691
    accuracy_spread_increase_per_shot = A1692
    accuracy_spread_reduction_speed = A1693
    charge = 0
    can_shoot_primary_while_sprinting = True

    def __init__(self, character):
        super(StickyGrenadeWeapon, self).__init__(character)
        self.animations['throw_grenade'] = AnimThrowGrenade(A1681, stop_on_end=False)
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(0.0, 0.1, 0.0)
                self.reset_position(model_index)

        self.arms_position_offset = Vector3(0.0, -0.1, 0.0)
        self.set_equipped_tool_tip_text(strings.EQUIPPED_TOOL_TIP_GRENADE)

    def can_shoot_primary(self):
        if self.is_active():
            return False
        else:
            return super(StickyGrenadeWeapon, self).can_shoot_primary()

    def can_shoot_secondary(self):
        if self.is_active():
            return False
        else:
            return super(StickyGrenadeWeapon, self).can_shoot_secondary()

    def can_display(self):
        if not super(StickyGrenadeWeapon, self).can_display():
            return False
        else:
            return not self.character.is_sprinting()

    def update(self, dt):
        if self.animations['throw_grenade'] and self.animations['throw_grenade'].is_playing():
            if self.character.is_sprinting():
                self.animations['throw_grenade'].timer = A1681
            self.charge = 1.0 - self.animations['throw_grenade'].timer / A1681
        else:
            self.charge = 0.0
        if not self.character.can_shoot_primary():
            self.empty_fire_sound_ready = True
        return super(StickyGrenadeWeapon, self).update(dt)

    def use_primary(self):
        if self.get_has_enough_ammo():
            character = self.character
            character.shoot_primary = False
            if character.main:
                self.use_an_ammo()
                self.update_ammo()
            self.play_sound(A2927, zone=media.IN_WORLD_AUDIO_ZONE)
            character.throw_stickygrenade(self.charge)
            self.shoot_delay = self.shoot_interval

    def on_stop_primary(self):
        super(StickyGrenadeWeapon, self).on_stop_primary()
        shot = False
        if self.animations['throw_grenade'].is_playing():
            if self.character.is_sprinting():
                shot = False
            else:
                self.use_primary()
            self.animations['throw_grenade'].stop()
            shot = True
        return shot

    def on_start_primary(self):
        if not self.get_has_enough_ammo() or not self.empty_fire_sound_ready:
            if not self.get_has_enough_ammo() and self.character is not None and self.character.main:
                self.character.auto_switch_tool(self)
            if self.empty_fire_sound_ready:
                self.empty_fire_sound_ready = False
        else:
            super(StickyGrenadeWeapon, self).on_start_primary()
            self.animations['throw_grenade'].start()
            self.play_sound(A2928, zone=media.IN_WORLD_AUDIO_ZONE)
        return

    def on_unset(self):
        super(StickyGrenadeWeapon, self).on_unset()
        self.charge = 0.0
        if self.animations['throw_grenade']:
            self.animations['throw_grenade'].stop()
        self.active_primary = False
        self.active_secondary = False

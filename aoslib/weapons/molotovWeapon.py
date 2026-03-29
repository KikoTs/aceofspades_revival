from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from aoslib.shaders import *
from aoslib.draw import DisplayList
from pyglet.gl import *
from shared.constants import *
from aoslib import media, strings
from aoslib.animations.animThrowGrenade import *

class MolotovWeapon(Weapon):
    name = strings.MOLOTOV_TOOL
    damage = None
    sight = None
    shoot_sound = None
    tracer = None
    model = [MOLOTOV_MODEL]
    model_size = 1.3 * BODY_PARTS_SIZE * 0.666
    view_model = [MOLOTOV_VIEW_MODEL]
    ammo = (A1641, A1642, None, None, A1643)
    shoot_interval = A1644
    image = TOOL_IMAGES[MOLOTOV_TOOL]
    delay = True
    empty_fire_sound_ready = True
    show_crosshair = HAS_AMMO_CROSSHAIR
    show_crosshair_centre = True
    accuracy_spread_min = A1654
    accuracy_spread = accuracy_spread_min
    accuracy_spread_max = accuracy_spread_min + A1655
    accuracy_spread_increase_per_shot = A1656
    accuracy_spread_reduction_speed = A1657
    charge = 0
    can_shoot_primary_while_sprinting = True

    def __init__(self, character):
        super(MolotovWeapon, self).__init__(character)
        self.animations['throw_grenade'] = AnimThrowGrenade(A1645, stop_on_end=False)
        self.set_equipped_tool_tip_text(strings.EQUIPPED_TOOL_TIP_GRENADE)

    def can_shoot_primary(self):
        if self.is_active():
            return False
        else:
            return super(MolotovWeapon, self).can_shoot_primary()

    def can_shoot_secondary(self):
        if self.is_active():
            return False
        else:
            return super(MolotovWeapon, self).can_shoot_secondary()

    def can_display(self):
        if not super(MolotovWeapon, self).can_display():
            return False
        else:
            return not self.character.is_sprinting()

    def update(self, dt):
        if self.animations['throw_grenade'] and self.animations['throw_grenade'].is_playing():
            if self.character.is_sprinting():
                self.animations['throw_grenade'].timer = A1645
            self.charge = 1.0 - self.animations['throw_grenade'].timer / A1645
        else:
            self.charge = 0.0
        if not self.character.can_shoot_primary():
            self.empty_fire_sound_ready = True
        return super(MolotovWeapon, self).update(dt)

    def use_primary(self):
        if self.get_has_enough_ammo():
            character = self.character
            character.shoot_primary = False
            if character.main:
                self.use_an_ammo()
                self.update_ammo()
            self.play_sound(MOLOTOV_THROW_SOUND, zone=media.IN_WORLD_AUDIO_ZONE)
            character.throw_molotov(self.charge)
            self.shoot_delay = self.shoot_interval

    def on_stop_primary(self):
        super(MolotovWeapon, self).on_stop_primary()
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
            super(MolotovWeapon, self).on_start_primary()
            self.animations['throw_grenade'].start()
        return

    def on_unset(self):
        super(MolotovWeapon, self).on_unset()
        self.charge = 0.0
        if self.animations['throw_grenade']:
            self.animations['throw_grenade'].stop()
        self.active_primary = False
        self.active_secondary = False

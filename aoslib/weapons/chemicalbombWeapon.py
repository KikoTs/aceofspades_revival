from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from aoslib.shaders import *
from aoslib.draw import DisplayList
from pyglet.gl import *
from shared.constants import *
from aoslib import media, strings
from aoslib.animations.animThrowGrenade import *

class ChemicalBombWeapon(Weapon):
    name = strings.CHEMICALBOMB
    damage = None
    sight = None
    shoot_sound = A2915
    tracer = None
    model = [CHEMICALBOMB_MODEL]
    model_size = 0.02
    view_model_size = 0.02
    view_model = [CHEMICALBOMB_VIEW_MODEL]
    ammo = (A1658, A1659, None, None, A1660)
    shoot_interval = A1661
    image = TOOL_IMAGES[CHEMICALBOMB_TOOL]
    delay = True
    empty_fire_sound_ready = True
    show_crosshair = HAS_AMMO_CROSSHAIR
    show_crosshair_centre = True
    accuracy_spread_min = A1671
    accuracy_spread = accuracy_spread_min
    accuracy_spread_max = accuracy_spread_min + A1672
    accuracy_spread_increase_per_shot = A1673
    accuracy_spread_reduction_speed = A1674
    charge = 0

    def __init__(self, character):
        super(ChemicalBombWeapon, self).__init__(character)
        self.animations['throw_grenade'] = AnimThrowGrenade(A1662, stop_on_end=False)
        self.set_equipped_tool_tip_text(strings.EQUIPPED_TOOL_TIP_GRENADE)
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(-0.02, 0.2, 0.0)
                self.reset_position(model_index)

        self.arms_position_offset = Vector3(0.02, -0.2, 0.0)

    def can_shoot_primary(self):
        if self.is_active():
            return False
        else:
            return super(ChemicalBombWeapon, self).can_shoot_primary()

    def can_shoot_secondary(self):
        if self.is_active():
            return False
        else:
            return super(ChemicalBombWeapon, self).can_shoot_secondary()

    def can_display(self):
        if not super(ChemicalBombWeapon, self).can_display():
            return False
        else:
            return not self.character.is_sprinting()

    def update(self, dt):
        if self.animations['throw_grenade'] and self.animations['throw_grenade'].is_playing():
            if self.character.is_sprinting():
                self.animations['throw_grenade'].timer = A1662
            self.charge = 1.0 - self.animations['throw_grenade'].timer / A1662
        else:
            self.charge = 0.0
        if not self.character.can_shoot_primary():
            self.empty_fire_sound_ready = True
        return super(ChemicalBombWeapon, self).update(dt)

    def use_primary(self):
        if self.get_has_enough_ammo():
            character = self.character
            character.shoot_primary = False
            if character.main:
                self.use_an_ammo()
                self.update_ammo()
            self.play_sound(A2915, zone=media.IN_WORLD_AUDIO_ZONE)
            character.throw_chemicalbomb(self.charge)
            self.shoot_delay = self.shoot_interval

    def on_stop_primary(self):
        super(ChemicalBombWeapon, self).on_stop_primary()
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
            if self.empty_fire_sound_ready:
                self.empty_fire_sound_ready = False
        else:
            super(ChemicalBombWeapon, self).on_start_primary()
            self.animations['throw_grenade'].start()

    def on_unset(self):
        super(ChemicalBombWeapon, self).on_unset()
        self.charge = 0.0
        if self.animations['throw_grenade']:
            self.animations['throw_grenade'].stop()
        self.active_primary = False
        self.active_secondary = False

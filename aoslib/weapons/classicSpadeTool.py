from diggingTool import DiggingTool
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.animations.animUseSpade import *
from aoslib import strings

class ClassicSpadeTool(DiggingTool):
    name = strings.CLASSIC_SPADE
    model = [SPADE_MODEL]
    view_model = [SPADE_VIEW_MODEL]
    shoot_interval = CLASSIC_SPADE_SHOOT_INTERVAL
    secondary_shoot_interval = 0.8
    delay_secondary = True
    image = TOOL_IMAGES[SPADE_TOOL]
    damage = CLASSIC_SPADE_DAMAGE_AMOUNT
    secondary_damage = CLASSIC_SPADE_SECONDARY_DAMAGE_AMOUNT
    damage_type = SPADE_DAMAGE
    pitch_increase = 40
    has_secondary = True

    def __init__(self, character):
        super(ClassicSpadeTool, self).__init__(character)
        self.set_equipped_tool_tip_text(strings.EQUIPPED_TOOL_TIP_MELEE)

    def can_shoot_primary(self):
        anim = self.animations.get('use_spade', None)
        if self.active_secondary or anim is not None and anim.is_playing():
            return False
        return super(ClassicSpadeTool, self).can_shoot_primary()
        return

    def use_primary(self):
        super(ClassicSpadeTool, self).use_primary()
        self.animations['use_spade'] = AnimUseSpade(self.shoot_interval)
        self.animations['use_spade'].start()
        return self.use_spade(False)

    def use_secondary(self):
        super(ClassicSpadeTool, self).use_secondary()
        use_spade_return = self.use_spade(True, self.secondary_damage)
        self.secondary_shoot_delay = 0
        return use_spade_return

    def is_active(self):
        anim = self.animations.get('use_spade', None)
        return super(ClassicSpadeTool, self).is_active() or anim is not None and anim.is_playing()

    def can_shoot_secondary(self):
        if self.is_active():
            return False
        else:
            return super(ClassicSpadeTool, self).can_shoot_secondary()

    def on_start_secondary(self):
        super(ClassicSpadeTool, self).on_start_secondary()
        self.animations['use_spade'] = AnimUseSpade(self.secondary_shoot_interval)
        self.animations['use_spade'].start()

    def update(self, dt):
        super(ClassicSpadeTool, self).update(dt)
        if self.active_secondary:
            if self.animations['use_spade'] is not None and not self.animations['use_spade'].is_playing():
                self.active_secondary = False
                self.on_stop_secondary()
        return

    def on_stop_secondary(self):
        super(ClassicSpadeTool, self).on_stop_secondary()
        if self.animations['use_spade'] is not None:
            if self.animations['use_spade'].is_playing():
                self.animations['use_spade'].stop()
            else:
                self.use_secondary()
        return

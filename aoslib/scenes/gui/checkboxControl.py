from pyglet import gl
from aoslib.gui import Checkbox
from aoslib.draw import draw_quad
from aoslib.images import global_images
from shared.hud_constants import CHECKBOX_BORDER_COLOUR, CHECKBOX_DISABLED_BORDER_COLOUR, CHECKBOX_BORDER_SIZE, CHECKBOX_INNER_COLOUR

class CheckboxControl(Checkbox):

    def initialize(self, value, x, y, size=32):
        self.image_scale_x = 1.0
        self.image_scale_y = 1.0
        self.tick_scale_x = 1.0
        self.tick_scale_y = 1.0
        super(CheckboxControl, self).initialize(value, x, y, size)

    def update_position(self, x, y):
        self.x1 = x - self.size / 2.0
        self.x2 = self.x1 + self.size
        self.y1 = y - self.size / 2.0
        self.y2 = self.y1 + self.size
        self.image_scale_x = float(self.size) / float(global_images.checkbox_background.width)
        self.image_scale_y = float(self.size) / float(global_images.checkbox_background.height)
        self.tick_scale_x = float(self.size - CHECKBOX_BORDER_SIZE) / float(global_images.checkmark.width)
        self.tick_scale_y = float(self.size) / float(global_images.checkmark.height)

    def draw(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        x = self.x1 + self.size / 2.0
        y = self.y1 + self.size / 2.0
        if self.enabled:
            colour = CHECKBOX_BORDER_COLOUR
        else:
            colour = CHECKBOX_DISABLED_BORDER_COLOUR
        draw_quad(self.x1, self.y1, self.size, self.size, colour)
        draw_quad(self.x1 + CHECKBOX_BORDER_SIZE, self.y1 + CHECKBOX_BORDER_SIZE, self.size - CHECKBOX_BORDER_SIZE * 2, self.size - CHECKBOX_BORDER_SIZE * 2, CHECKBOX_INNER_COLOUR)
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        if self.enabled and self.value:
            gl.glPushMatrix()
            gl.glTranslatef(self.x1 + CHECKBOX_BORDER_SIZE, self.y1 + CHECKBOX_BORDER_SIZE / 2, 0)
            gl.glScalef(self.tick_scale_x, self.tick_scale_y, 0.0)
            global_images.checkmark.blit(0, 0)
            gl.glPopMatrix()

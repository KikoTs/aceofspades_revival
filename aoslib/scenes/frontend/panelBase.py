from aoslib.scenes import Scene, ElementScene, MenuScene
from aoslib.images import global_images
from aoslib.text import draw_text_with_alignment_and_size_validation, title_font, hc_font, small_aldo_ui_font, medium_aldo_ui_font, big_edo_ui_font
from aoslib.draw import draw_quad
from shared.constants import MENU_FONT_COLOR
from shared.hud_constants import LIST_PANEL_SPACING, TEXT_BACKGROUND_SPACING
from pyglet import gl
BACKGROUND_NONE, BACKGROUND_WITH_IMAGE, BACKGROUND_WITH_BOX = xrange(3)

class PanelBase(MenuScene):

    def initialize(self):
        super(PanelBase, self).initialize()
        self.frame_image = None
        self.title = None
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.title_width = None
        self.title_height = 40
        self.has_header = False
        self.center_header_text = False
        self.visible_content = True
        self.draw_background = False
        self.set_background()
        self.visible = True
        self.frame_padding_width = 0
        self.frame_padding_height = 0
        self.frame_padding_offset_y = 0
        self.frame_padding_offset_x = 0
        return

    def set_background(self, background=BACKGROUND_WITH_IMAGE, background_colour=(0, 0, 0, 255)):
        self.background_colour = background_colour
        if background == BACKGROUND_WITH_IMAGE:
            self.frame_image = global_images.panel_frame
            self.draw_background = True
        elif background == BACKGROUND_NONE:
            self.draw_background = False
            self.frame_image = None
        else:
            self.draw_background = True
            self.frame_image = None
        return

    def initialise_ui(self, title, x, y, width, height, has_header=False):
        self.elements = []
        self.title = title
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.original_height = height
        self.scale_x = float(self.width) / float(global_images.panel_frame.width)
        self.scale_y = float(self.height) / float(global_images.panel_frame.height)
        self.has_header = has_header

    def set_content_visibility(self, visible):
        self.visible_content = visible

    def draw_header_frame(self, x, y, width, height, frame=global_images.settings_matchsettings_frame):
        if frame is None:
            return
        else:
            title_scale_x = float(width) / float(frame.width)
            title_scale_y = float(height) / float(frame.height)
            gl.glPushMatrix()
            gl.glTranslatef(x, y, 0)
            gl.glScalef(title_scale_x, title_scale_y, 0.0)
            frame.blit(0, 0)
            gl.glPopMatrix()
            return

    def draw_text(self, x, y, width, height, title=None, font=hc_font, center_text=False):
        if title is None:
            return
        else:
            alignment_x = 'center' if center_text else 'left'
            draw_text_with_alignment_and_size_validation(title, x, y, width, height, MENU_FONT_COLOR, font, alignment_x, alignment_y='center')
            return

    def draw_background_frame(self):
        if self.draw_background == False:
            return
        else:
            if self.frame_image is None:
                x = self.x - self.frame_padding_width / 2 + self.frame_padding_offset_x
                y = self.y - self.frame_padding_height - self.height + self.frame_padding_offset_y
                width = self.width + self.frame_padding_width
                height = self.height + self.frame_padding_height
                draw_quad(x, y, width, height, self.background_colour)
            else:
                x = self.x + self.width / 2
                y = self.y - self.height / 2
                gl.glColor4f(1.0, 1.0, 1.0, 1.0)
                gl.glPushMatrix()
                gl.glTranslatef(x, y, 0)
                gl.glScalef(self.scale_x, self.scale_y, 0.0)
                global_images.panel_frame.blit(0, 0)
                gl.glPopMatrix()
            return

    def draw_header(self, title=None):
        spacing = LIST_PANEL_SPACING
        x = self.x + spacing
        y = self.y - spacing
        width = self.width - spacing * 2
        height = self.title_height
        frame_x = x + width / 2
        frame_y = y - height / 2
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        self.draw_header_frame(frame_x, frame_y, width, self.title_height)
        font = big_edo_ui_font
        if self.title_width is None:
            text_width = width - TEXT_BACKGROUND_SPACING * 2
        else:
            text_width = self.title_width
        self.draw_text(x + TEXT_BACKGROUND_SPACING, y - height, text_width, height, title, font, self.center_header_text)
        return

    def get_header_font(self):
        return big_edo_ui_font

    def draw(self):
        if self.visible == False:
            return
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        self.draw_background_frame()
        if self.has_header:
            self.draw_header(self.title)

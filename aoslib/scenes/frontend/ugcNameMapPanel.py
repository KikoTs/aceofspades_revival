from aoslib.scenes.frontend.panelBase import PanelBase
from aoslib.scenes.gui.editBoxControl import EditBoxControl
from aoslib import strings
from aoslib.ugc_data import get_ugc_path, get_ugc_subscribed_path
from aoslib.image import load_image_from_path
from shared.hud_constants import LIST_PANEL_SPACING
from pyglet import gl

class UGCNameMapPanel(PanelBase):

    def initialize(self):
        super(UGCNameMapPanel, self).initialize()
        self.edit_box_control = None
        self.image = None
        self.image_scale_x = 1.0
        self.image_scale_y = 1.0
        self.set_background()
        return

    def initialise_ui(self, map_name, image, x, y, width, height, edit_box_height=30):
        super(UGCNameMapPanel, self).initialise_ui(strings.NAME_MAP, x, y, width, height, has_header=True)
        self.image = image
        self.name = map_name
        self.filename = ''
        edit_box_height = edit_box_height
        edit_box_y = self.y - self.title_height - edit_box_height - LIST_PANEL_SPACING * 2
        edit_box_width = self.width - LIST_PANEL_SPACING * 2
        self.image_y = edit_box_y - LIST_PANEL_SPACING
        self.image_height = self.height - self.title_height - edit_box_height - LIST_PANEL_SPACING * 4
        self.edit_box_control = EditBoxControl(map_name, self.x + LIST_PANEL_SPACING, edit_box_y, edit_box_width, edit_box_height, center=False)
        self.elements.append(self.edit_box_control)

    def set_map_name(self, name):
        self.name = name
        if self.edit_box_control is not None:
            self.edit_box_control.set(name)
        return

    def set_content_visibility(self, visible):
        self.visible = visible
        self.enabled = visible
        if self.edit_box_control is not None:
            self.edit_box_control.enabled = visible
        if visible:
            self.__load_image()
        else:
            self.reset_image()
        return

    def reset_image(self):
        if self.image is not None:
            self.image = None
        return

    def __load_image(self):
        if self.image is not None:
            return
        else:
            image_path = get_ugc_path(self.filename, 'png')
            self.image = load_image_from_path(image_path, True, silent=True)
            if not self.image:
                image_path = get_ugc_subscribed_path(self.name, 'png')
                self.image = load_image_from_path(image_path, True, silent=True)
            if self.image is not None:
                self.image_scale_x = float(self.width - LIST_PANEL_SPACING * 2) / float(self.image.width)
                self.image_scale_y = float(self.image_height) / float(self.image.height)
            return

    def draw(self):
        if self.visible == False:
            return
        else:
            super(UGCNameMapPanel, self).draw()
            if self.image is not None:
                gl.glColor4f(1.0, 1.0, 1.0, 1.0)
                gl.glPushMatrix()
                gl.glTranslatef(self.x + LIST_PANEL_SPACING, self.image_y - self.image_height, 0)
                gl.glScalef(self.image_scale_x, self.image_scale_y, 0.0)
                self.image.blit(0, 0)
                gl.glPopMatrix()
            for element in self.elements:
                element.draw()

            return

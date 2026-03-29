from aoslib.gui import HandlerBase
from aoslib.images import global_images
from aoslib.gui import TextButton
from aoslib import strings
from aoslib.text import big_standard_ui_font, medium_standard_ui_font, get_resized_font_and_formatted_text_to_fit_boundaries, draw_text_lines
from pyglet import gl
from shared.constants import MENU_FONT_COLOR
from shared.hud_constants import TEXT_BACKGROUND_SPACING
from shared.steam import SteamShowWebPage
DIALOG_INFORMATION, DIALOG_WITH_BUTTONS, DIALOG_EXTENDED = xrange(3)
BUTTONS_NONE, BUTTONS_OK, BUTTONS_OK_CANCEL, BUTTONS_YES_NO, BUTTONS_RETRY_CANCEL = xrange(5)

class MessageBox(HandlerBase):

    def initialize(self, x, y, message_text=None, extended_message_text=None):
        self.elements = []
        self.frame_spacing = 40
        self.visible = False
        self.x = x
        self.y = y
        self.width = global_images.message_box_frame.width
        self.height = global_images.message_box_frame.height
        self.set_dialog_message_type(DIALOG_INFORMATION, BUTTONS_NONE, message_text, extended_message_text)
        self.mouse_over_extended_text = False

    def set_buttons_callback(self, button_one_callback, button_two_callback=None):
        self.button_one_callback = button_one_callback
        self.button_two_callback = button_two_callback

    def set_visible(self, visible):
        self.visible = visible

    def set_dialog_message_type(self, dialog_type, buttons_type, text=None, extended_text=None):
        self.dialog_type = dialog_type
        if dialog_type == DIALOG_WITH_BUTTONS:
            self.background = global_images.message_box_with_buttons_frame
        elif dialog_type == DIALOG_EXTENDED:
            self.background = global_images.message_box_extended_frame
        else:
            self.background = global_images.message_box_frame
        self.__set_buttons_type(buttons_type)
        self.__set_text(text, extended_text)

    def __set_text(self, message_text, extended_message_text=None):
        self.text = message_text
        self.extended_text = extended_message_text
        if self.dialog_type == DIALOG_EXTENDED:
            self.text_y = self.y + self.height * 0.5 - self.frame_spacing - TEXT_BACKGROUND_SPACING * 2
        else:
            if self.dialog_type == DIALOG_WITH_BUTTONS:
                frame_height_diff = global_images.message_box_extended_frame.height - global_images.message_box_with_buttons_frame.height
            else:
                frame_height_diff = global_images.message_box_extended_frame.height - global_images.message_box_frame.height
            self.text_y = self.y + self.height * 0.5 - self.frame_spacing - TEXT_BACKGROUND_SPACING - frame_height_diff
        self.text_x = self.x - self.width * 0.5 + self.frame_spacing + TEXT_BACKGROUND_SPACING
        self.text_width = self.width - self.frame_spacing * 2 - TEXT_BACKGROUND_SPACING * 2
        self.text_height = self.height - TEXT_BACKGROUND_SPACING * 2 - self.frame_spacing * 2
        self.extended_text_y = self.y - self.height * 0.5 - self.text_height * 0.5
        if self.text is not None:
            self.text_font, self.text_lines = get_resized_font_and_formatted_text_to_fit_boundaries(self.text, self.text_width, self.text_height, big_standard_ui_font, 2, True)
        else:
            self.text_font = None
            self.text_lines = None
        if self.extended_text is not None:
            self.extended_text_font, self.extended_lines = get_resized_font_and_formatted_text_to_fit_boundaries(self.extended_text, self.text_width, self.text_height, medium_standard_ui_font, 2, True)
        else:
            self.extended_text_font = None
            self.extended_lines = None
        return

    def __set_buttons_type(self, buttons_type):
        self.button_one = None
        self.button_two = None
        del self.elements[:]
        if buttons_type == BUTTONS_NONE or self.dialog_type == DIALOG_INFORMATION:
            return
        font_size = 18
        height = 50
        width = self.width / 3
        spacing = width / 3
        x1 = self.x - self.width * 0.5 + spacing
        x2 = x1 + spacing + width
        y = self.y - self.height * 0.5
        if self.dialog_type == DIALOG_EXTENDED:
            y += self.height / 3 - 4
        elif self.dialog_type == DIALOG_WITH_BUTTONS:
            frame_height_diff = global_images.message_box_extended_frame.height - global_images.message_box_with_buttons_frame.height
            y += self.height * 0.25 - frame_height_diff * 0.5 + TEXT_BACKGROUND_SPACING
        else:
            y += self.height * 0.25
        if buttons_type == BUTTONS_OK:
            x1 = self.x - width * 0.5
            self.button_one = TextButton(strings.OK, x1, y, width, height, font_size)
        elif buttons_type == BUTTONS_OK_CANCEL:
            self.button_one = TextButton(strings.OK, x1, y, width, height, font_size)
            self.button_two = TextButton(strings.CANCEL, x2, y, width, height, font_size)
        elif buttons_type == BUTTONS_YES_NO:
            self.button_one = TextButton(strings.KICK_YES, x1, y, width, height, font_size)
            self.button_two = TextButton(strings.KICK_NO, x2, y, width, height, font_size)
        elif buttons_type == BUTTONS_RETRY_CANCEL:
            self.button_one = TextButton(strings.RETRY, x1, y, width, height, font_size)
            self.button_two = TextButton(strings.CANCEL, x2, y, width, height, font_size)
        callbacks = [self.button_one_callback, self.button_two_callback]
        for index, button in enumerate([self.button_one, self.button_two]):
            if button is not None:
                self.elements.append(button)
                button.add_handler(callbacks[index])

        return

    def draw(self):
        if self.visible == False:
            return
        else:
            if self.background is not None:
                gl.glColor4f(1.0, 1.0, 1.0, 1.0)
                gl.glPushMatrix()
                gl.glTranslatef(self.x, self.y, 0)
                gl.glScalef(1.0, 1.0, 0.0)
                self.background.blit(0, 0)
                gl.glPopMatrix()
            if self.text_lines is not None and len(self.text_lines) > 0:
                draw_text_lines(self.text_lines, self.text_x, self.text_y, self.text_width, self.text_height, self.text_font, 10.0, MENU_FONT_COLOR, 'center', 'center')
            if self.extended_lines is not None and len(self.extended_lines) > 0:
                colour = MENU_FONT_COLOR if self.mouse_over_extended_text else (0, 0, 255, 255)
                draw_text_lines(self.extended_lines, self.text_x, self.extended_text_y - TEXT_BACKGROUND_SPACING - 4, self.text_width, self.text_height, self.extended_text_font, 2.0, colour, 'center', 'center')
            for element in self.elements:
                element.draw()

            return

    def on_mouse_press(self, x, y, button, modifiers):
        if self.visible:
            for element in self.elements:
                element.on_mouse_press(x, y, button, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.visible:
            for element in self.elements:
                element.on_mouse_motion(x, y, dx, dy)

            if self.extended_lines is None or len(self.extended_lines) == 0:
                self.mouse_over_extended_text = False
            else:
                self.mouse_over_extended_text = x >= self.text_x - self.frame_spacing and x <= self.text_x + self.text_width + self.frame_spacing and y >= 145 and y <= 180
        return

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        if self.visible:
            for element in self.elements:
                element.on_mouse_drag(x, y, dx, dy, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        if self.visible:
            for element in self.elements:
                element.on_mouse_release(x, y, button, modifiers)

            if self.mouse_over_extended_text:
                SteamShowWebPage('http://steamcommunity.com/sharedfiles/workshoplegalagreement')

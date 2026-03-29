from aoslib.scenes.frontend.listPreviewMenuBase import ListPreviewMenuBase
from aoslib.scenes.frontend.ugcMapPreviewPanel import UGCMapPreviewPanel
from aoslib.scenes.frontend.ugcMapsListPanel import UGCMapsListPanel
from aoslib.scenes.frontend.ugcNameMapPanel import UGCNameMapPanel
from aoslib.scenes.frontend.ugcPublishedMapsPanel import UGCPublishedMapsPanel
from aoslib.scenes.main.ugcMapListItem import UGCMapListItem
from aoslib.scenes.gui.messageBox import *
from aoslib.images import global_images
from pyglet import gl
from aoslib import strings
from aoslib.ugc_data import ugc_data, delete_ugc_file
from shared.hud_constants import UI_CONTROL_SPACING
from shared.steam import SteamShowWebPage, SteamActivateGameOverlayToStore
from shared.constants import SPADES_GAME_APP_ID
from aoslib.media import HUD_AUDIO_ZONE
PANEL_PREVIEW_MAP_INFO, PANEL_MAP_LIST, PANEL_NAME_MAP, PANEL_PUBLISHED_MAPS = xrange(4)
MSG_TYPE_NONE, MSG_TYPE_UPLOADING, MSG_TYPE_UPLOAD_CONFIRMATION, MSG_TYPE_ERROR_UPLOADING, MSG_TYPE_DELETED_FILE, MSG_TYPE_DELETE_MAP_CONFIRMATION = xrange(6)

class UGCPublishMenu(ListPreviewMenuBase):
    title = strings.PUBLISH

    def initialize(self):
        super(UGCPublishMenu, self).initialize(self.title)
        self.__initialise_panels()
        self.button_height = 50
        self.last_selected_filter_index = 0
        self.button_background_x = 0
        self.button_background_y = 0
        self.button_background_scale_x = 1.0
        self.button_background_scale_y = 1.0
        self.message_box_type = MSG_TYPE_NONE
        self.message_box = MessageBox(400, 300)
        self.message_box.set_buttons_callback(self.message_box_button_one_pressed, self.message_box_button_two_pressed)

    def __initialise_panels(self):
        self.ugc_maps_panel = UGCMapsListPanel(self.manager)
        self.preview_panel = UGCMapPreviewPanel(self.manager)
        self.ugc_name_map_panel = UGCNameMapPanel(self.manager)
        self.ugc_published_maps_panel = UGCPublishedMapsPanel(self.manager)
        self.panels = {PANEL_PREVIEW_MAP_INFO: (self.preview_panel), 
           PANEL_MAP_LIST: (self.ugc_maps_panel), 
           PANEL_NAME_MAP: (self.ugc_name_map_panel), 
           PANEL_PUBLISHED_MAPS: (self.ugc_published_maps_panel)}

    def on_start(self, *arg, **kw):
        self.elements = []
        self.buttons = []
        self.elements.append(self.navigation_bar)
        self.elements.append(self.message_box)
        for id, panel in self.panels.iteritems():
            self.elements.append(panel)

        button_y = 144
        panel_width = 340
        self.buy_now_button = self.create_button(strings.BUY_NOW, 405, button_y, panel_width - UI_CONTROL_SPACING * 2, self.button_height, 18, self.on_buy_now)
        self.buy_now_button.tint = (0.2, 1.0, 0.2)
        self.buy_now_button.text_colour = (255, 255, 255, 255)
        self.buy_now_button.enabled = False
        self.publish_button = self.create_button(strings.UGC_PREVIEW_PUBLISH, 405, button_y, panel_width - UI_CONTROL_SPACING * 2, self.button_height, 18, self.on_publish_button_clicked)
        self.publish_button.enabled = False
        self.ugc_maps_panel.initialise_ui(56, 505, panel_width, 413, self.on_ugc_map_selected)
        self.ugc_name_map_panel.initialise_ui('', None, 56, 505, panel_width, 413)
        self.preview_panel.initialise_ui(None, 401, 505, panel_width, 354)
        self.ugc_published_maps_panel.initialise_ui(401, 505, panel_width, 354, self.on_ugc_published_map_selected, self.on_ugc_published_map_unselected)
        self.preview_panel.add_delete_button(self.on_delete_button_callback)
        self.preview_panel.delete_button.visible = self.ugc_maps_panel.maps_list.get_selected_item() is not None
        initial_visible_panels = [
         PANEL_MAP_LIST, PANEL_PREVIEW_MAP_INFO]
        for id, panel in self.panels.iteritems():
            if panel is not None:
                panel.set_content_visibility(id in initial_visible_panels)

        button_y = self.publish_button.y
        button_height = self.publish_button.height
        button_background_height = button_height + 4.0
        self.button_background_x = self.preview_panel.x + self.preview_panel.width / 2.0
        self.button_background_y = button_y - button_height - 1 + button_background_height / 2.0 + 1
        self.button_background_scale_x = float(self.preview_panel.width) / float(global_images.panel_frame.width)
        self.button_background_scale_y = float(button_background_height) / float(global_images.panel_frame.height)
        self.show_message_box(MSG_TYPE_NONE, False)
        return

    def on_stop(self):
        for id, panel in self.panels.iteritems():
            panel.close()

    def on_buy_now(self):
        self.media.play('menu_buyA', zone=HUD_AUDIO_ZONE)

    def set_panel_visibility(self, panel_id, visible):
        if self.panels[panel_id] is not None:
            self.panels[panel_id].set_content_visibility(visible)
        return

    def on_delete_button_callback(self):
        row = self.ugc_maps_panel.maps_list.get_selected_item()
        if row is None:
            return
        else:
            if self.media:
                self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
            map_name = row.name
            text = strings.UGC_DELETE_MAP_CONFIMATION + '\n' + map_name
            self.show_message_box(MSG_TYPE_DELETE_MAP_CONFIRMATION, True, text, None, DIALOG_WITH_BUTTONS, BUTTONS_YES_NO)
            return

    def delete_selected_map(self):
        row = self.ugc_maps_panel.maps_list.get_selected_item()
        if row is None:
            self.show_message_box(MSG_TYPE_NONE, False)
            return
        else:
            delete_ugc_file(row.uid)
            self.show_message_box(MSG_TYPE_DELETED_FILE, True, strings.UGC_MAP_DELETED_SUCCESSFULLY, None, DIALOG_WITH_BUTTONS, BUTTONS_OK)
            return

    def refresh_ui_on_map_deleted(self):
        self.show_message_box(MSG_TYPE_NONE, False)
        self.preview_panel.clear_display_data()
        self.ugc_maps_panel.populate_list()
        if self.ugc_name_map_panel.visible:
            self.publish_button.set_text(strings.UGC_PREVIEW_PUBLISH)
            self.set_panel_visibility(PANEL_MAP_LIST, True)
            self.set_panel_visibility(PANEL_NAME_MAP, False)
        self.update_publish_button_state()

    def update_publish_button_state(self):
        row = self.ugc_maps_panel.maps_list.get_selected_item()
        if row is None:
            self.publish_button.enabled = False
        else:
            self.publish_button.enabled = len(row.publishable_modes) > 0
        return

    def on_publish_button_clicked(self):
        if self.ugc_maps_panel.visible:
            if self.media:
                self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
            self.publish_button.set_text(strings.PUBLISH)
            self.set_panel_visibility(PANEL_MAP_LIST, False)
            self.set_panel_visibility(PANEL_NAME_MAP, True)
        elif self.ugc_name_map_panel.visible:
            if self.media:
                self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
            self.show_message_box(MSG_TYPE_UPLOAD_CONFIRMATION, True, strings.UGC_PUBLISH_CONFIRMATION, strings.STEMWORKS_LICENSE_MESSAGE, DIALOG_EXTENDED, BUTTONS_YES_NO)

    def publish_finished_callback(self, success):
        if success:
            self.show_message_box(MSG_TYPE_NONE, False)
            from selectMenu import SelectMenu
            self.parent.set_menu(SelectMenu, back=True)
            SteamShowWebPage('http://steamcommunity.com/workshop/browse/?appid=224540')
        else:
            self.show_message_box(MSG_TYPE_ERROR_UPLOADING, True, strings.UGC_UPLOAD_ERROR, None, DIALOG_WITH_BUTTONS, BUTTONS_OK)
        return

    def show_message_box(self, message_type, show, text=None, extended_text=None, dialog_type=DIALOG_INFORMATION, buttons_type=BUTTONS_NONE):
        self.message_box_type = message_type
        if show:
            self.publish_button.enabled = False
        else:
            self.update_publish_button_state()
        self.navigation_bar.enabled = not show
        for id, panel in self.panels.iteritems():
            if panel.visible:
                panel.enabled = not show

        if show:
            self.message_box.set_dialog_message_type(dialog_type, buttons_type, text, extended_text)
        self.message_box.set_visible(show)

    def message_box_button_one_pressed(self):
        if self.media:
            self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        if self.message_box_type == MSG_TYPE_UPLOAD_CONFIRMATION:
            self.show_message_box(MSG_TYPE_UPLOADING, True, strings.UGC_UPLOADING_MAP_MESSAGE, None, DIALOG_INFORMATION, BUTTONS_NONE)
            ugc_title = self.ugc_name_map_panel.edit_box_control.value
            if self.preview_panel.filename != None:
                filename_to_publish = self.preview_panel.filename
                ugc_data_to_publish = ugc_data(network=None, local_filename=filename_to_publish)
                ugc_data_to_publish.publish(self.publish_finished_callback, ugc_title=ugc_title)
            else:
                print 'Unable to publish as row filename was not set'
        elif self.message_box_type == MSG_TYPE_ERROR_UPLOADING:
            self.show_message_box(MSG_TYPE_NONE, False)
        elif self.message_box_type == MSG_TYPE_DELETE_MAP_CONFIRMATION:
            self.delete_selected_map()
        elif self.message_box_type == MSG_TYPE_DELETED_FILE:
            self.refresh_ui_on_map_deleted()
        return

    def message_box_button_two_pressed(self):
        if self.media:
            self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
        if self.message_box_type == MSG_TYPE_UPLOAD_CONFIRMATION:
            self.show_message_box(MSG_TYPE_NONE, False)
        elif self.message_box_type == MSG_TYPE_DELETE_MAP_CONFIRMATION:
            self.show_message_box(MSG_TYPE_NONE, False)
            self.update_publish_button_state()

    def on_ugc_map_selected(self, index, row):
        if row is None:
            return
        else:
            self.preview_panel.title = row.name
            self.preview_panel.filename = row.uid
            self.preview_panel.populate_list(row.publishable_modes, row.unpublishable_modes)
            self.publish_button.enabled = len(row.publishable_modes) > 0
            self.ugc_name_map_panel.set_map_name(row.name)
            self.ugc_name_map_panel.filename = row.uid
            return

    def on_ugc_published_map_selected(self, index, row):
        if row is None:
            return
        else:
            self.publish_button.set_text(strings.OVERWRITE)
            return

    def on_ugc_published_map_unselected(self, index, row):
        if row is None:
            return
        else:
            self.publish_button.set_text(strings.PUBLISH)
            return

    def back_pressed(self, is_back):
        if is_back and self.ugc_name_map_panel.visible:
            if self.media:
                self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
            self.title = strings.PUBLISH
            self.publish_button.set_text(strings.UGC_PREVIEW_PUBLISH)
            self.set_panel_visibility(PANEL_PREVIEW_MAP_INFO, True)
            self.set_panel_visibility(PANEL_MAP_LIST, True)
            self.set_panel_visibility(PANEL_NAME_MAP, False)
            self.set_panel_visibility(PANEL_PUBLISHED_MAPS, False)
        else:
            self.title = strings.UGC_MENU_PUBLISH_MAP
            super(UGCPublishMenu, self).back_pressed(is_back)

    def open_parent_menu(self):
        from aoslib.scenes.frontend.ugcSelectMenu import UGCSelectMenu
        self.parent.set_menu(UGCSelectMenu, back=True)

    def draw_buttons_background(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        gl.glPushMatrix()
        gl.glTranslatef(self.button_background_x, self.button_background_y, 0)
        gl.glScalef(self.button_background_scale_x, self.button_background_scale_y, 0.0)
        global_images.panel_frame.blit(0, 0)
        gl.glPopMatrix()

    def draw_elements(self):
        for element in self.elements:
            if element == self.message_box:
                continue
            element.draw()

        self.message_box.draw()

    def draw(self):
        self.draw_buttons_background()
        super(UGCPublishMenu, self).draw()

from aoslib.scenes import Scene, ElementScene, MenuScene
from aoslib.common import wave, collides
from shared.constants import *
from shared.hud_constants import *
from shared.common import clamp
from aoslib.text import title_font, settings_font, settings_changed_font, Label, draw_text_with_size_validation, draw_text_with_alignment_and_size_validation, ammo_font, reserve_font, medium_standard_ui_font, medium_edo_ui_font, small_standard_ui_font
from aoslib.gui import TextButton, VerticalScrollBar
from aoslib.scenes.gui.dropBoxControl import DropBoxControl
from aoslib.scenes.frontend.listPanelBase import ListPanelBase
from aoslib.scenes.main.listPanelItemBase import ListPanelItemBase
from aoslib.scenes.frontend.panelBase import BACKGROUND_NONE
from aoslib.images import global_images
from pyglet import gl
from aoslib import strings
from aoslib.media import MUSIC_AUDIO_ZONE, HUD_AUDIO_ZONE
from shared.steam import SteamShowAchievements, SteamActivateGameOverlayToStore, GetUserSteamID
from aoslib.weapons.list import WEAPONS
from aoslib.draw import draw_quad
from aoslib.scenes.frontend.tabBase import TabBase
from aoslib.scoremanager import ScoreManager
from shared.constants_playerprofile import *
from shared.playerStat import PlayerStat
from aoslib.scenes.frontend.playerProfileListItems import *
from shared.steam import SteamIsLoggedOn

class WeaponStat:
    shots = 0
    hits = 0
    accuracy = 0.0
    points = 0


class PlayerStatsTab(TabBase):

    def __init__(self):
        self.filters = [
         strings.SUMMARY]
        self.current_filter = None
        return


class EquipmentStatsTab(TabBase):

    def __init__(self):
        self.filters = [
         strings.WEAPON_ACCURACY, strings.WEAPON_POINTS]
        self.current_filter = None
        return


class ClassesStatsTab(TabBase):

    def __init__(self):
        self.filters = [
         strings.SOLDIER, strings.SCOUT, strings.ENGINEER2, strings.MINER, strings.SPECIALIST, strings.MEDIC, strings.GANGSTER, strings.CLASSIC, strings.ZOMBIE]
        self.current_filter = None
        return


class GameModesStatsTab(TabBase):

    def __init__(self):
        self.filters = [
         strings.GENERAL, strings.TDM_TITLE, strings.VIP_MODE_TITLE, strings.OCCUPATION_MODE_TITLE, strings.TC_TITLE, strings.DIAMOND_MINE_TITLE, strings.CTF_TITLE, strings.ZOMBIE_MODE_TITLE, strings.DEMOLITION_TITLE, strings.MULTIHILL_TITLE, strings.HOURS_PLAYED]
        self.current_filter = None
        return


class PlayerProfileSummaryListPanel(ListPanelBase):

    def initialize(self):
        super(PlayerProfileSummaryListPanel, self).initialize()
        self.first_item_y_offset = PLAYER_PROFILE_SUMMARY_REDBAR_GAP

    def set_list_items_position_on_scroll(self, x, y, width):
        if self.min_index == 0:
            min_index_to_render = self.min_index
        else:
            min_index_to_render = self.min_index + 1
        for row_index, row in enumerate(self.rows):
            if row_index > 0 and (row_index < min_index_to_render or row_index >= self.max_index):
                if row.enable_on_scroll:
                    row.set_enabled(False)
            elif row.enable_on_scroll:
                row.set_enabled(True)
            if row_index == 0:
                row.update_position(x, y + self.first_item_y_offset, width, self.row_height, width)
            else:
                row.update_position(x, y, width, self.row_height, width)
            y -= self.row_height + self.line_spacing

    def draw_list_items(self):
        if self.min_index == 0:
            min_index_to_render = self.min_index
        else:
            min_index_to_render = self.min_index + 1
        color_index = 0
        for index, row in enumerate(self.rows):
            if index > 0 and (index < min_index_to_render or index >= self.max_index):
                continue
            row.draw(self.list_items_background_colors[color_index])
            color_index += 1
            if color_index == len(self.list_items_background_colors):
                color_index = 0


class PlayerProfileMenu(MenuScene):
    title = strings.PLAYER_PROFILE
    content_frame = global_images.profile_stats_bg
    tab_active_img = global_images.generic_tab_active
    tab_inactive_img = global_images.generic_tab_inactive

    def on_menu_opened(self):
        font_size = 30
        width = 240
        height = 60
        x = 152
        y = 108
        self.cancel_button = TextButton(strings.CANCEL, x, y, width, height, font_size)
        self.cancel_button.add_handler(self.back_pressed)
        self.elements.append(self.cancel_button)
        self.achievements_button = TextButton(strings.ACHIEVEMENTS, 405, y, width, height, font_size)
        self.achievements_button.add_handler(self.achievements_pressed)
        self.elements.append(self.achievements_button)
        self.manager.score_manager.set_request_profile_callback(self.score_manager_callback)
        self.manager.score_manager.request_profile(GetUserSteamID())
        for tab in self.tabs:
            tab[1].set_in_game_tab(self.in_game_menu)
            self.elements.append(tab[1])

        self.set_tab(0, False)

    def on_start(self, menu=None, tab=-1, **kw):
        self.kd_ratio = 0.0
        self.show_wait_msg = True
        self.show_no_connection = False
        self.profile_data = None
        self.elements = []
        self.filter_drop_box = None
        self.focused_dropbox = None
        self.current_index = 0
        self.list_panel = None
        self.current_tab = None
        self.tab_width = 110.0
        self.tabs_start_x = PLAYER_PROFILE_TABS_START_X
        player_stats_tab = PlayerStatsTab()
        equipment_stats_tab = EquipmentStatsTab()
        classes_stats_tab = ClassesStatsTab()
        game_mode_stats_tab = GameModesStatsTab()
        self.tabs = [
         (
          strings.PLAYER_STATS, player_stats_tab),
         (
          strings.GAME_MODES, game_mode_stats_tab),
         (
          strings.CLASSES, classes_stats_tab),
         (
          strings.EQUIPMENT, equipment_stats_tab)]
        self.setup_categories()
        self.on_menu_opened()
        return

    def on_stop(self):
        self.manager.score_manager.clear_request_profile_callback()

    def update(self, dt):
        super(PlayerProfileMenu, self).update(dt)
        if not SteamIsLoggedOn():
            from aoslib.scenes.frontend.selectMenu import SelectMenu
            self.manager.set_menu(SelectMenu, back=True)

    def on_filter_changed(self, index):
        self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        if index == 0:
            self.current_tab.current_filter = None
            self.populate_stats_list(self.current_tab.filters)
        else:
            self.current_tab.current_filter = self.current_tab.filters[index - 1]
            self.populate_stats_list([self.current_tab.current_filter])
        return

    def on_mouse_press(self, x, y, button, modifiers):
        width = 496
        x1 = self.tabs_start_x - 3
        x2 = x1 + width
        y1 = 467
        y2 = 500
        if collides(x1, y1, x2, y2, x, y, x, y):
            index = int((x - x1) / float(width / len(self.tabs)))
            self.set_tab(index)
            return
        super(PlayerProfileMenu, self).on_mouse_press(x, y, button, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        if not self.enabled:
            return
        else:
            if self.filter_drop_box is not None:
                self.filter_drop_box.on_mouse_motion(x, y, dx, dy)
            for element in self.get_elements():
                if self.filter_drop_box is not None:
                    if element is self.filter_drop_box:
                        continue
                    if element is self.list_panel and self.filter_drop_box.over:
                        continue
                element.on_mouse_motion(x, y, dx, dy)

            return

    def on_mouse_scroll(self, x, y, dx, dy):
        if not self.enabled:
            return
        if self.filter_drop_box:
            self.filter_drop_box.on_mouse_scroll(x, y, dx, dy)
        for element in self.get_elements():
            if self.filter_drop_box:
                if element is self.filter_drop_box:
                    continue
                if element is self.list_panel and self.filter_drop_box.over:
                    continue
            element.on_mouse_scroll(x, y, dx, dy)

    def set_tab(self, index, play_sound=True):
        if self.current_index != index:
            if play_sound:
                self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        if self.current_tab:
            self.current_tab.enabled = False
        self.current_index = index
        self.current_name, self.current_tab = self.tabs[index]
        self.current_tab.enabled = True
        if self.list_panel in self.elements:
            self.elements.remove(self.list_panel)
        list_panel_pos_y = PLAYER_PROFILE_PANEL_POS_Y
        if index == 0:
            list_panel_height = PLAYER_PROFILE_PANEL_HEIGHT
        else:
            list_panel_height = PLAYER_PROFILE_PANEL_OTHER_TABS_HEIGHT
        if self.current_index == 0:
            list_panel_pos_y = PLAYER_PROFILE_SUMMARY_POS_Y
            list_panel_height = PLAYER_PROFILE_SUMMARY_HEIGHT
        if self.current_index == 0:
            self.list_panel = PlayerProfileSummaryListPanel(self.manager)
        else:
            self.list_panel = ListPanelBase(self.manager)
        self.list_panel.scrollbar_extra_offset_x = -2
        if self.current_index == 0:
            self.list_panel.scrollbar_extra_length = 0
            self.list_panel.scrollbar_extra_offset_y += PLAYER_PROFILE_SUMMARY_REDBAR_GAP
        self.list_panel.initialise_ui(None, PLAYER_PROFILE_PANEL_POS_X, list_panel_pos_y, PLAYER_PROFILE_PANEL_WIDTH, list_panel_height, row_height=20, has_header=False)
        self.list_panel.set_background(background=BACKGROUND_NONE)
        self.list_panel.title = strings.SUMMARY
        self.list_panel.rows = []
        self.list_panel.current_row_index = 0
        self.list_panel.on_scroll(0, silent=True)
        self.elements.append(self.list_panel)
        if self.current_index == 0:
            self.populate_summary_list()
        else:
            self.populate_stats_list(self.current_tab.filters)
        if self.filter_drop_box in self.elements:
            self.elements.remove(self.filter_drop_box)
        if len(self.current_tab.filters) > 1:
            current_filter_index = 0
            if self.current_tab.current_filter != None:
                current_filter_index = self.current_tab.filters.index(self.current_tab.current_filter) + 1
            all_text = strings.get_by_id('ALL')
            rows = [all_text] + self.current_tab.filters
            self.filter_drop_box = DropBoxControl(self.manager, rows, 0, PLAYER_PROFILE_FILTER_DROPBOX_X, PLAYER_PROFILE_FILTER_DROPBOX_Y, PLAYER_PROFILE_FILTER_WIDTH, 30, len(rows))
            self.filter_drop_box.add_handler(self.on_filter_changed)
            self.filter_drop_box.add_focus_gained_handler(self.on_drop_focus_lost)
            self.filter_drop_box.add_focus_lost_handler(self.on_drop_focus_gained)
            self.elements.append(self.filter_drop_box)
            self.current_tab.current_filter = None
        return

    def on_drop_focus_lost(self, dropBoxControl):
        if self.focused_dropbox and self.focused_dropbox != dropBoxControl:
            self.focused_dropbox.close_drop_down(True)
        self.focused_dropbox = dropBoxControl

    def on_drop_focus_gained(self, dropBoxControl):
        self.focused_dropbox = None
        return

    def score_manager_callback(self, profile):
        if profile is None:
            return
        else:
            if 'profile' not in profile:
                self.show_no_connection = True
                self.show_wait_msg = False
                return
            if 'stats' not in profile['profile']:
                self.show_no_connection = True
                self.show_wait_msg = False
                return
            self.show_wait_msg = False
            self.profile_data = profile
            weapon_stats = {}
            for weaponID in range(len(WEAPONS)):
                weapon_stats[weaponID] = WeaponStat()

            profile_stats = profile['profile']['stats']
            for key, stat_values in profile_stats.iteritems():
                count_value, score_value = stat_values
                keyAsInt = int(key)
                if keyAsInt <= MAX_NOOF_SCORE_REASONS:
                    stat = self.get_category(keyAsInt)
                    if stat == None:
                        continue
                    stat.count = count_value
                    stat.score = score_value
                else:
                    if keyAsInt >= WEAPON_SHOOT_STATS[0] and keyAsInt < WEAPON_SHOOT_STATS[0] + STATS_MAX_WEAPONS:
                        weaponID = keyAsInt - WEAPON_SHOOT_STATS[0]
                        weapon_stats[weaponID].shots = count_value
                    if keyAsInt >= WEAPON_HIT_STATS[0] and keyAsInt < WEAPON_HIT_STATS[0] + STATS_MAX_WEAPONS:
                        weaponID = keyAsInt - WEAPON_HIT_STATS[0]
                        weapon_stats[weaponID].hits = count_value
                    if keyAsInt >= WEAPON_ACCUMULATED_POINTS_STATS[0] and keyAsInt < WEAPON_ACCUMULATED_POINTS_STATS[0] + STATS_MAX_WEAPONS:
                        stat = self.get_category(keyAsInt)
                        if stat == None:
                            continue
                        stat.score = score_value

            for weaponID in range(len(WEAPONS)):
                if weaponID in weapon_stats:
                    try:
                        weapon = WEAPONS[weaponID]
                        weapon_stat = weapon_stats[weaponID]
                        stat = self.get_category(WEAPON_SHOOT_STATS[weaponID])
                        if stat and weapon_stat.shots > 0:
                            stat.score = weapon_stat.hits / float(weapon_stat.shots)
                    except:
                        raise KeyError('Invalid weapon')

            if str(DEATH_SCORE_REASON) in profile_stats and str(KILL_SCORE_REASON) in profile_stats:
                if profile_stats[str(DEATH_SCORE_REASON)][0] > 0:
                    self.kd_ratio = profile_stats[str(KILL_SCORE_REASON)][0] / float(profile_stats[str(DEATH_SCORE_REASON)][0])
            for stat in self.category_stats:
                if stat.show_bar:
                    stat.calculate_level()

            self.set_tab(0, False)
            return

    def back_pressed(self):
        self.go_back()

    def go_back(self):
        self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
        from selectMenu import SelectMenu
        self.parent.set_menu(SelectMenu, back=True)

    def achievements_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        if not SteamShowAchievements():
            pass

    def draw(self):
        mid_x, mid_y = (400, 300)
        y = mid_y
        title_y = 549
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        global_images.small_frame.blit(mid_x, y)
        title_width = 300
        title_height = 80
        draw_text_with_size_validation(self.title.upper(), mid_x - title_width / 2, title_y - title_height / 2, title_width, title_height, MENU_FONT_COLOR, font=title_font)
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        if self.current_tab:
            self.content_frame.blit(mid_x - 2, mid_y)
            self.current_tab.draw()
            tab_height = 24.0
            tab_x = self.tabs_start_x
            tab_y = 470
            tab_index = 0
            for name, tab in self.tabs:
                tab_x = self.tabs_start_x + tab_index * (PLAYER_PROFILE_TABS_END_X - PLAYER_PROFILE_TABS_START_X) / (len(self.tabs) - 1)
                if self.current_tab == tab:
                    text_colour = MENU_FONT_COLOR2
                    self.tab_active_img.blit(int(tab_x + self.tab_width / 2), tab_y + tab_height / 2 - 1)
                else:
                    text_colour = MENU_FONT_COLOR
                    self.tab_inactive_img.blit(int(tab_x + self.tab_width / 2), tab_y + tab_height / 2 - 1)
                draw_text_with_size_validation(name, tab_x, tab_y, self.tab_width, tab_height, text_colour, settings_font)
                tab_index += 1

        if self.show_wait_msg:
            settings_font.draw(strings.CONNECTING_PLEASE_WAIT, mid_x, mid_y, MENU_FONT_COLOR, center=True)
        elif self.show_no_connection:
            settings_font.draw(strings.PROFILE_NOT_FOUND, mid_x, mid_y, MENU_FONT_COLOR, center=True)
        elif self.profile_data is not None:
            draw_text_with_size_validation(self.profile_data['profile']['name'], PLAYER_PROFILE_PLAYERNAME_X, PLAYER_PROFILE_PLAYERNAME_Y, 200, 20, MENU_FONT_COLOR, ammo_font, False)
            if self.current_tab:
                if strings.SUMMARY in self.current_tab.filters:
                    self.draw_summary()
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        for element in self.elements:
            if not element.enabled:
                continue
            element.draw()

        return

    def get_stat(self, code=KILL_SCORE_REASON):
        for stat in self.category_stats:
            if stat.code == code:
                return stat

        return

    def has_achieved_rank_level(self, rank=RANK_BEGINNER, criteria=LEVEL_CRITERIA_SOLDIER):
        criteria_count = 0
        for crit in criteria[rank]:
            stat = self.get_stat(crit.criterion)
            if stat:
                if stat.level > crit.level_requirement:
                    criteria_count += 1

        if criteria_count >= 3:
            return True
        return False

    def get_current_rank_level(self, criteria=LEVEL_CRITERIA_SOLDIER):
        if self.has_achieved_rank_level(RANK_INTERMEDIATE, criteria):
            if self.has_achieved_rank_level(RANK_ADVANCED, criteria):
                return RANK_ADVANCED
            else:
                return RANK_INTERMEDIATE

        return RANK_BEGINNER

    def populate_summary_list(self):
        if self.profile_data is None:
            return
        else:
            if self.list_panel == None:
                return
            class_background_tint = (1.0, 1.0, 1.0, 1.0)
            mode_background_tint = (1.0, 1.0, 1.0, 1.0)
            contents = ((strings.SOLDIER, LEVEL_CRITERIA_SOLDIER, class_background_tint),
             (
              strings.SCOUT, LEVEL_CRITERIA_SCOUT, class_background_tint),
             (
              strings.ENGINEER2, LEVEL_CRITERIA_ENGINEER, class_background_tint),
             (
              strings.MINER, LEVEL_CRITERIA_MINER, class_background_tint),
             (
              strings.GANGSTER, LEVEL_CRITERIA_GANGSTER, class_background_tint),
             (
              strings.SPECIALIST, LEVEL_CRITERIA_SPECIALIST , class_background_tint),
             (
              strings.MEDIC, LEVEL_CRITERIA_MEDIC, class_background_tint),
             (
              strings.TDM_TITLE, LEVEL_CRITERIA_TDM, mode_background_tint),
             (
              strings.CTF_TITLE, LEVEL_CRITERIA_CTF, mode_background_tint),
             (
              strings.DIAMOND_MINE_TITLE, LEVEL_CRITERIA_DIA, mode_background_tint),
             (
              strings.DEMOLITION_TITLE, LEVEL_CRITERIA_DEMO, mode_background_tint),
             (
              strings.MULTIHILL_TITLE, LEVEL_CRITERIA_MH, mode_background_tint),
             (
              strings.OCCUPATION_MODE_TITLE, LEVEL_CRITERIA_OCC, mode_background_tint),
             (
              strings.TC_TITLE, LEVEL_CRITERIA_TC, mode_background_tint),
             (
              strings.VIP_MODE_TITLE, LEVEL_CRITERIA_VIP, mode_background_tint),
             (
              strings.ZOMBIE_MODE_TITLE, LEVEL_CRITERIA_ZOM, mode_background_tint),
             (
              strings.CLASSIC, LEVEL_CRITERIA_CLASSIC, mode_background_tint))
            self.list_panel.rows = []
            listitem = PlayerProfileCategoryMultiColumnItem(strings.CLASS + ' / ' + strings.MODE, strings.RANK)
            listitem.update_position(self.list_panel.x1, self.list_panel.y1 - 10, self.list_panel.width, self.list_panel.row_height, self.list_panel.width)
            self.list_panel.rows.append(listitem)
            for row in contents:
                rank_id = self.get_current_rank_level(row[1])
                rank = strings.get_by_id(rank_id)
                listitem = PlayerProfileSummaryListItem(row[0], rank, background_tint=row[2])
                self.list_panel.rows.append(listitem)

            self.list_panel.on_scroll(0, silent=True)
            return

    def populate_stats_list(self, filter=[]):
        if self.profile_data is None:
            return
        else:
            if self.list_panel == None:
                return
            self.list_panel.rows = []
            for category in filter:
                listitem = PlayerProfileCategoryItem(category)
                self.list_panel.rows.append(listitem)
                for stat in self.category_stats:
                    if strings.get_by_id(PLAYER_PROFILE_CATEGORYS[stat.category]) != category:
                        continue
                    listitem = None
                    if stat.code < MAX_NOOF_SCORE_REASONS:
                        if stat.show_bar:
                            listitem = PlayerProfileStatListItem(strings.get_by_id(SCORE_REASON_CODES[stat.code]), stat.count)
                            listitem.setup_bar(stat.level, stat.next_level_min, stat.next_level_max)
                        else:
                            stat_value = str(0)
                            if stat.show_score == True:
                                stat_value = stat.score
                            else:
                                stat_value = stat.count
                            if stat.value_modifier != None:
                                stat_value = stat.value_modifier(stat_value)
                            listitem = PlayerProfileStatListItem(strings.get_by_id(SCORE_REASON_CODES[stat.code]), stat_value)
                    else:
                        weapon = None
                        if stat.code >= WEAPON_SHOOT_STATS[0] and stat.code < WEAPON_SHOOT_STATS[0] + STATS_MAX_WEAPONS:
                            weapon_id = stat.code - WEAPON_SHOOT_STATS[0]
                            try:
                                weapon = WEAPONS[weapon_id]
                            except KeyError:
                                continue

                        elif stat.code >= WEAPON_ACCUMULATED_POINTS_STATS[0] and stat.code < WEAPON_ACCUMULATED_POINTS_STATS[0] + STATS_MAX_WEAPONS:
                            weapon_id = stat.code - WEAPON_ACCUMULATED_POINTS_STATS[0]
                            try:
                                weapon = WEAPONS[weapon_id]
                            except KeyError:
                                continue

                        if weapon is not None:
                            stat_value = str(0)
                            if stat.show_score == True:
                                stat_value = stat.score
                            else:
                                stat_value = stat.count
                            if stat.value_modifier != None:
                                stat_value = stat.value_modifier(stat_value)
                            listitem = PlayerProfileStatListItem(weapon.name, stat_value)
                    if listitem:
                        self.list_panel.rows.append(listitem)

            self.list_panel.on_scroll(0, silent=True)
            return

    def draw_summary(self):
        kd_y = PLAYER_PROFILE_PLAYERNAME_Y
        kd_ratio_string = '%.3f' % round(self.kd_ratio, 3)
        kd_x = PLAYER_PROFILE_PANEL_POS_X + self.list_panel.width / 2
        kd_width = PLAYER_PROFILE_KDRATIO_RIGHTALIGN_TO - kd_x
        draw_text_with_alignment_and_size_validation(strings.KILL_DEATH_RATIO + ': ' + kd_ratio_string, kd_x, kd_y, kd_width, 20, MENU_FONT_COLOR, small_standard_ui_font, alignment_x='right')

    def get_category(self, code):
        for stat in self.category_stats:
            if stat.code == code:
                return stat

    def setup_categories(self):
        self.category_stats = PLAYER_PROFILE_CATEGORY_STATS

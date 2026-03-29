from shared.constants import *
from aoslib import image
from shared.common import get_map_directory
from aoslib.vxl import create_shadow_vbo
import gc, os

class SkinnedImage(object):
    current_image = None
    default_image = None
    mafia_image = None

    def __init__(self, default_image, mafia_image, skin):
        self.default_image = default_image
        self.mafia_image = mafia_image
        self.set_skin(skin)

    def is_image(self, image):
        if self.current_image == image:
            return True
        return False

    def set_skin(self, skin):
        if skin == 'mafia':
            self.current_image = self.mafia_image
        else:
            self.current_image = self.default_image
        return self.current_image


def load_ui(old_tex, name, center=False, scale=0.6, filtered=True, none_resource=False, add_path=False, skinned_images=None, skin=None):
    try:
        if skinned_images is not None and skin is not None:
            default_image = image.load_texture(name, filtered=filtered, center=center, scale=scale, none_resource=none_resource, add_path=add_path)
            image.set_texture_skin(skin)
            mafia_image = image.load_texture(name, filtered=filtered, center=center, scale=scale, none_resource=none_resource, add_path=add_path)
            image.set_texture_skin(None)
            skinned_image = SkinnedImage(default_image, mafia_image, None)
            skinned_images.append(skinned_image)
            return skinned_image.current_image
        if old_tex is None or image.needs_reload(name, add_path=add_path) or old_tex.name != name:
            return image.load_texture(name, filtered=filtered, center=center, scale=scale, none_resource=none_resource, add_path=add_path)
    except MemoryError:
        print 'Failed to load:', name, 'due to MemoryError'

    return old_tex


def get_map_preview_full_filename(name):
    return os.path.join(get_map_directory(), '%s' % name)


class GlobalImages(object):
    skinned_images = []

    def __init__(self):
        self.global_scale = 0.64
        self.clear()
        del self.skinned_images[:]

    def reset_map_previews(self):
        self.map_previews = {'Alcatraz': [
                      'Blocatraz', None, None], 
           'Ancient Egypt': [
                           'ancientegypt', None, None], 
           'Arctic Base': [
                         'arcticbase', None, None], 
           'Atlantis': [
                      'Atlantis', None, None], 
           'Block Ness': [
                        'blockness', None, None], 
           'Bran Castle': [
                         'brancastle', None, None], 
           'Castle Wars': [
                         'castlewars', None, None], 
           'City Of Chicago': [
                             'midtownmassacre', None, None], 
           'City of Chicago': [
                             'midtownmassacre', None, None], 
           'Classic': [
                     'Classic', None, None], 
           'Crossroads': [
                        'crossroadcarnage', None, None], 
           'Double Dragon': [
                           'doubledragon', None, None], 
           'Dragon Island': [
                           'dragonisland', None, None], 
           'Frontier': [
                      'frontier', None, None], 
           'Great Wall': [
                        'greatwall', None, None], 
           'Hiesville': [
                       'hiesville', None, None], 
           'Invasion': [
                      'Invasion', None, None], 
           'London': [
                    'london', None, None], 
           'Lunar Base': [
                        'lunarbase', None, None], 
           'Mayan Jungle': [
                          'mayanjungle', None, None], 
           'Spooky Mansion': [
                            'spookymansion', None, None], 
           'The Colosseum': [
                           'colosseum', None, None], 
           'To The Bridge': [
                           'tothebridge', None, None], 
           'Tokyo Neon': [
                        'tokyoneon', None, None], 
           'Trenches': [
                      'Trenches', None, None], 
           'Winter Valley': [
                           'wintervalley', None, None], 
           'WW1': [
                 'ww1', None, None], 
           'Desert': [
                    'DesertBaseplate', None, None], 
           'Grassland': [
                       'GrasslandBaseplate', None, None], 
           'Lunar': [
                   'LunarBaseplate', None, None], 
           'Mountain': [
                      'MountainBaseplate', None, None], 
           'Temple': [
                    'TempleBaseplate', None, None], 
           'Urban': [
                   'UrbanBaseplate', None, None]}
        self.map_preview_ugc = None
        return

    def load_loading_screen(self):
        frames = ['common_elements', 'frames']
        self.large_frame = load_ui(self.large_frame, frames + ['ui_frame_large'], center=True, scale=self.global_scale, skinned_images=self.skinned_images, skin='mafia')

    def set_skin(self, skin_string):
        for skin in self.skinned_images:
            if skin.is_image(self.large_frame):
                self.large_frame = skin.set_skin(skin_string)
                continue
            elif skin.is_image(self.ingame_settings_frame):
                self.ingame_settings_frame = skin.set_skin(skin_string)
                continue
            elif skin.is_image(self.main_settings_frame):
                self.main_settings_frame = skin.set_skin(skin_string)
                continue
            elif skin.is_image(self.graphics_settings_frame):
                self.graphics_settings_frame = skin.set_skin(skin_string)
                continue
            elif skin.is_image(self.controls_frame):
                self.controls_frame = skin.set_skin(skin_string)
                continue
            elif skin.is_image(self.choose_team_frame):
                self.choose_team_frame = skin.set_skin(skin_string)
                continue
            elif skin.is_image(self.view_scores_frame):
                self.view_scores_frame = skin.set_skin(skin_string)
                continue
            elif skin.is_image(self.change_team_frame):
                self.change_team_frame = skin.set_skin(skin_string)
                continue
            elif skin.is_image(self.pause_menu_frame):
                self.pause_menu_frame = skin.set_skin(skin_string)
                continue

    def load_global_images(self, load_ui_frame_large=True):
        common_elements = ['common_elements']
        buttons = common_elements + ['buttons']
        frames = common_elements + ['frames']
        server_list = ['server select']
        icons = ['icons']
        panels = common_elements + ['panels']
        ugc_tools = ['ugc_tools']
        global_scale = self.global_scale
        for number_key in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10'):
            self.key_images[number_key][0] = load_ui(self.key_images[number_key][0], icons + ['key%s' % number_key], scale=global_scale, center=True, filtered=False)
            self.key_images[number_key][1] = load_ui(self.key_images[number_key][1], icons + ['key_press%s' % number_key], scale=global_scale, center=True, filtered=False)

        for ugc_tool_id, ugc_image_name in UGC_TOOL_IMAGES.iteritems():
            self.ugc_tool_images[ugc_tool_id] = load_ui(self.ugc_tool_images[ugc_tool_id], ugc_tools + [ugc_image_name], scale=global_scale, center=True)

        self.splash_image = load_ui(self.splash_image, 'splash', center=True)
        self.main_image = load_ui(self.main_image, 'ugc_splash')
        self.main_menu_frame = load_ui(self.main_menu_frame, ['main_menu', 'frame_main_menu'], center=True)
        self.name_frame = load_ui(self.name_frame, ['main_menu', 'frame_player_name'])
        self.frame_3button_menu = load_ui(self.frame_3button_menu, ['main_menu', 'frame_3button_menu'], center=True)
        self.frame_nav_bar_small = load_ui(self.frame_nav_bar_small, ['main_menu', 'frame_nav_bar_small'], center=True)
        self.green_highlight_glow = load_ui(self.green_highlight_glow, buttons + ['highlight_glow'], filtered=False)
        self.green_highlight_line = load_ui(self.green_highlight_line, buttons + ['highlight_line'], filtered=False)
        self.button_left = load_ui(self.button_left, buttons + ['button_large_left'], filtered=False)
        self.button_mid = load_ui(self.button_mid, buttons + ['button_large_mid'], filtered=False)
        self.button_right = load_ui(self.button_right, buttons + ['button_large_right'], filtered=False)
        self.button_hover_left = load_ui(self.button_hover_left, buttons + ['button_large_hover_left'], filtered=False)
        self.button_hover_mid = load_ui(self.button_hover_mid, buttons + ['button_large_hover_mid'], filtered=False)
        self.button_hover_right = load_ui(self.button_hover_right, buttons + ['button_large_hover_right'], filtered=False)
        self.button_press_left = load_ui(self.button_press_left, buttons + ['button_large_press_left'], filtered=False)
        self.button_press_mid = load_ui(self.button_press_mid, buttons + ['button_large_press_mid'], filtered=False)
        self.button_press_right = load_ui(self.button_press_right, buttons + ['button_large_press_right'], filtered=False)
        self.button_ready_left = load_ui(self.button_ready_left, buttons + ['button_large_ready_left'], filtered=False)
        self.button_ready_mid = load_ui(self.button_ready_mid, buttons + ['button_large_ready_mid'], filtered=False)
        self.button_ready_right = load_ui(self.button_ready_right, buttons + ['button_large_ready_right'], filtered=False)
        self.button_glow_left = load_ui(self.button_glow_left, buttons + ['button_large_start_left_default'], filtered=False)
        self.button_glow_mid = load_ui(self.button_glow_mid, buttons + ['button_large_start_mid_default'], filtered=False)
        self.button_glow_right = load_ui(self.button_glow_right, buttons + ['button_large_start_right_default'], filtered=False)
        self.button_glow_press_left = load_ui(self.button_glow_press_left, buttons + ['button_large_start_left_press'], filtered=False)
        self.button_glow_press_mid = load_ui(self.button_glow_press_mid, buttons + ['button_large_start_mid_press'], filtered=False)
        self.button_glow_press_right = load_ui(self.button_glow_press_right, buttons + ['button_large_start_right_press'], filtered=False)
        self.button_glow_hover_left = load_ui(self.button_glow_hover_left, buttons + ['button_large_start_left_hover'], filtered=False)
        self.button_glow_hover_mid = load_ui(self.button_glow_hover_mid, buttons + ['button_large_start_mid_hover'], filtered=False)
        self.button_glow_hover_right = load_ui(self.button_glow_hover_right, buttons + ['button_large_start_right_hover'], filtered=False)
        self.button_square = load_ui(self.button_square, buttons + ['button_square'], filtered=False, scale=1.0)
        self.button_square_hover = load_ui(self.button_square_hover, buttons + ['button_square_hover'], filtered=False, scale=1.0)
        self.button_square_press = load_ui(self.button_square_press, buttons + ['button_square_press'], filtered=False, scale=1.0)
        self.main_menu_button_square = load_ui(self.main_menu_button_square, buttons + ['mm_button_square_default'], filtered=False, scale=1.0)
        self.main_menu_button_square_hover = load_ui(self.main_menu_button_square_hover, buttons + ['mm_button_square_hover'], filtered=False, scale=1.0)
        self.main_menu_button_square_press = load_ui(self.main_menu_button_square_press, buttons + ['mm_button_square_press'], filtered=False, scale=1.0)
        self.button_glow = load_ui(self.button_glow, buttons + ['button_large_glow'], center=True, scale=global_scale)
        self.panel_frame = load_ui(self.panel_frame, panels + ['ui_panel_frame'], center=True, scale=global_scale)
        self.panel_header_dark_frame = load_ui(self.panel_header_dark_frame, panels + ['subtitle_bg'], center=True, scale=global_scale)
        self.small_frame = load_ui(self.small_frame, frames + ['ui_frame_small'], center=True, scale=global_scale)
        if load_ui_frame_large:
            self.large_frame = load_ui(self.large_frame, frames + ['ui_frame_large'], center=True, scale=global_scale, skinned_images=self.skinned_images, skin='mafia')
        self.message_box_frame = load_ui(self.message_box_frame, frames + ['ui_frame_overlay_confirmation'], center=True, scale=global_scale)
        self.message_box_with_buttons_frame = load_ui(self.message_box_with_buttons_frame, frames + ['ui_frame_overlay_warning'], center=True, scale=global_scale)
        self.message_box_extended_frame = load_ui(self.message_box_extended_frame, frames + ['ui_frame_overlay_disclaimer'], center=True, scale=global_scale)
        self.server_content_frame = load_ui(self.server_content_frame, server_list + ['server_select_content_frames'], center=True, scale=global_scale)
        self.server_tab_name_frame = load_ui(self.server_tab_name_frame, server_list + ['tab_name_frame'], center=True, scale=global_scale)
        self.favorite_star_button = load_ui(self.favorite_star_button, server_list + ['favourite_star_button'], scale=global_scale, center=True)
        self.favorite_star = load_ui(self.favorite_star, server_list + ['favourite_star'], scale=global_scale, center=True)
        self.star_checkmark = load_ui(self.star_checkmark, 'favourite_star_settings', scale=global_scale)
        self.star_checkmark_off = load_ui(self.star_checkmark_off, 'favourite_star_settings_off', scale=global_scale)
        self.leaderboard_frame = load_ui(self.leaderboard_frame, ['leaderboard_menu', 'ui_frame_leaderboard'], center=True)
        scroll_bar = common_elements + ['scroll_bar']
        self.filter_up = load_ui(self.filter_up, common_elements + ['filter_arrow_up'], center=True, scale=global_scale)
        self.filter_down = load_ui(self.filter_down, common_elements + ['filter_arrow_down'], center=True, scale=global_scale)
        self.filter_up_white = load_ui(self.filter_up_white, common_elements + ['filter_arrow_up_white'], center=True, scale=global_scale)
        self.filter_down_white = load_ui(self.filter_down_white, common_elements + ['filter_arrow_down_white'], center=True, scale=global_scale)
        self.edit_icon = load_ui(self.edit_icon, common_elements + ['icon_edit'], center=True, scale=1.0, filtered=False)
        self.checkmark = load_ui(self.checkmark, common_elements + ['tick'], scale=global_scale)
        self.checkbox_background = load_ui(self.checkbox_background, common_elements + ['menu_item_checkbox'], center=True, scale=global_scale)
        self.round_control_frame = load_ui(self.round_control_frame, common_elements + ['round_control_frame'], center=True, scale=global_scale)
        self.collapse_minus = load_ui(self.collapse_minus, common_elements + ['collapse_minus'], center=True, scale=1.0)
        self.collapse_plus = load_ui(self.collapse_plus, common_elements + ['collapse_plus'], center=True, scale=1.0)
        self.red_header_center = load_ui(self.red_header_center, common_elements + ['header'] + ['red_header_center'], center=True, scale=global_scale, filtered=False)
        self.red_header_left = load_ui(self.red_header_left, common_elements + ['header'] + ['red_header_left'], center=True, scale=global_scale, filtered=False)
        self.red_header_right = load_ui(self.red_header_right, common_elements + ['header'] + ['red_header_right'], center=True, scale=global_scale, filtered=False)
        self.left_arrow = load_ui(self.left_arrow, scroll_bar + ['scroll_bar_arrow_left'], center=True, scale=1.0, filtered=False)
        self.right_arrow = load_ui(self.right_arrow, scroll_bar + ['scroll_bar_arrow_right'], center=True, scale=1.0, filtered=False)
        self.up_arrow = load_ui(self.up_arrow, scroll_bar + ['scroll_bar_arrow_up'], center=True, scale=1.0, filtered=False)
        self.down_arrow = load_ui(self.down_arrow, scroll_bar + ['scroll_bar_arrow_down'], center=True, scale=1.0, filtered=False)
        self.scroll_top = load_ui(self.scroll_top, scroll_bar + ['scroll_bar_top'], scale=0.8, filtered=False)
        self.scroll_mid = load_ui(self.scroll_mid, scroll_bar + ['scroll_bar_mid'], scale=0.8, filtered=False)
        self.scroll_bottom = load_ui(self.scroll_bottom, scroll_bar + ['scroll_bar_bottom'], scale=0.8, filtered=False)
        self.scroll_bar_top = load_ui(self.scroll_bar_top, scroll_bar + ['scrollbar_top'], center=True)
        self.scroll_bar_mid = load_ui(self.scroll_bar_mid, scroll_bar + ['scrollbar_mid'], center=True)
        self.scroll_bar_bottom = load_ui(self.scroll_bar_bottom, scroll_bar + ['scrollbar_bottom'], center=True)
        self.scroll_bar_left = load_ui(self.scroll_bar_left, scroll_bar + ['scrollbar_left'], center=True)
        self.scroll_bar_hmid = load_ui(self.scroll_bar_hmid, scroll_bar + ['scrollbar_hmid'], center=True)
        self.scroll_bar_right = load_ui(self.scroll_bar_right, scroll_bar + ['scrollbar_right'], center=True)
        self.pointer_billboard = image.load('pointer_icon', center=True)
        self.map_placeholder = load_ui(self.map_placeholder, server_list + ['map_placeholder'], scale=global_scale)
        for map_name, image_details in self.map_previews.iteritems():
            loading = ['game_loading']
            map_previews = loading + ['map_previews']
            try:
                self.map_previews[map_name][2] = load_ui(self.map_previews[map_name][2], map_previews + [image_details[0]], scale=global_scale)
                tex_coords = self.map_previews[map_name][2].tex_coords
                self.map_previews[map_name][2].tex_coords = tex_coords[3:] + tex_coords[:3]
            except IOError:
                self.map_previews[map_name][2] = None

            self.map_previews[map_name][1] = self.map_previews[map_name][2]

        navbar = common_elements + ['nav_bar']
        self.quit_icon = load_ui(self.quit_icon, navbar + ['quit_icon'], scale=global_scale, center=True)
        self.main_menu_icon = load_ui(self.main_menu_icon, navbar + ['main_menu_icon'], scale=global_scale, center=True)
        self.back_icon = load_ui(self.back_icon, navbar + ['back_icon'], scale=global_scale, center=True)
        self.right_icon = load_ui(self.right_icon, navbar + ['right_icon'], scale=global_scale, center=True)
        settings = [
         'settings']
        settings_controls = settings + ['settings_contols']
        settings_main = settings + ['settings_main']
        settings_controls = settings + ['settings_controls']
        settings_graphics = settings + ['settings_graphics']
        settings_common = settings + ['settings_common']
        self.ingame_settings_frame = load_ui(self.ingame_settings_frame, settings + ['in_game_settings_frame'], scale=global_scale, center=True, skinned_images=self.skinned_images, skin='mafia')
        self.ingame_settings_content_frame = load_ui(self.ingame_settings_content_frame, settings + ['in_game_settings_content_frame'], scale=global_scale, center=True)
        self.settings_tooltip_frame = load_ui(self.settings_tooltip_frame, settings_common + ['settings_tooltip_frame'], filtered=False, scale=1.0, center=True)
        self.settings_tooltip_frame_ingame = load_ui(self.settings_tooltip_frame_ingame, settings_common + ['settings_tooltip_frame_ingame'], filtered=False, scale=1.0, center=True)
        self.bullet_hole = load_ui(self.bullet_hole, settings_common + ['bullet_hole'], filtered=False, scale=1.0, center=True)
        self.bullet_hole_disabled = load_ui(self.bullet_hole_disabled, settings_common + ['bullet_hole_disabled'], filtered=False, scale=1.0, center=True)
        self.bullet_slider = load_ui(self.bullet_slider, settings_common + ['settings_bullet_slider'], scale=global_scale, center=True)
        self.settings_matchsettings_frame = load_ui(self.settings_matchsettings_frame, settings_common + ['settings_matchsettings_frame'], scale=global_scale, center=True)
        self.settings_frame_disabled = load_ui(self.settings_frame_disabled, settings_common + ['settings_frame_disabled'], scale=global_scale, center=True)
        self.main_settings_frame = load_ui(self.main_settings_frame, settings_main + ['settings_main_content_frames'], scale=global_scale, center=True, skinned_images=self.skinned_images, skin='mafia')
        self.volume_bar = load_ui(self.volume_bar, settings_main + ['volume_bar'], scale=global_scale, filtered=False, center=True)
        self.graphics_settings_frame = load_ui(self.graphics_settings_frame, settings_graphics + ['settings_graphics_content_frames'], scale=global_scale, center=True, skinned_images=self.skinned_images, skin='mafia')
        self.controls_frame = load_ui(self.controls_frame, settings_controls + ['settings_controls_content_frames'], scale=global_scale, center=True, skinned_images=self.skinned_images, skin='mafia')
        self.controls_frame_content = load_ui(self.controls_frame_content, settings_controls + ['settings_controls_content_frame'], scale=global_scale, center=True)
        generic_tabs = settings + ['tab_frames']
        self.generic_tab_active = load_ui(self.generic_tab_active, generic_tabs + ['generic_tab_active'], scale=global_scale, center=True)
        self.generic_tab_inactive = load_ui(self.generic_tab_inactive, generic_tabs + ['generic_tab_inactive'], scale=global_scale, center=True)
        self.profile_stats_bg = load_ui(self.profile_stats_bg, generic_tabs + ['player_profile_stats_bg'], scale=global_scale, center=True)
        self.profile_level_bar_bg = load_ui(self.profile_level_bar_bg, generic_tabs + ['level_bar_bg'], scale=global_scale, center=True)
        loading = [
         'game_loading']
        self.loading_map_frame = load_ui(self.loading_map_frame, loading + ['minimap_bg'], center=False, scale=self.global_scale)
        self.progress_bullet = load_ui(self.progress_bullet, loading + ['loading_bar_bullet'], scale=0.7)
        self.progress_bullet.anchor_y = self.progress_bullet.height / 2
        self.loading_bar_bg = load_ui(self.loading_bar_bg, loading + ['game_loading_bar_bg'], scale=global_scale, center=False)
        self.loading_tab_bg = load_ui(self.loading_tab_bg, loading + ['game_loading_tab_bg'], scale=global_scale, center=True)
        self.choose_team_frame = load_ui(self.choose_team_frame, ['choose_team', 'choose_team_content_frames'], scale=global_scale, center=True, skinned_images=self.skinned_images, skin='mafia')
        searching = [
         'searching']
        self.searching_logo = load_ui(self.searching_logo, searching + ['ui_searching'], center=True, scale=global_scale * 0.9, filtered=False)
        self.searching_tutorial = load_ui(self.searching_tutorial, searching + ['searching_tut'], center=True, scale=global_scale * 0.9, filtered=False)
        loading_mode_images = loading + ['letterbox_images']
        self.mode_images_letterbox = {}
        self.mode_image_letterbox_random = load_ui(self.mode_image_letterbox_random, loading_mode_images + ['letterbox_random'], scale=global_scale, center=True)
        self.mode_image_letterbox_multi_mode = load_ui(self.mode_image_letterbox_multi_mode, loading_mode_images + ['letterbox_multiplegamemodes'], scale=global_scale, center=True)
        for mode, name in self.mode_image_names.iteritems():
            self.mode_images_letterbox[mode] = None
            self.mode_images_letterbox[mode] = load_ui(self.mode_images_letterbox[mode], loading_mode_images + [name], scale=global_scale, center=True)

        ingame = [
         'in_game_menus']
        self.big_text_frame = load_ui(self.big_text_frame, ingame + ['big_text_frame'], scale=global_scale, center=True)
        self.view_scores_frame = load_ui(self.view_scores_frame, ingame + ['view_scores_content_frames'], scale=global_scale, center=True, skinned_images=self.skinned_images, skin='mafia')
        self.ugc_tab_frame = load_ui(self.ugc_tab_frame, ingame + ['ugc_tab_frame'], scale=global_scale, center=True)
        self.view_game_stats_frame = load_ui(self.view_game_stats_frame, ingame + ['view_game_stats_content_framesy'], scale=global_scale, center=True)
        self.view_game_stats_rankbar_bar = load_ui(self.view_game_stats_rankbar_bar, ingame + ['view_game_stats_rankup_bar_stroke'], scale=global_scale, center=False)
        self.view_game_stats_rankbar_stroke_glow = load_ui(self.view_game_stats_rankbar_stroke_glow, ingame + ['view_game_stats_content_stroke_glow'], scale=global_scale, center=False)
        self.change_team_frame = load_ui(self.change_team_frame, ingame + ['change_team_content_frames'], scale=global_scale, center=True, skinned_images=self.skinned_images, skin='mafia')
        self.score_text_frame = load_ui(self.score_text_frame, ingame + ['score_text_frame'], scale=global_scale, center=True)
        self.four_items_frame = load_ui(self.four_items_frame, ingame + ['four_items_frame'], scale=global_scale, center=True)
        self.five_items_frame = load_ui(self.five_items_frame, ingame + ['five_items_frame'], scale=global_scale, center=True)
        self.pause_menu_frame = load_ui(self.pause_menu_frame, ingame + ['pause_menu_frame'], scale=global_scale, center=True, skinned_images=self.skinned_images, skin='mafia')
        self.pause_menu_frame_big = load_ui(self.pause_menu_frame_big, ingame + ['pause_menu_frame_expanded'], scale=global_scale, center=True)
        self.screenshot_frame = load_ui(self.screenshot_frame, ingame + ['screenshot_frame'], scale=global_scale, center=False)
        self.highlight_scoreboard_blue = load_ui(self.highlight_scoreboard_blue, buttons + ['highlight_scoreboard_blue'], scale=1.0, center=True)
        self.highlight_scoreboard_green = load_ui(self.highlight_scoreboard_green, buttons + ['highlight_scoreboard_green'], scale=1.0, center=True)
        self.highlight_scoreboard_white = load_ui(self.highlight_scoreboard_white, buttons + ['highlight_scoreboard_white'], scale=1.0, center=True)
        self.hover_scoreboard_blue = load_ui(self.hover_scoreboard_blue, buttons + ['hover_scoreboard_blue'], scale=1.0, center=True)
        self.hover_scoreboard_green = load_ui(self.hover_scoreboard_green, buttons + ['hover_scoreboard_green'], scale=1.0, center=True)
        self.hover_scoreboard_white = load_ui(self.hover_scoreboard_white, buttons + ['hover_scoreboard_white'], scale=1.0, center=True)
        choose_class_path = ingame + ['select_class']
        self.score_dominated_image = load_ui(self.score_dominated_image, choose_class_path + ['dominated'], scale=global_scale, center=True)
        self.score_dominating_image = load_ui(self.score_dominating_image, choose_class_path + ['domination'], scale=global_scale, center=True)
        self.in_game_class_frame = load_ui(self.in_game_class_frame, choose_class_path + ['in_game_class_frame'], scale=global_scale, center=True)
        self.class_background_frame = load_ui(self.class_background_frame, choose_class_path + ['class_background_frame'], scale=global_scale, center=True, filtered=False)
        self.class_background_frame5 = load_ui(self.class_background_frame5, choose_class_path + ['class_background_frame_5'], scale=global_scale, center=True, filtered=False)
        self.class_selected_frame = load_ui(self.class_selected_frame, choose_class_path + ['class_selected_frame'], scale=global_scale, center=True)
        self.loadout_item_background = load_ui(self.loadout_item_background, choose_class_path + ['loadout_background'], scale=global_scale, center=True, filtered=False)
        self.loadout_item_background_disabled = load_ui(self.loadout_item_background_disabled, choose_class_path + ['loadout_background_disabled'], scale=global_scale, center=True, filtered=False)
        self.loadout_info_frame = load_ui(self.loadout_info_frame, choose_class_path + ['item_info_frame'], scale=global_scale, center=True)
        self.disabled_loadout_info_frame = load_ui(self.disabled_loadout_info_frame, choose_class_path + ['disabled_item_info_frame'], scale=global_scale, center=True)
        self.class_info_frame_left = load_ui(self.class_info_frame_left, choose_class_path + ['class_info_frame_left'], scale=global_scale, center=True)
        self.class_info_frame_right = load_ui(self.class_info_frame_right, choose_class_path + ['class_info_frame_right'], scale=global_scale, center=True)
        self.disabled_class_info_frame_left = load_ui(self.disabled_class_info_frame_left, choose_class_path + ['disabled_class_info_frame_left'], scale=global_scale, center=True)
        self.disabled_class_info_frame_right = load_ui(self.disabled_class_info_frame_right, choose_class_path + ['disabled_class_info_frame_right'], scale=global_scale, center=True)
        self.prefab_info_frame = load_ui(self.prefab_info_frame, choose_class_path + ['prefab_info_frame'], scale=global_scale, center=True)
        self.class_frame_arrow = load_ui(self.class_frame_arrow, choose_class_path + ['frame_arrow'], scale=global_scale, center=True)
        self.disabled_class_frame_arrow = load_ui(self.disabled_class_frame_arrow, choose_class_path + ['disabled_frame_arrow'], scale=global_scale, center=True)
        self.ugcbuilder_icon_team1 = load_ui(self.ugcbuilder_icon_team1, choose_class_path + ['ugcbuilder_icon_team1'], scale=global_scale, center=True)
        self.miner_icon_team1 = load_ui(self.miner_icon_team1, choose_class_path + ['miner_icon_team1'], scale=global_scale, center=True)
        self.scout_icon_team1 = load_ui(self.scout_icon_team1, choose_class_path + ['scout_icon_team1'], scale=global_scale, center=True)
        self.pilot_icon_team1 = load_ui(self.pilot_icon_team1, choose_class_path + ['pilot_icon_team1'], scale=global_scale, center=True)
        self.engineer_icon_team1 = load_ui(self.engineer_icon_team1, choose_class_path + ['engineer_icon_team1'], scale=global_scale, center=True)
        self.soldier_icon_team1 = load_ui(self.soldier_icon_team1, choose_class_path + ['soldier_icon_team1'], scale=global_scale, center=True)
        self.classic_icon_team1 = load_ui(self.classic_icon_team1, choose_class_path + ['classic_icon_team1'], scale=global_scale, center=True)
        self.gangster1_icon_team1 = load_ui(self.gangster1_icon_team1, choose_class_path + ['gangster1_icon_team1'], scale=global_scale, center=True)
        self.gangster2_icon_team1 = load_ui(self.gangster2_icon_team1, choose_class_path + ['gangster2_icon_team1'], scale=global_scale, center=True)
        self.gangster3_icon_team1 = load_ui(self.gangster3_icon_team1, choose_class_path + ['gangster3_icon_team1'], scale=global_scale, center=True)
        self.gangster4_icon_team1 = load_ui(self.gangster4_icon_team1, choose_class_path + ['gangster4_icon_team1'], scale=global_scale, center=True)
        self.boss_icon_team1 = load_ui(self.boss_icon_team1, choose_class_path + ['boss_icon_team1'], scale=global_scale, center=True)
        self.ugcbuilder_icon_team2 = load_ui(self.ugcbuilder_icon_team2, choose_class_path + ['ugcbuilder_icon_team2'], scale=global_scale, center=True)
        self.miner_icon_team2 = load_ui(self.miner_icon_team2, choose_class_path + ['miner_icon_team2'], scale=global_scale, center=True)
        self.scout_icon_team2 = load_ui(self.scout_icon_team2, choose_class_path + ['scout_icon_team2'], scale=global_scale, center=True)
        self.pilot_icon_team2 = load_ui(self.pilot_icon_team2, choose_class_path + ['pilot_icon_team2'], scale=global_scale, center=True)
        self.engineer_icon_team2 = load_ui(self.engineer_icon_team2, choose_class_path + ['engineer_icon_team2'], scale=global_scale, center=True)
        self.soldier_icon_team2 = load_ui(self.soldier_icon_team2, choose_class_path + ['soldier_icon_team2'], scale=global_scale, center=True)
        self.classic_icon_team2 = load_ui(self.classic_icon_team2, choose_class_path + ['classic_icon_team2'], scale=global_scale, center=True)
        self.gangster1_icon_team2 = load_ui(self.gangster1_icon_team2, choose_class_path + ['gangster1_icon_team2'], scale=global_scale, center=True)
        self.gangster2_icon_team2 = load_ui(self.gangster2_icon_team2, choose_class_path + ['gangster2_icon_team2'], scale=global_scale, center=True)
        self.gangster3_icon_team2 = load_ui(self.gangster3_icon_team2, choose_class_path + ['gangster3_icon_team2'], scale=global_scale, center=True)
        self.gangster4_icon_team2 = load_ui(self.gangster4_icon_team2, choose_class_path + ['gangster4_icon_team2'], scale=global_scale, center=True)
        self.boss_icon_team2 = load_ui(self.boss_icon_team2, choose_class_path + ['boss_icon_team2'], scale=global_scale, center=True)
        self.zombie_icon = load_ui(self.zombie_icon, choose_class_path + ['zombie_icon'], scale=global_scale, center=True)
        self.ugcbuilder_image_team1 = load_ui(self.ugcbuilder_image_team1, choose_class_path + ['ugcbuilder_character_team1'], scale=global_scale, center=True)
        self.miner_image_team1 = load_ui(self.miner_image_team1, choose_class_path + ['miner_character_team1'], scale=global_scale, center=True)
        self.scout_image_team1 = load_ui(self.scout_image_team1, choose_class_path + ['scout_character_team1'], scale=global_scale, center=True)
        self.pilot_image_team1 = load_ui(self.pilot_image_team1, choose_class_path + ['pilot_character_team1'], scale=global_scale, center=True)
        self.engineer_image_team1 = load_ui(self.engineer_image_team1, choose_class_path + ['engineer_character_team1'], scale=global_scale, center=True)
        self.soldier_image_team1 = load_ui(self.soldier_image_team1, choose_class_path + ['soldier_character_team1'], scale=global_scale, center=True)
        self.classic_image_team1 = load_ui(self.classic_image_team1, choose_class_path + ['classic_character_team1'], scale=global_scale, center=True)
        self.zombie_image_team1 = load_ui(self.zombie_image_team1, choose_class_path + ['zombie_character_team1'], scale=global_scale, center=True)
        self.ugcbuilder_image_team2 = load_ui(self.ugcbuilder_image_team2, choose_class_path + ['ugcbuilder_character_team2'], scale=global_scale, center=True)
        self.miner_image_team2 = load_ui(self.miner_image_team2, choose_class_path + ['miner_character_team2'], scale=global_scale, center=True)
        self.scout_image_team2 = load_ui(self.scout_image_team2, choose_class_path + ['scout_character_team2'], scale=global_scale, center=True)
        self.pilot_image_team2 = load_ui(self.pilot_image_team2, choose_class_path + ['pilot_character_team2'], scale=global_scale, center=True)
        self.engineer_image_team2 = load_ui(self.engineer_image_team2, choose_class_path + ['engineer_character_team2'], scale=global_scale, center=True)
        self.soldier_image_team2 = load_ui(self.soldier_image_team2, choose_class_path + ['soldier_character_team2'], scale=global_scale, center=True)
        self.classic_image_team2 = load_ui(self.classic_image_team2, choose_class_path + ['classic_character_team2'], scale=global_scale, center=True)
        self.zombie_image_team2 = load_ui(self.zombie_image_team2, choose_class_path + ['zombie_character_team2'], scale=global_scale, center=True)
        self.score_icon_commando = load_ui(self.score_icon_commando, ['score_icon_commando'], scale=global_scale, center=True)
        self.score_icon_crown = load_ui(self.score_icon_crown, ['score_icon_crown'], scale=global_scale, center=True)
        self.score_icon_death = load_ui(self.score_icon_death, ['score_icon_death'], scale=global_scale, center=True)
        self.score_icon_miner = load_ui(self.score_icon_miner, ['score_icon_miner'], scale=global_scale, center=True)
        self.score_icon_rocketeer = load_ui(self.score_icon_rocketeer, ['score_icon_rocketeer'], scale=global_scale, center=True)
        self.score_icon_engineer = load_ui(self.score_icon_engineer, ['score_icon_engineer'], scale=global_scale, center=True)
        self.score_icon_sniper = load_ui(self.score_icon_sniper, ['score_icon_sniper'], scale=global_scale, center=True)
        self.specialist_icon_team1 = load_ui(self.specialist_icon_team1, choose_class_path + ['specialist_icon_team1'], scale=global_scale, center=True)
        self.specialist_icon_team2 = load_ui(self.specialist_icon_team2, choose_class_path + ['specialist_icon_team2'], scale=global_scale, center=True)
        self.specialist_image_team1 = load_ui(self.specialist_image_team1, choose_class_path + ['specialist_character_team1'], scale=global_scale, center=True)
        self.specialist_image_team2 = load_ui(self.specialist_image_team2, choose_class_path + ['specialist_character_team2'], scale=global_scale, center=True)
        self.score_icon_specialist = load_ui(self.score_icon_specialist, ['score_icon_specialist'], scale=global_scale, center=True)
        self.disabled_specialist_icon_team1 = load_ui(self.disabled_specialist_icon_team1, choose_class_path + ['disabled_specialist_icon_team1'], scale=global_scale, center=True)
        self.disabled_specialist_icon_team2 = load_ui(self.disabled_specialist_icon_team2, choose_class_path + ['disabled_specialist_icon_team2'], scale=global_scale, center=True)
        self.disabled_specialist_image_team1 = load_ui(self.disabled_specialist_image_team1, choose_class_path + ['disabled_specialist_character_team1'], scale=global_scale, center=True)
        self.disabled_specialist_image_team2 = load_ui(self.disabled_specialist_image_team2, choose_class_path + ['disabled_specialist_character_team2'], scale=global_scale, center=True)
        self.medic_icon_team1 = load_ui(self.medic_icon_team1, choose_class_path + ['medic_icon_team1'], scale=global_scale, center=True)
        self.medic_icon_team2 = load_ui(self.medic_icon_team2, choose_class_path + ['medic_icon_team2'], scale=global_scale, center=True)
        self.medic_image_team1 = load_ui(self.medic_image_team1, choose_class_path + ['medic_character_team1'], scale=global_scale, center=True)
        self.medic_image_team2 = load_ui(self.medic_image_team2, choose_class_path + ['medic_character_team2'], scale=global_scale, center=True)
        self.score_icon_medic = load_ui(self.score_icon_medic, ['score_icon_medic'], scale=global_scale, center=True)
        self.disabled_medic_icon_team1 = load_ui(self.disabled_medic_icon_team1, choose_class_path + ['disabled_medic_icon_team1'], scale=global_scale, center=True)
        self.disabled_medic_icon_team2 = load_ui(self.disabled_medic_icon_team2, choose_class_path + ['disabled_medic_icon_team2'], scale=global_scale, center=True)
        self.disabled_medic_image_team1 = load_ui(self.disabled_medic_image_team1, choose_class_path + ['disabled_medic_character_team1'], scale=global_scale, center=True)
        self.disabled_medic_image_team2 = load_ui(self.disabled_medic_image_team2, choose_class_path + ['disabled_medic_character_team2'], scale=global_scale, center=True)
        prefab_path = ingame + ['prefab_selection']
        self.blueprint_background = load_ui(self.blueprint_background, prefab_path + ['blueprint'], scale=global_scale, center=True)
        self.map_frame = load_ui(self.map_frame, ['mini_map', 'minimap_frame'], center=False, scale=1.0)
        self.big_map_frame = load_ui(self.big_map_frame, ['map', 'map_frame'], center=True, scale=1.0)
        self.weapon_frame_selected = load_ui(self.weapon_frame_selected, ['weapon_select', 'weapon_frame_selected'], center=True, scale=0.7)
        self.weapon_frame = load_ui(self.weapon_frame, ['weapon_select', 'weapon_frame'], scale=1.0, center=True)
        self.health_bar = load_ui(self.health_bar, ['health_bar', 'health_bar'], scale=1.0, center=True)
        self.health_bar.anchor_x = 35
        self.health_bar_frame = load_ui(self.health_bar_frame, ['health_bar', 'health_bar_frame'], scale=1.0, center=True)
        self.jetpack_fuel_bar = load_ui(self.jetpack_fuel_bar, ['jetpack_fuel', 'jetpack_fuel_bar'], scale=1.0, center=True)
        self.jetpack_fuel_bar.anchor_y = 0
        self.jetpack_fuel_frame = load_ui(self.jetpack_fuel_frame, ['jetpack_fuel', 'jetpack_fuel_frame'], scale=1.0, center=True)
        self.timer_frame = load_ui(self.timer_frame, ['timer', 'timer_frame'], scale=1.0)
        self.timer_icon = load_ui(self.timer_icon, ['timer', 'timer'], scale=1.0, center=True)
        self.score_frame = load_ui(self.score_frame, ['score', 'score_frame'], scale=1.0, center=False)
        mode_path = [
         'modes']
        self.mode_bar = load_ui(self.mode_bar, mode_path + ['progress_bar'], scale=1.0)
        self.mode_bar_base = load_ui(self.mode_bar_base, ['minimap_base'], scale=1.0)
        self.mode_bar_diamond = load_ui(self.mode_bar_diamond, ['minimap_diamond'], scale=1.0)
        self.ammo_frame = load_ui(self.ammo_frame, ['ammo', 'ammo_frame'], scale=1.0)
        self.tc_backplate = load_ui(self.tc_backplate, mode_path + ['tc_backplate'], scale=1.0)
        self.tc_frame = load_ui(self.tc_frame, mode_path + ['tc_frame'], scale=1.0)
        self.tc_letters[0] = load_ui(self.tc_letters[0], mode_path + ['tc_text_a'], scale=1.0)
        self.tc_letters[1] = load_ui(self.tc_letters[1], mode_path + ['tc_text_b'], scale=1.0)
        self.tc_letters[2] = load_ui(self.tc_letters[2], mode_path + ['tc_text_c'], scale=1.0)
        self.tc_letters[3] = load_ui(self.tc_letters[3], mode_path + ['tc_text_d'], scale=1.0)
        self.tc_letters[4] = load_ui(self.tc_letters[4], mode_path + ['tc_text_e'], scale=1.0)
        self.tc_letters[5] = load_ui(self.tc_letters[5], mode_path + ['tc_text_f'], scale=1.0)
        self.tc_letters[6] = load_ui(self.tc_letters[6], mode_path + ['tc_text_g'], scale=1.0)
        self.tc_letters[7] = load_ui(self.tc_letters[7], mode_path + ['tc_text_g'], scale=1.0)
        self.tc_letters[8] = load_ui(self.tc_letters[8], mode_path + ['tc_text_g'], scale=1.0)
        self.tc_letters[9] = load_ui(self.tc_letters[9], mode_path + ['tc_text_g'], scale=1.0)
        self.team1_intel_icon = load_ui(self.team1_intel_icon, icons + ['intel_blue_90'], scale=1.0, center=True)
        self.team2_intel_icon = load_ui(self.team2_intel_icon, icons + ['intel_green_90'], scale=1.0, center=True)
        self.host_icon = load_ui(self.host_icon, icons + ['leader_icon'], scale=global_scale, center=True, filtered=False)
        self.player_count_icon = load_ui(self.player_count_icon, icons + ['playercount_icon'], scale=global_scale, center=True, filtered=False)
        self.leaderboard_icon = load_ui(self.leaderboard_icon, icons + ['icon_leaderboards'], scale=1.0, center=True, filtered=False)
        self.options_icon = load_ui(self.options_icon, icons + ['icon_options'], scale=1.0, center=True, filtered=False)
        self.achievements_icon = load_ui(self.achievements_icon, icons + ['icon_achievements'], scale=1.0, center=True, filtered=False)
        self.tutorial_icon = load_ui(self.tutorial_icon, icons + ['icon_tutorial'], scale=1.0, center=True, filtered=False)
        self.head_1 = load_ui(self.head_1, icons + ['deuce_head_1'], scale=global_scale, center=True)
        self.head_color_1 = load_ui(self.head_color_1, icons + ['deuce_head_colour_1'], scale=global_scale, center=True)
        self.head_2 = load_ui(self.head_2, icons + ['deuce_head_2'], scale=global_scale, center=True)
        self.head_color_2 = load_ui(self.head_color_2, icons + ['deuce_head_colour_2'], scale=global_scale, center=True)
        self.hc_frame = load_ui(self.hc_frame, ['head_count', 'hc_frame'], scale=1.0)
        self.hc_frame_long = load_ui(self.hc_frame_long, ['head_count', 'hc_frame_long'], scale=1.0)
        dlc_path = [
         'dlc']
        self.buy_game_background = load_ui(self.buy_game_background, dlc_path + ['buy_aos_bg'], center=True)
        self.buy_game_lobby_background = load_ui(self.buy_game_lobby_background, dlc_path + ['buy_aos_lobby'], center=True)
        self.head_images = {TEAM1: (
               self.head_2, self.head_color_2), 
           TEAM2: (
               self.head_1, self.head_color_1)}
        self.class_icons = {CLASS_SOLDIER: {TEAM1: (self.soldier_icon_team1), TEAM2: (self.soldier_icon_team2)}, CLASS_SCOUT: {TEAM1: (self.scout_icon_team1), TEAM2: (self.scout_icon_team2)}, CLASS_ROCKETEER: {TEAM1: (self.pilot_icon_team1), TEAM2: (self.pilot_icon_team2)}, CLASS_ENGINEER: {TEAM1: (self.engineer_icon_team1), TEAM2: (self.engineer_icon_team2)}, CLASS_MINER: {TEAM1: (self.miner_icon_team1), TEAM2: (self.miner_icon_team2)}, CLASS_ZOMBIE: {TEAM1: (self.zombie_icon), TEAM2: (self.zombie_icon)}, CLASS_CLASSIC_SOLDIER: {TEAM1: (self.classic_icon_team1), TEAM2: (self.classic_icon_team2)}, CLASS_GANGSTER_1: {TEAM1: (self.gangster1_icon_team1), TEAM2: (self.gangster1_icon_team2)}, CLASS_GANGSTER_2: {TEAM1: (self.gangster2_icon_team1), TEAM2: (self.gangster2_icon_team2)}, CLASS_GANGSTER_3: {TEAM1: (self.gangster3_icon_team1), TEAM2: (self.gangster3_icon_team2)}, CLASS_GANGSTER_4: {TEAM1: (self.gangster4_icon_team1), TEAM2: (self.gangster4_icon_team2)}, CLASS_GANGSTER_VIP_1: {TEAM1: (self.boss_icon_team1), TEAM2: (self.boss_icon_team2)}, CLASS_GANGSTER_VIP_2: {TEAM1: (self.boss_icon_team1), TEAM2: (self.boss_icon_team2)}, CLASS_UGCBUILDER: {TEAM1: (self.ugcbuilder_icon_team1), TEAM2: (self.ugcbuilder_icon_team2)}, CLASS_SPECIALIST: {TEAM1: (self.specialist_icon_team1), TEAM2: (self.specialist_icon_team2)}, CLASS_MEDIC: {TEAM1: (self.medic_icon_team1), TEAM2: (self.medic_icon_team2)}}
        self.disabled_class_icons = {CLASS_SPECIALIST: {TEAM1: (self.disabled_specialist_icon_team1), TEAM2: (self.disabled_specialist_icon_team2)}, CLASS_MEDIC: {TEAM1: (self.disabled_medic_icon_team1), TEAM2: (self.disabled_medic_icon_team2)}}
        self.class_images = {CLASS_SOLDIER: {TEAM1: (self.soldier_image_team1), TEAM2: (self.soldier_image_team2)}, CLASS_SCOUT: {TEAM1: (self.scout_image_team1), TEAM2: (self.scout_image_team2)}, CLASS_ROCKETEER: {TEAM1: (self.pilot_image_team1), TEAM2: (self.pilot_image_team2)}, CLASS_ENGINEER: {TEAM1: (self.engineer_image_team1), TEAM2: (self.engineer_image_team2)}, CLASS_MINER: {TEAM1: (self.miner_image_team1), TEAM2: (self.miner_image_team2)}, CLASS_ZOMBIE: {TEAM1: (self.zombie_image_team1), TEAM2: (self.zombie_image_team2)}, CLASS_CLASSIC_SOLDIER: {TEAM1: (self.classic_image_team1), TEAM2: (self.classic_image_team2)}, CLASS_GANGSTER_1: {TEAM1: (self.soldier_image_team1), TEAM2: (self.soldier_image_team2)}, CLASS_GANGSTER_2: {TEAM1: (self.soldier_image_team1), TEAM2: (self.soldier_image_team2)}, CLASS_GANGSTER_3: {TEAM1: (self.soldier_image_team1), TEAM2: (self.soldier_image_team2)}, CLASS_GANGSTER_4: {TEAM1: (self.soldier_image_team1), TEAM2: (self.soldier_image_team2)}, CLASS_GANGSTER_VIP_1: {TEAM1: (self.soldier_image_team1), TEAM2: (self.soldier_image_team2)}, CLASS_GANGSTER_VIP_2: {TEAM1: (self.soldier_image_team1), TEAM2: (self.soldier_image_team2)}, CLASS_UGCBUILDER: {TEAM1: (self.ugcbuilder_image_team1), TEAM2: (self.ugcbuilder_image_team2)}, CLASS_SPECIALIST: {TEAM1: (self.specialist_image_team1), TEAM2: (self.specialist_image_team2)}, CLASS_MEDIC: {TEAM1: (self.medic_image_team1), TEAM2: (self.medic_image_team2)}}
        self.disabled_class_images = {CLASS_SPECIALIST: {TEAM1: (self.disabled_specialist_image_team1), TEAM2: (self.disabled_specialist_image_team2)}, CLASS_MEDIC: {TEAM1: (self.disabled_medic_image_team1), TEAM2: (self.disabled_medic_image_team2)}}
        self.score_icons = {CLASS_SOLDIER: (self.score_icon_commando), 
           CLASS_SCOUT: (self.score_icon_sniper), 
           CLASS_ROCKETEER: (self.score_icon_rocketeer), 
           CLASS_ENGINEER: (self.score_icon_engineer), 
           CLASS_MINER: (self.score_icon_miner), 
           CLASS_ZOMBIE: (self.score_icon_death), 
           CLASS_CLASSIC_SOLDIER: (self.score_icon_commando), 
           CLASS_GANGSTER_1: (self.score_icon_commando), 
           CLASS_GANGSTER_2: (self.score_icon_commando), 
           CLASS_GANGSTER_3: (self.score_icon_commando), 
           CLASS_GANGSTER_4: (self.score_icon_commando), 
           CLASS_GANGSTER_VIP_1: (self.score_icon_crown), 
           CLASS_GANGSTER_VIP_2: (self.score_icon_crown), 
           CLASS_SPECIALIST: (self.score_icon_specialist), 
           CLASS_MEDIC: (self.score_icon_medic)}
        self.score_icon_dead = self.score_icon_death
        self.score_icon_vip = self.score_icon_crown
        self.pf_blueprint_bg_default = load_ui(self.pf_blueprint_bg_default, ugc_tools + ['pf_blueprint_bg_default'], scale=global_scale, center=True)
        self.pf_select_marker = load_ui(self.pf_select_marker, ugc_tools + ['pf_select_marker'], scale=1.0, center=True, filtered=False)
        self.pf_selected_tab = load_ui(self.pf_selected_tab, ugc_tools + ['pf_selected_tab'], scale=1.0, center=True)
        self.pf_template_bg = load_ui(self.pf_template_bg, ugc_tools + ['pf_template_bg'], scale=1.0, center=True)
        self.pf_unselected_tab = load_ui(self.pf_unselected_tab, ugc_tools + ['pf_unselected_tab'], scale=1.0, center=True)
        self.prefab_selection_blueprint = load_ui(self.prefab_selection_blueprint, ugc_tools + ['prefab_selection_blueprint'], scale=1.0, center=True)
        self.ugc_select_bg = load_ui(self.ugc_select_bg, ugc_tools + ['ugc_select_bg'], scale=1.0, center=True)
        self.gd_select_marker = load_ui(self.gd_select_marker, ugc_tools + ['gd_select_marker'], scale=1.0, center=True, filtered=False)
        self.gdata_blueprint_bg_default = load_ui(self.gdata_blueprint_bg_default, ugc_tools + ['gdata_blueprint_bg_default'], scale=global_scale, center=True)
        self.gdata_selected_tab = load_ui(self.gdata_selected_tab, ugc_tools + ['gdata_selected_tab'], scale=1.0, center=True)
        self.gdata_template_bg = load_ui(self.gdata_template_bg, ugc_tools + ['gdata_template_bg'], scale=1.0, center=True)
        self.gdata_unselected_tab = load_ui(self.gdata_unselected_tab, ugc_tools + ['gdata_unselected_tab'], scale=1.0, center=True)
        return

    def clear(self):
        self.splash_image = None
        self.main_image = None
        self.score_dominated_image = None
        self.score_dominating_image = None
        self.main_menu_frame = None
        self.name_frame = None
        self.frame_3button_menu = None
        self.frame_nav_bar_small = None
        self.global_scale = 0.64
        self.green_highlight_glow = None
        self.green_highlight_line = None
        self.button_left = None
        self.button_mid = None
        self.button_right = None
        self.button_hover_left = None
        self.button_hover_mid = None
        self.button_hover_right = None
        self.button_press_left = None
        self.button_press_mid = None
        self.button_press_right = None
        self.button_ready_left = None
        self.button_ready_mid = None
        self.button_ready_right = None
        self.main_menu_button_square = None
        self.main_menu_button_square_hover = None
        self.main_menu_button_square_press = None
        self.button_square = None
        self.button_square_hover = None
        self.button_square_press = None
        self.button_glow_left = None
        self.button_glow_mid = None
        self.button_glow_right = None
        self.button_glow_press_left = None
        self.button_glow_press_mid = None
        self.button_glow_press_right = None
        self.button_glow_hover_left = None
        self.button_glow_hover_mid = None
        self.button_glow_hover_right = None
        self.button_glow = None
        self.panel_frame = None
        self.panel_header_dark_frame = None
        self.large_frame = None
        self.small_frame = None
        self.message_box_frame = None
        self.message_box_with_buttons_frame = None
        self.message_box_extended_frame = None
        self.loading_map_frame = None
        self.searching_logo = None
        self.searching_tutorial = None
        self.server_content_frame = None
        self.server_tab_name_frame = None
        self.favorite_star_button = None
        self.favorite_star = None
        self.checkmark = None
        self.star_checkmark = None
        self.star_checkmark_off = None
        self.leaderboard_frame = None
        self.filter_up = None
        self.filter_down = None
        self.filter_up_white = None
        self.filter_down_white = None
        self.edit_icon = None
        self.checkbox_background = None
        self.round_control_frame = None
        self.collapse_plus = None
        self.collapse_minus = None
        self.red_header_center = None
        self.red_header_left = None
        self.red_header_right = None
        self.left_arrow = None
        self.right_arrow = None
        self.up_arrow = None
        self.down_arrow = None
        self.scroll_top = None
        self.scroll_mid = None
        self.scroll_bottom = None
        self.scroll_bar_top = None
        self.scroll_bar_mid = None
        self.scroll_bar_bottom = None
        self.scroll_bar_left = None
        self.scroll_bar_hmid = None
        self.scroll_bar_right = None
        self.map_placeholder = None
        self.reset_map_previews()
        self.map_preview_ugc = None
        self.quit_icon = None
        self.main_menu_icon = None
        self.back_icon = None
        self.right_icon = None
        self.ingame_settings_frame = None
        self.ingame_settings_content_frame = None
        self.settings_tooltip_frame = None
        self.settings_tooltip_frame_ingame = None
        self.bullet_hole = None
        self.bullet_hole_disabled = None
        self.bullet_slider = None
        self.settings_matchsettings_frame = None
        self.settings_frame_disabled = None
        self.main_settings_frame = None
        self.volume_bar = None
        self.graphics_settings_frame = None
        self.controls_frame = None
        self.controls_frame_content = None
        self.generic_tab_active = None
        self.generic_tab_inactive = None
        self.profile_stats_bg = None
        self.profile_level_bar_bg = None
        self.progress_bullet = None
        self.not_classic_loading_infographic_imagenames = {A2435: 'infographic_tdm', 
           A2441: 'infographic_tdm', 
           A2436: 'infographic_dem', 
           A2437: 'infographic_zom', 
           A2438: 'infographic_mh', 
           A2439: 'infographic_oc', 
           A2440: 'infographic_dia', 
           A2442: 'infographic_vip', 
           A2444: 'infographic_tc', 
           A2443: 'infographic_ctf', 
           A2445: 'infographic_tut', 
           A2447: 'infographic_ugc'}
        self.classic_loading_infographic_imagenames = {A2435: 'infographic_tdm', 
           A2441: 'infographic_tdm', 
           A2436: 'infographic_dem', 
           A2437: 'infographic_zom', 
           A2438: 'infographic_mh', 
           A2439: 'infographic_oc', 
           A2440: 'infographic_dia', 
           A2442: 'infographic_vip', 
           A2444: 'infographic_tc', 
           A2443: 'infographic_classic_ctf', 
           A2445: 'infographic_tut', 
           A2447: 'infographic_ugc'}
        self.mafia_loading_infographic_imagenames = {A2435: 'infographic_tdm', 
           A2441: 'infographic_tdm', 
           A2436: 'infographic_dem', 
           A2437: 'infographic_zom', 
           A2438: 'infographic_mh', 
           A2439: 'infographic_oc', 
           A2440: 'infographic_dia', 
           A2442: 'infographic_mafia_vip', 
           A2444: 'infographic_mafia_tc', 
           A2443: 'infographic_ctf', 
           A2445: 'infographic_tut', 
           A2447: 'infographic_ugc'}
        self.loading_map_imagenames = {'Alcatraz': 'loading_mapimage_alcatraz', 
           'Ancient Egypt': 'loading_mapimage_ancientegypt', 
           'Arctic Base': 'loading_mapimage_arcticbase', 
           'Atlantis': 'loading_mapimage_atlantis', 
           'Block Ness': 'loading_mapimage_blockness', 
           'Bran Castle': 'loading_mapimage_brancastle', 
           'Castle Wars': 'loading_mapimage_castlewars', 
           'City Of Chicago': 'loading_mapimage_cityofchicago', 
           'City of Chicago': 'loading_mapimage_cityofchicago', 
           'Classic': 'loading_mapimage_classic', 
           'Crossroads': 'loading_mapimage_crossroads', 
           'Double Dragon': 'loading_mapimage_doubledragon', 
           'Dragon Island': 'loading_mapimage_dragonisland', 
           'Frontier': 'loading_mapimage_frontier', 
           'Great Wall': 'loading_mapimage_greatwall', 
           'Hiesville': 'loading_mapimage_hiesville', 
           'Ice Train': 'loading_mapimage_icetrain', 
           'Invasion': 'loading_mapimage_invasion', 
           'London': 'loading_mapimage_london', 
           'Lunar Base': 'loading_mapimage_lunarbase', 
           'Mall Of War': 'loading_mapimage_mallowar', 
           'Mayan Jungle': 'loading_mapimage_mayanjungle', 
           'Mount Rushmoore': 'loading_mapimage_mayanjungle', 
           'Orc Fortress': 'loading_mapimage_orcfortress', 
           'Pool Table': 'loading_mapimage_pooltable', 
           'Spooky Mansion': 'loading_mapimage_spookymansion', 
           'The Colosseum': 'loading_mapimage_thecolosseum', 
           'Tokyo Neon': 'loading_mapimage_tokyoneon', 
           'To The Bridge': 'loading_mapimage_tothebridge', 
           'Trenches': 'loading_mapimage_trenches', 
           'Winter Valley': 'loading_mapimage_wintervalley', 
           'WW1': 'loading_mapimage_ww1', 
           'Training': 'loading_mapimage_tut', 
           'Default_map_image': 'loading_mapimage_default'}
        self.choose_team_frame = None
        self.loading_bar_bg = None
        self.loading_tab_bg = None
        self.mode_image_names = {A2435: 'letterbox_tdm', 
           A2441: 'letterbox_tdm', 
           A2436: 'letterbox_demolition', 
           A2437: 'letterbox_zombie', 
           A2438: 'letterbox_multihill', 
           A2439: 'letterbox_occupation', 
           A2440: 'letterbox_diamondmine', 
           A2442: 'letterbox_vip_gangster', 
           A2443: 'letterbox_ctf', 
           A2446: 'letterbox_classic', 
           A2444: 'letterbox_territory'}
        self.mode_image_letterbox_random = None
        self.mode_image_letterbox_multi_mode = None
        self.mode_images_letterbox = {}
        self.big_text_frame = None
        self.view_scores_frame = None
        self.ugc_tab_frame = None
        self.view_game_stats_frame = None
        self.view_game_stats_rankbar_bar = None
        self.view_game_stats_rankbar_stroke_glow = None
        self.change_team_frame = None
        self.score_text_frame = None
        self.four_items_frame = None
        self.five_items_frame = None
        self.pause_menu_frame = None
        self.pause_menu_frame_big = None
        self.screenshot_frame = None
        self.highlight_scoreboard_blue = None
        self.highlight_scoreboard_green = None
        self.highlight_scoreboard_white = None
        self.hover_scoreboard_blue = None
        self.hover_scoreboard_green = None
        self.hover_scoreboard_white = None
        self.in_game_class_frame = None
        self.class_background_frame = None
        self.class_background_frame5 = None
        self.class_selected_frame = None
        self.loadout_item_background = None
        self.loadout_item_background_disabled = None
        self.loadout_info_frame = None
        self.disabled_loadout_info_frame = None
        self.class_info_frame_left = None
        self.class_info_frame_right = None
        self.disabled_class_info_frame_left = None
        self.disabled_class_info_frame_right = None
        self.prefab_info_frame = None
        self.class_frame_arrow = None
        self.disabled_class_frame_arrow = None
        self.miner_icon_team1 = None
        self.scout_icon_team1 = None
        self.pilot_icon_team1 = None
        self.engineer_icon_team1 = None
        self.soldier_icon_team1 = None
        self.classic_icon_team1 = None
        self.ugcbuilder_icon_team1 = None
        self.miner_icon_team2 = None
        self.scout_icon_team2 = None
        self.pilot_icon_team2 = None
        self.engineer_icon_team2 = None
        self.soldier_icon_team2 = None
        self.classic_icon_team2 = None
        self.ugcbuilder_icon_team2 = None
        self.zombie_icon = None
        self.miner_image_team1 = None
        self.scout_image_team1 = None
        self.pilot_image_team1 = None
        self.engineer_image_team1 = None
        self.soldier_image_team1 = None
        self.classic_image_team1 = None
        self.zombie_image_team1 = None
        self.ugcbuilder_image_team1 = None
        self.gangster1_icon_team1 = None
        self.gangster2_icon_team1 = None
        self.gangster3_icon_team1 = None
        self.gangster4_icon_team1 = None
        self.boss_icon_team1 = None
        self.gangster1_icon_team2 = None
        self.gangster2_icon_team2 = None
        self.gangster3_icon_team2 = None
        self.gangster4_icon_team2 = None
        self.boss_icon_team2 = None
        self.miner_image_team2 = None
        self.scout_image_team2 = None
        self.pilot_image_team2 = None
        self.engineer_image_team2 = None
        self.soldier_image_team2 = None
        self.zombie_image_team2 = None
        self.ugcbuilder_image_team2 = None
        self.classic_image_team2 = None
        self.score_icon_commando = None
        self.score_icon_crown = None
        self.score_icon_death = None
        self.score_icon_miner = None
        self.score_icon_rocketeer = None
        self.score_icon_engineer = None
        self.score_icon_sniper = None
        self.specialist_icon_team1 = None
        self.specialist_icon_team2 = None
        self.specialist_image_team1 = None
        self.specialist_image_team2 = None
        self.disabled_specialist_icon_team1 = None
        self.disabled_specialist_icon_team2 = None
        self.disabled_specialist_image_team1 = None
        self.disabled_specialist_image_team2 = None
        self.score_icon_specialist = None
        self.medic_icon_team1 = None
        self.medic_icon_team2 = None
        self.medic_image_team1 = None
        self.medic_image_team2 = None
        self.disabled_medic_icon_team1 = None
        self.disabled_medic_icon_team2 = None
        self.disabled_medic_image_team1 = None
        self.disabled_medic_image_team2 = None
        self.score_icon_medic = None
        self.blueprint_background = None
        self.map_frame = None
        self.big_map_frame = None
        self.weapon_frame_selected = None
        self.weapon_frame = None
        self.health_bar = None
        self.health_bar_frame = None
        self.jetpack_fuel_bar = None
        self.jetpack_fuel_frame = None
        self.timer_frame = None
        self.timer_icon = None
        self.score_frame = None
        self.mode_bar = None
        self.mode_bar_base = None
        self.mode_bar_diamond = None
        self.tc_backplate = None
        self.tc_frame = None
        self.tc_letters = [None, None, None, None, None, None, None, None, None, None]
        self.ammo_frame = None
        self.team1_intel_icon = None
        self.team2_intel_icon = None
        self.head_1 = None
        self.head_color_1 = None
        self.head_2 = None
        self.head_color_2 = None
        self.hc_frame = None
        self.hc_frame_long = None
        self.host_icon = None
        self.player_count_icon = None
        self.leaderboard_icon = None
        self.options_icon = None
        self.achievements_icon = None
        self.tutorial_icon = None
        self.buy_game_background = None
        self.buy_game_lobby_background = None
        self.head_images = {}
        self.class_icons = {}
        self.class_images = {}
        self.score_icons = {}
        self.key_images = {}
        for number_key in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10'):
            self.key_images[number_key] = [
             None, None]

        self.ugc_tool_images = {}
        for ugc_tool_id in UGC_TOOL_IMAGES.iterkeys():
            self.ugc_tool_images[ugc_tool_id] = None

        self.pf_blueprint_bg_default = None
        self.pf_select_marker = None
        self.pf_selected_tab = None
        self.pf_template_bg = None
        self.pf_unselected_tab = None
        self.prefab_selection_blueprint = None
        self.ugc_select_bg = None
        self.gd_select_marker = None
        self.gdata_blueprint_bg_default = None
        self.gdata_selected_tab = None
        self.gdata_template_bg = None
        self.gdata_unselected_tab = None
        create_shadow_vbo()
        return


global_images = GlobalImages()

def load_global_images(load_ui_frame_large=True):
    global_images.load_global_images(load_ui_frame_large)


def set_main_skin(skin):
    global_images.set_skin(skin)


def load_skinned_loading_screen():
    global_images.load_loading_screen()


load_global_images()
PARTICLE_IMAGE = None
particle_lut_image = None
particle_glow_block = None
particle_tumbling_cube = None
particle_smoke_trail = None
particle_smoke_lut = None
particle_pickup_twinkle = None
particle_snowke_trail = None

def load_particle_textures():
    global PARTICLE_IMAGE
    global particle_glow_block
    global particle_lut_image
    global particle_pickup_twinkle
    global particle_smoke_lut
    global particle_smoke_trail
    global particle_snowke_trail
    global particle_tumbling_cube
    PARTICLE_IMAGE = image.load_texture('block128', none_resource=True, add_path=True)
    particle_lut_image = image.load_texture('tumbling_cube_lut', none_resource=True, add_path=True)
    particle_glow_block = image.load_texture('Tumbling_Glowcube_anim_8x8', none_resource=True, add_path=True)
    particle_tumbling_cube = image.load_texture('Tumbling_cube_anim', none_resource=True, add_path=True)
    particle_smoke_trail = image.load_texture('SmokeTrail_anim_8x8', none_resource=True, add_path=True)
    particle_smoke_lut = image.load_texture('particle_lut', none_resource=True, add_path=True)
    particle_pickup_twinkle = image.load_texture('PickUp_Twinkle_anim_4x4', none_resource=True, add_path=True)
    particle_snowke_trail = image.load_texture('SnowkeTrail_anim_8x8', none_resource=True, add_path=True)


load_particle_textures()

class SkyboxTextures(object):

    def __init__(self, skybox_tex_name):
        self.skybox_top = image.load_texture(skybox_tex_name + '_00', filtered=False)
        self.skybox_1 = image.load_texture(skybox_tex_name + '_01', filtered=False)
        self.skybox_2 = image.load_texture(skybox_tex_name + '_02', filtered=False)
        self.skybox_3 = image.load_texture(skybox_tex_name + '_03', filtered=False)
        self.skybox_4 = image.load_texture(skybox_tex_name + '_04', filtered=False)
        self.skybox_width = self.skybox_top.width
        self.skybox_height = self.skybox_top.height


def get_skybox(skybox_tex_name):
    return SkyboxTextures(skybox_tex_name)

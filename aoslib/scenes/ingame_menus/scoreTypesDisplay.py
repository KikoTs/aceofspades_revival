from pyglet import gl
from shared.constants import *
from shared.constants_gamemode import *
from aoslib.text import draw_text_with_size_validation, score_types_heading_font, score_types_font, score_types_subheading_font, medium_edo_ui_font, big_edo_ui_font
from aoslib.gui import VerticalScrollBar
from aoslib.media import MUSIC_AUDIO_ZONE, HUD_AUDIO_ZONE
from aoslib.scenes import Scene, ElementScene
from aoslib import strings
from aoslib.draw import draw_quad
from aoslib.common import collides
from aoslib.images import global_images
from aoslib.image import Sprite
from aoslib.common import *
from aoslib.scenes.frontend.expandableListPanel import ExpandableListPanel
from aoslib.scenes.main.multiColumnPanelItem import MultiColumnPanelItem
from aoslib.scenes.main.categoryListItem import CategoryListItem
from aoslib.scenes.frontend.panelBase import BACKGROUND_NONE

class ScoreType(object):

    def __init__(self, reason=0, mode=0, score=0, score_interval=0, score_text='', percent=False, seconds=False, blocks=False, heading=False, heading_text=0):
        self.reason = reason
        self.mode = mode
        self.score = score
        self.score_interval = score_interval
        self.score_text = score_text
        self.percent = percent
        self.seconds = seconds
        self.blocks = blocks
        self.heading = heading
        self.heading_text = heading_text


class ScoreTypesDisplay(ElementScene):
    scoreTypesList = []
    filterList = []
    setup = False

    def setup_scores(self, x=73, y=453, width=654, height=280, mode_filter=[], friendly_fire=False, draw_solid_border=True):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = False
        self.elements = []
        self.friendly_fire = friendly_fire
        self.initialize_scoreTypes(mode_filter)
        self.score_types_expandable_list = ExpandableListPanel(self.manager)
        self.elements.append(self.score_types_expandable_list)
        self.setup = True
        self.max_height = height
        self.setup_expandable_list(x, y, width, height)

    def setup_expandable_list(self, x, y, width, height):
        if len(self.scoreTypesList) > 0:
            self.score_types_expandable_list.initialise_ui('', x, y, width, height, has_header=False)
            self.score_types_expandable_list.set_background(background=BACKGROUND_NONE)
            self.score_types_expandable_list.visible = False
            self.score_types_expandable_list.reset_list()
            for filter in self.filterList:
                filter_score_types = []
                column_widths = [330, 200]
                for score_type in self.scoreTypesList:
                    if score_type[0] == filter[0]:
                        score_type = (
                         score_type[1], score_type[2])
                        filter_score_types.append(score_type)

                self.add_category(filter[1], column_widths, filter_score_types)

            self.score_types_expandable_list.visible = True
        self.score_types_expandable_list.on_scroll(0, True)

    def add_category(self, name, column_widths, category_texts):
        category_row = CategoryListItem(name, is_expandable=True, sub_row_colours=[(87, 83, 74, 150), (54, 51, 44, 150)], draw_background_texture=True)
        category_row.center_text = False
        category_row.small_font = medium_edo_ui_font
        category_row.medium_font = big_edo_ui_font
        rows = []
        for column_texts in category_texts:
            row = MultiColumnPanelItem(column_widths, column_texts)
            row.selectable_row = False
            row.center_text = False
            rows.append(row)

        self.score_types_expandable_list.add_list_item(category_row, rows)

    def draw(self):
        if not self.setup:
            return
        for element in self.elements:
            if not element.visible:
                continue
            element.draw()

    def initialize_scoreTypes(self, filter_modes=[]):
        del self.scoreTypesList[:]
        del self.filterList[:]
        self.add_score_type(filter_modes, ScoreType(mode=A2441, heading=True, heading_text=strings.MODE_SPECIFIC_SCORE_TYPES))
        self.add_score_type(filter_modes, ScoreType(KILL_SCORE_DISTRACT_REASON, A2441, A2518))
        self.add_score_type(filter_modes, ScoreType(mode=A2444, heading=True, heading_text=strings.MODE_SPECIFIC_SCORE_TYPES))
        self.add_score_type(filter_modes, ScoreType(TC_OCCUPY_SCORE_REASON, A2444, A2554, A2553, seconds=True))
        self.add_score_type(filter_modes, ScoreType(TC_CONTEND_SCORE_REASON, A2444, A2560, A2559, seconds=True))
        self.add_score_type(filter_modes, ScoreType(TC_CLAIM_SCORE_REASON, A2444, A2555))
        self.add_score_type(filter_modes, ScoreType(TC_CONTROL_SCORE_REASON, A2444, A2556))
        self.add_score_type(filter_modes, ScoreType(TC_DEFEND_SCORE_REASON, A2444, A2557))
        self.add_score_type(filter_modes, ScoreType(TC_ASSAULT_SCORE_REASON, A2444, A2558))
        self.add_score_type(filter_modes, ScoreType(mode=A2440, heading=True, heading_text=strings.MODE_SPECIFIC_SCORE_TYPES))
        self.add_score_type(filter_modes, ScoreType(DIA_CARRY_SCORE_REASON, A2440, A2614, A2615, seconds=True))
        self.add_score_type(filter_modes, ScoreType(DIA_ESCORT_SCORE_REASON, A2440, A2616, A2617, seconds=True))
        self.add_score_type(filter_modes, ScoreType(DIA_CAPTURE_SCORE_REASON, A2440, A2609))
        self.add_score_type(filter_modes, ScoreType(DIA_UNCOVER_SCORE_REASON, A2440, A2608))
        self.add_score_type(filter_modes, ScoreType(DIA_DISTRACT_SCORE_REASON, A2440, A2620))
        self.add_score_type(filter_modes, ScoreType(DIA_CARRIER_DEFEND_SCORE_REASON, A2440, A2621))
        self.add_score_type(filter_modes, ScoreType(DIA_DEFEND_SCORE_REASON, A2440, A2623))
        self.add_score_type(filter_modes, ScoreType(DIA_ASSAULT_SCORE_REASON, A2440, A2625))
        self.add_score_type(filter_modes, ScoreType(DIA_INTERCEPT_SCORE_REASON, A2440, A2626))
        self.add_score_type(filter_modes, ScoreType(mode=A2437, heading=True, heading_text=strings.MODE_SPECIFIC_SCORE_TYPES))
        self.add_score_type(filter_modes, ScoreType(ZOM_SURVIVE_SCORE_REASON, A2437, A2528, A2529, seconds=True))
        self.add_score_type(filter_modes, ScoreType(ZOM_LASTMAN_SCORE_REASON, A2437, A2530, A2531, seconds=True))
        self.add_score_type(filter_modes, ScoreType(ZOM_KILLSURVIVOR_SCORE_REASON, A2437, A2532))
        self.add_score_type(filter_modes, ScoreType(ZOM_LASTMAN_ZOMBIEKILL_SCORE_REASON, A2437, A2533))
        self.add_score_type(filter_modes, ScoreType(mode=A2442, heading=True, heading_text=strings.MODE_SPECIFIC_SCORE_TYPES))
        self.add_score_type(filter_modes, ScoreType(VIP_SURVIVE_SCORE_REASON, A2442, A2591, A2592, seconds=True))
        self.add_score_type(filter_modes, ScoreType(VIP_ESCORT_SCORE_REASON, A2442, A2593, A2594, seconds=True))
        self.add_score_type(filter_modes, ScoreType(VIP_KILLENEMYVIP_SCORE_REASON, A2442, 0, A2586, strings.VIP_SCORE, percent=True))
        self.add_score_type(filter_modes, ScoreType(VIP_DISTRACT_SCORE_REASON, A2442, A2598))
        self.add_score_type(filter_modes, ScoreType(VIP_KILL_SCORE_REASON, A2442, A2588))
        self.add_score_type(filter_modes, ScoreType(VIP_DEFEND_SCORE_REASON, A2442, A2599))
        self.add_score_type(filter_modes, ScoreType(mode=A2436, heading=True, heading_text=strings.MODE_SPECIFIC_SCORE_TYPES))
        self.add_score_type(filter_modes, ScoreType(DEM_DESTROY_SCORE_REASON, A2436, A2632, A2633, blocks=True))
        self.add_score_type(filter_modes, ScoreType(DEM_REPAIR_SCORE_REASON, A2436, A2634, A2635, blocks=True))
        self.add_score_type(filter_modes, ScoreType(DEM_DEFEND_SCORE_REASON, A2436, A2637))
        self.add_score_type(filter_modes, ScoreType(DEM_ASSAULT_SCORE_REASON, A2436, A2638))
        self.add_score_type(filter_modes, ScoreType(mode=A2443, heading=True, heading_text=strings.MODE_SPECIFIC_SCORE_TYPES))
        self.add_score_type(filter_modes, ScoreType(CTF_CARRY_SCORE_REASON, A2443, A2647, A2648, seconds=True))
        self.add_score_type(filter_modes, ScoreType(CTF_ESCORT_SCORE_REASON, A2443, A2649, A2650, seconds=True))
        self.add_score_type(filter_modes, ScoreType(CTF_CAPTURE_SCORE_REASON, A2443, A2642))
        self.add_score_type(filter_modes, ScoreType(CTF_CLAIM_SCORE_REASON, A2443, A2661))
        self.add_score_type(filter_modes, ScoreType(CTF_DISTRACT_SCORE_REASON, A2443, A2653))
        self.add_score_type(filter_modes, ScoreType(CTF_DEFEND_SCORE_REASON, A2443, A2656))
        self.add_score_type(filter_modes, ScoreType(CTF_ASSAULT_SCORE_REASON, A2443, A2658))
        self.add_score_type(filter_modes, ScoreType(CTF_ASSAULT_ENEMY_SCORE_REASON, A2443, A2659))
        self.add_score_type(filter_modes, ScoreType(CTF_CARRIER_DEFEND_SCORE_REASON, A2443, A2654))
        self.add_score_type(filter_modes, ScoreType(CTF_INTERCEPT_SCORE_REASON, A2443, A2660))
        self.add_score_type(filter_modes, ScoreType(mode=A2439, heading=True, heading_text=strings.MODE_SPECIFIC_SCORE_TYPES))
        self.add_score_type(filter_modes, ScoreType(OCC_OCCUPY_SCORE_REASON, A2439, A2578, A2579, seconds=True))
        self.add_score_type(filter_modes, ScoreType(OCC_CARRY_SCORE_REASON, A2439, A2568, A2569, seconds=True))
        self.add_score_type(filter_modes, ScoreType(OCC_BOOM_SCORE_REASON, A2439, A2567))
        self.add_score_type(filter_modes, ScoreType(OCC_DISTRACT_SCORE_REASON, A2439, A2570))
        self.add_score_type(filter_modes, ScoreType(OCC_CARRIER_DEFEND_SCORE_REASON, A2439, A2571))
        self.add_score_type(filter_modes, ScoreType(OCC_DEFEND_SCORE_REASON, A2439, A2573))
        self.add_score_type(filter_modes, ScoreType(OCC_ASSAULT_SCORE_REASON, A2439, A2575))
        self.add_score_type(filter_modes, ScoreType(OCC_SURVIVE_SCORE_REASON, A2439, A2577))
        self.add_score_type(filter_modes, ScoreType(OCC_INTERCEPT_SCORE_REASON, A2439, A2576))
        self.add_score_type(filter_modes, ScoreType(mode=A2438, heading=True, heading_text=strings.MODE_SPECIFIC_SCORE_TYPES))
        self.add_score_type(filter_modes, ScoreType(MH_OCCUPY_SCORE_REASON, A2438, A2540, A2541, seconds=True))
        self.add_score_type(filter_modes, ScoreType(MH_FIRST_SCORE_REASON, A2438, A2544))
        self.add_score_type(filter_modes, ScoreType(MH_CLAIM_SCORE_REASON, A2438, A2545))
        self.add_score_type(filter_modes, ScoreType(MH_CONTROL_SCORE_REASON, A2438, A2546))
        self.add_score_type(filter_modes, ScoreType(MH_DEFEND_SCORE_REASON, A2438, A2542))
        self.add_score_type(filter_modes, ScoreType(MH_ASSAULT_SCORE_REASON, A2438, A2543))
        self.add_score_type(filter_modes, ScoreType(MH_CONTEST_SCORE_REASON, A2438, A2547))
        self.add_score_type(filter_modes, ScoreType(mode=A2435, heading=True, heading_text=strings.GENERIC_SCORE_TYPES))
        self.add_score_type(filter_modes, ScoreType(KILL_SCORE_HEADSHOT_REASON, A2435, A2506))
        self.add_score_type(filter_modes, ScoreType(KILL_SCORE_MELEE_REASON, A2435, A2507))
        self.add_score_type(filter_modes, ScoreType(KILL_SCORE_REASON, A2435, A2505))
        self.add_score_type(filter_modes, ScoreType(KILL_SCORE_ASSIST_REASON, A2435, A2508))
        self.add_score_type(filter_modes, ScoreType(KILL_SCORE_REVENGE_REASON, A2435, A2509))
        self.add_score_type(filter_modes, ScoreType(KILL_SCORE_PAYBACK_REASON, A2435, A2510))
        self.add_score_type(filter_modes, ScoreType(KILL_SCORE_RELOAD_REASON, A2435, A2511))
        self.add_score_type(filter_modes, ScoreType(KILL_SCORE_DEFEND_REASON, A2435, A2512))
        self.add_score_type(filter_modes, ScoreType(SUICIDE_SCORE_REASON, A2435, A2513))
        if self.friendly_fire:
            self.add_score_type(filter_modes, ScoreType(KILL_SCORE_TEAMKILL_REASON, A2435, A2514))

    def on_scroll(self, value, silent=False):
        if self.media is not None and not silent:
            self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        return

    def get_interval_text(self, scoreType):
        interval_text1 = ''
        interval_text2 = ''
        if scoreType.score_interval != 0:
            if scoreType.percent:
                interval_text1 = strings.PERCENT_INTERVAL.format(str(int(scoreType.score_interval)))
            elif scoreType.blocks:
                interval_text2 = ' ' + strings.BLOCKS_INTERVAL.format(str(int(scoreType.score_interval)))
            elif scoreType.seconds:
                interval_text2 = ' ' + strings.SECONDS_INTERVAL.format(str(int(scoreType.score_interval)))
        if scoreType.score_text is '':
            if scoreType.score > 0:
                score_text = '+' + str(int(scoreType.score))
            else:
                score_text = str(int(scoreType.score))
            text = interval_text1 + score_text + interval_text2
        else:
            text = interval_text1 + scoreType.score_text + interval_text2
        return text

    def add_score_type(self, filter_modes, score_type):
        for mode in filter_modes:
            if mode is score_type.mode:
                if not score_type.heading:
                    score_type_text = (
                     score_type.mode, strings.get_by_id(SCORE_REASON_CODES[score_type.reason]), self.get_interval_text(score_type))
                    self.scoreTypesList.append(score_type_text)
                if score_type.heading:
                    filter = (
                     score_type.mode, score_type.heading_text)
                    self.filterList.append(filter)

    def on_mouse_press(self, x, y, button, modifiers):
        ElementScene.on_mouse_press(self, x, y, button, modifiers)

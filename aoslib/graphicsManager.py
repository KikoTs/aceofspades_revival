import operator

class ScreenResolution:

    def __init__(self, width=640, height=480, resolution_string=None):
        self.width = width
        self.height = height
        if resolution_string is None:
            self.resolution_string = '%dx%d' % (width, height)
        else:
            self.resolution_string = resolution_string
        return


class GraphicsManager(object):
    screen_modes = None
    config = None
    graphics_tab_resolutions_populate_callback = None
    screen_resolutions_dict = {}
    screen_resolutions_by_string = {}
    current_resolution = None
    current_window = None
    current_py_config = None
    compatible_options = {'double_buffer': True, 
       'depth_size': 24}
    is_msaa_supported = False
    msaa_options = (0, 2, 4, 8)

    def initialise(self, config):
        self.config = config
        for mode in self.screen_modes:
            resolution = ScreenResolution(mode.width, mode.height)
            self.screen_resolutions_dict[(int(mode.width), int(mode.height))] = resolution
            self.config.screen_resolutions_by_string[resolution.resolution_string] = resolution

        self.config.sorted_screen_resolutions_for_gui = sorted(self.screen_resolutions_dict.iteritems(), key=operator.itemgetter(0))
        self.update_resolutions()
        try:
            self.current_resolution = self.screen_resolutions_dict[(int(self.config.width), int(self.config.height))]
        except:
            self.current_resolution = ScreenResolution(int(self.config.width), int(self.config.height))

    def update_resolutions(self):
        if self.config.fullscreen:
            height = self.config.height
            width = self.config.width
        else:
            height = self.config.window_height
            width = self.config.window_width
        current_resolution_index = -1
        custom_resolution_item = None
        added_custom = False
        for index, item in enumerate(self.config.sorted_screen_resolutions_for_gui):
            if item[1].width == width and item[1].height == height:
                current_resolution_index = index
            elif item[1].width == 0 and item[1].height == 0:
                custom_resolution_item = item
            if current_resolution_index != -1 and custom_resolution_item != None:
                break

        if current_resolution_index != -1 and custom_resolution_item != None:
            del self.config.screen_resolutions_by_string[custom_resolution_item[1].resolution_string]
            self.config.sorted_screen_resolutions_for_gui.remove(custom_resolution_item)
            current_resolution_index -= 1
        elif current_resolution_index == -1 and custom_resolution_item == None:
            from aoslib import strings
            resolution = ScreenResolution(0, 0, strings.CUSTOM)
            self.screen_resolutions_dict[(0, 0)] = resolution
            self.config.screen_resolutions_by_string[resolution.resolution_string] = resolution
            self.config.sorted_screen_resolutions_for_gui = sorted(self.screen_resolutions_dict.iteritems(), key=operator.itemgetter(0))
            current_resolution_index = 0
            added_custom = True
        elif current_resolution_index == -1:
            current_resolution_index = 0
        self.config.resolution = current_resolution_index
        self.config.set('resolution', current_resolution_index)
        if self.graphics_tab_resolutions_populate_callback != None:
            self.graphics_tab_resolutions_populate_callback(True, current_resolution_index)
        return

    def is_custom_resolution(self, width, height):
        custom = False
        found = False
        for index, item in enumerate(self.config.sorted_screen_resolutions_for_gui):
            if item[1].width == width and item[1].height == height:
                found = True
                from aoslib import strings
                if item[1].resolution_string == strings.CUSTOM:
                    custom = True
                    break

        if not found:
            custom = True
        return custom


graphics_manager = GraphicsManager()

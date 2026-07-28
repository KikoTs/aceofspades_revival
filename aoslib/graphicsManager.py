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
        self.screen_resolutions_dict = {}
        self.screen_resolutions_by_string = {}
        self.config.screen_resolutions_by_string = {}
        for mode in self.screen_modes:
            try:
                width = int(mode.width)
                height = int(mode.height)
            except (TypeError, ValueError, OverflowError):
                continue
            if width < 640 or height < 480:
                continue
            resolution = ScreenResolution(width, height)
            self.screen_resolutions_dict[(width, height)] = resolution
            self.config.screen_resolutions_by_string[resolution.resolution_string] = resolution

        if not self.screen_resolutions_dict:
            resolution = ScreenResolution(800, 600)
            self.screen_resolutions_dict[(800, 600)] = resolution

        if self.config.fullscreen:
            active_pair = (int(self.config.width), int(self.config.height))
            if active_pair not in self.screen_resolutions_dict:
                fallback_pair = (
                    (800, 600)
                    if (800, 600) in self.screen_resolutions_dict
                    else sorted(self.screen_resolutions_dict.keys())[0]
                )
                self.config.width, self.config.height = fallback_pair
                active_pair = fallback_pair
        else:
            active_pair = (
                int(self.config.window_width),
                int(self.config.window_height),
            )

        self.update_resolutions()
        self.current_resolution = self.screen_resolutions_dict.get(
            active_pair,
            ScreenResolution(active_pair[0], active_pair[1]),
        )

    def update_resolutions(self):
        if self.config.fullscreen:
            height = int(self.config.height)
            width = int(self.config.width)
        else:
            height = int(self.config.window_height)
            width = int(self.config.window_width)

        items = sorted(
            self.screen_resolutions_dict.items(),
            key=operator.itemgetter(0),
        )
        active_pair = (width, height)
        if active_pair in self.screen_resolutions_dict:
            current_resolution_index = [
                item[0] for item in items
            ].index(active_pair)
        else:
            from aoslib import strings
            resolution = ScreenResolution(width, height, strings.CUSTOM)
            items.insert(0, (active_pair, resolution))
            current_resolution_index = 0

        resolutions_by_string = {}
        for pair, resolution in items:
            resolutions_by_string[resolution.resolution_string] = resolution
        self.screen_resolutions_by_string = resolutions_by_string
        self.config.screen_resolutions_by_string = resolutions_by_string
        self.config.sorted_screen_resolutions_for_gui = items
        self.config.resolution = current_resolution_index
        if self.graphics_tab_resolutions_populate_callback != None:
            self.graphics_tab_resolutions_populate_callback(True, current_resolution_index)
        return

    def is_custom_resolution(self, width, height):
        try:
            pair = (int(width), int(height))
        except (TypeError, ValueError, OverflowError):
            return True
        return pair not in self.screen_resolutions_dict


graphics_manager = GraphicsManager()

import aoslib.font, aoslib.graphicsManager as graphics_manager
the_graphics_manager = graphics_manager.graphics_manager

def calculate_scale_on_window_resize(window, image, invert_ratio=False, check_custom_resolution=False):
    original_width = float(image.width)
    original_height = float(image.height)
    window_width = float(window.width)
    window_height = float(window.height)
    if original_width <= 0 or original_height <= 0 or window_height <= 0 or window_width <= 0:
        print 'Invalid window size:', original_width, original_height, window_height, window_width
        return (
         0, 0, 0, 0, False)
    original_ratio = original_width / original_height
    ratio = window_width / window_height
    new_width = original_width / original_height * window_height
    new_height = original_height / original_width * window_width
    x = 0.0
    y = 0.0
    decrease_width = ratio < original_ratio
    if decrease_width and invert_ratio == False or not decrease_width and invert_ratio:
        scale_w = new_width / original_width
        scale_h = window_height / original_height
        x = (window_width - new_width) / 2.0
    else:
        scale_w = window_width / original_width
        scale_h = new_height / original_height
        y = (window_height - new_height) / 2.0
    aoslib.font.GLOBAL_WINDOW_HEIGHT = window_height
    aoslib.font.GLOBAL_WINDOW_WIDTH = window_width
    custom_resolution = False
    if check_custom_resolution:
        custom_resolution = is_custom_resolution(window_width, window_height)
    return (x, y, scale_w, scale_h, custom_resolution)


def is_custom_resolution(width, height):
    if the_graphics_manager is not None:
        return the_graphics_manager.is_custom_resolution(width, height)
    else:
        return


def update_resolutions():
    return the_graphics_manager.update_resolutions()

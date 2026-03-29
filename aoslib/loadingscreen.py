import pyglet.image
from pyglet import gl
from aoslib import calculate_scale_on_window_resize
progress = 0
PROGRESS_MAX_BULLETS = 36
PROGRESS_MAX = 975
X = 316
Y = 166.5

def init(window):
    global _window
    global loading_image
    global progress_image
    global progress_image_dark
    global splash_image
    _window = window
    gl.glViewport(0, 0, _window.width, _window.height)
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    gl.glOrtho(0, _window.width, 0, _window.height, -1, 1)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()
    _window.dispatch_events()
    loading_image = pyglet.image.load('./png/ui/title_and_copyright.png')
    splash_image = pyglet.image.load('./png/ui/ugc_splash.png')
    progress_image = pyglet.image.load('./png/ui/progress_bullet_large.png')
    progress_image_dark = pyglet.image.load('./png/ui/progress_bullet_dark_large.png')
    update_progress(0)


def show_window():
    _window.set_visible(True)


def update_progress(progress_increment=1):
    global progress
    if not splash_image:
        return
    else:
        if progress_increment == 1 and _window.context is None:
            raise SystemExit()
        old_noof_bullets = progress * PROGRESS_MAX_BULLETS / PROGRESS_MAX
        progress += progress_increment
        new_noof_bullets = min(progress * PROGRESS_MAX_BULLETS / PROGRESS_MAX, PROGRESS_MAX_BULLETS)
        gl.glViewport(0, 0, _window.width, _window.height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0, _window.width, 0, _window.height, -1, 1)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        x, y, scale_w, scale_h, custom_resolution = calculate_scale_on_window_resize(_window, splash_image)
        gl.glPushMatrix()
        gl.glTranslatef(x, y, 1.0)
        gl.glScalef(scale_w, scale_h, 0.0)
        splash_image.blit(0, 0)
        gl.glPopMatrix()
        x, y, scale_w, scale_h, custom_resolution = calculate_scale_on_window_resize(_window, splash_image, True)
        gl.glPushMatrix()
        gl.glTranslatef(x, y, 0.0)
        gl.glScalef(scale_w, scale_h, 1.0)
        loading_image.blit(0, 0)
        for bullet_index in range(0, PROGRESS_MAX_BULLETS):
            progress_image_dark.blit(X + bullet_index * progress_image.width, Y)

        for bullet_index in range(0, new_noof_bullets):
            progress_image.blit(X + bullet_index * progress_image.width, Y)

        gl.glPopMatrix()
        _window.flip()
        _window.dispatch_events()
        return


def finished():
    global progress_image
    global progress_image_dark
    global splash_image
    if progress != PROGRESS_MAX:
        print 'Progress bar finished on %d of %d. Values in loadingscreen.py need updating' % (progress, PROGRESS_MAX)
    splash_image = None
    progress_image = None
    progress_image_dark = None
    return

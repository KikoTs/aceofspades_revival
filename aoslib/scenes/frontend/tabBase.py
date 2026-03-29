from aoslib.scenes import Scene, ElementScene, MenuScene

class TabBase(MenuScene):
    enabled = False

    def set_in_game_tab(self, in_game_tab):
        self.in_game_tab = in_game_tab
        self.update_display()

    def on_menu_opened(self):
        pass

    def on_set(self):
        pass

    def update_display(self):
        pass

    def set_enabled_controls(self, enabled):
        pass

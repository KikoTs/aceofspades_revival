class DrawItem(object):
    draw_on_minimap_when_out_of_range = False
    deleted = False
    requires_update = True
    requires_draw = True
    needs_shadow = False

    def __init__(self, scene, *arg, **kw):
        self.scene = scene
        scene.objects.append(self)
        if self.__class__ not in scene.objects_by_type.keys():
            scene.objects_by_type[self.__class__] = []
        scene.objects_by_type[self.__class__].append(self)
        self.initialize(*arg, **kw)

    def initialize(self, *arg, **kw):
        pass

    def update(self, dt):
        pass

    def delete(self):
        if self.deleted:
            return
        self.deleted = True
        self.scene.objects.remove(self)
        self.scene.objects_by_type[self.__class__].remove(self)
        self.on_delete()

    def on_delete(self):
        pass

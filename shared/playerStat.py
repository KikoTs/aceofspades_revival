import math
LEVEL_EASE_FACTOR = [
 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 4, 5, 6, 7, 
 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 
 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 
 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 
 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 
 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87]

class PlayerStat(object):

    def __init__(self, code=0, category='NONE', show_bar=False, show_score=False, level1_requirement=10, multiplier=1.15, value_modifier=None):
        self.code = code
        self.category = category
        self.count = 0
        self.score = 0
        self.value_modifier = value_modifier
        self.multiplier = multiplier
        self.show_bar = show_bar
        self.show_score = show_score
        self.level1_requirement = level1_requirement
        self.level = 1
        self.percentage = 0.0
        self.next_level_min = 0.0
        self.next_level_max = 0.0

    def calculate_level(self):
        res = self.__calculate_level(self.count, self.level1_requirement, self.multiplier)
        self.level = res['level']
        self.percentage = res['percentage']
        self.next_level_min = res['next_level_min']
        self.next_level_max = res['next_level_max']

    @staticmethod
    def __calculate_level(score, level1_requirement, multiplier):
        level = 1
        percentage = 0
        next_level_min = 0
        next_level_max = level1_requirement * LEVEL_EASE_FACTOR[0]
        for i in range(score):
            if i >= next_level_max:
                level = level + 1
                next_level_min = next_level_max
                next_level_max = next_level_max + level1_requirement * ((level - 1) * multiplier)
                if level in range(0, len(LEVEL_EASE_FACTOR)):
                    next_level_max = next_level_max * LEVEL_EASE_FACTOR[level]
                next_level_max = round(next_level_max)

        percentage = 100.0 / max(0.001, next_level_max - next_level_min) * (score - next_level_min)
        return {'level': level, 'percentage': percentage, 'next_level_min': next_level_min, 'next_level_max': next_level_max}

    @staticmethod
    def value_modifier_mins_to_hours(value):
        if value == 0:
            return 0
        return '%.2f' % (value / 60.0)

    @staticmethod
    def value_modifier_percentage(value):
        return str(int(value * 100)) + '%'

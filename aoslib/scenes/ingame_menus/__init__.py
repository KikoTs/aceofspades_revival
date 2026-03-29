from pyglet import gl
from shared.common import blend_color
from aoslib.images import global_images
from aoslib.text import team_list_font, list_font, list_font_tuffy, draw_text_with_size_validation, draw_text_with_alignment_and_size_validation
from aoslib.draw import draw_quad
from pyglet.gl import glPushMatrix, glPopMatrix, glColor4ub, glScalef
from shared.constants import *
from aoslib import strings
from aoslib.common import collides
import aoslib.strings as strings
from shared.steam import SteamGetCurrentLobby, SteamGetLobbyOwner, SteamGetFriendPersonaName
LIST_COLOR2 = (35, 35, 35)
LIST_COLOR1 = (10, 10, 10)
LIST_X_OFFSET = 5
LIST_Y_OFFSET = -12
LIST_SPACING = 10
LIST_BLEND_COLOR = 0.2
LIST_CENTER_PAD = 10.0

def get_highlighted_team_member(team, x, y, width, height, mouse_xy, extra_players=[]):
    list_y_size = height / 16.0
    y -= 10 + list_y_size
    height += list_y_size
    if mouse_xy[0] < x or mouse_xy[0] > x + width:
        return
    if mouse_xy[1] > y or mouse_xy[1] < y - height:
        return
    index = int(round((y - mouse_xy[1]) / list_y_size))
    player_index = index - 1
    if player_index < 0 or player_index >= team.count():
        first_extra = 16 - len(extra_players)
        if player_index >= first_extra and player_index < 16:
            return (extra_players[player_index - first_extra], (x, y - list_y_size * index, width, list_y_size))
        return
    if player_index < 16:
        players = list(team.get_players(sort=True))
        return (
         players[player_index], (x, y - list_y_size * index, width, list_y_size))
    else:
        return
        return


def draw_player_list(team, x, y, width, height, score_x, extra_players=[]):
    list_y_size = height / 16.0
    base_color = UI_TEAM_COLOURS[team.id]
    if team.id == TEAM1:
        other_team_color = UI_TEAM_COLOURS[TEAM2]
    else:
        other_team_color = UI_TEAM_COLOURS[TEAM1]
    other_team_color += (255, )
    team_id = team.id
    color = base_color + (255, )
    team_y = y - 10
    team_x = x + 100
    text_area_width = 155
    text = None
    if team.show_score:
        text = '%s' % team.score
        if team.show_max_score:
            text += '/%s' % team.max_score
    else:
        text_area_width += 25
    if team_id == TEAM2:
        head_x = x + width - 65
        if team.show_score:
            team_x -= 45
        else:
            team_x -= 70
    else:
        head_x = x + 65
        score_x -= 50
    head_image, head_color_image = global_images.head_images[team_id]
    head_y = y + 20
    gl.glColor4f(1.0, 1.0, 1.0, 1.0)
    head_image.blit(head_x, head_y)
    gl.glColor4ub(*color)
    head_color_image.blit(head_x, head_y)
    draw_text_with_size_validation(team.name, team_x, team_y, text_area_width, 30, color, team_list_font)
    if team.show_score:
        draw_text_with_size_validation(text, score_x, team_y, 50, 30, color, team_list_font)
    players = list(team.get_players(sort=True))
    score_icon_offset_x = x + LIST_X_OFFSET + LIST_CENTER_PAD
    font_size = 11.0
    dom_offset = x + width * 0.1 + LIST_CENTER_PAD
    name_offset = x + width * 0.15 + LIST_CENTER_PAD
    score_offset = x + width * 0.6 + LIST_CENTER_PAD
    ping_offset = x + width * 0.85 + LIST_CENTER_PAD
    y -= 10
    for i in xrange(17):
        extra_player = False
        name_offset = x + width * 0.15 + LIST_CENTER_PAD
        if i == 0:
            player = None
            name, score, ping = strings.NAME, strings.SCORE, strings.PING
            text_color = (0, 0, 0, 255)
        else:
            try:
                player = players.pop(0)
            except IndexError:
                first_extra = 16 - len(extra_players)
                if i > first_extra:
                    extra_player = True
                    player = extra_players[i - 1 - first_extra]
                else:
                    player = None

            back_color_base = base_color
            if player is None:
                pass
            elif player.character and player.character.dead:
                text_color = DEAD_PLAYER_NAME_COLOR
            elif player.demo_player:
                text_color = DEMO_PLAYER_NAME_COLOR
            elif not extra_player:
                text_color = color
            elif player.team.id == TEAM_SPECTATOR:
                text_color = SPECTATOR_PLAYER_NAME_COLOR
                back_color_base = text_color[:3]
            else:
                text_color = other_team_color
                back_color_base = text_color[:3]
            if i % 2 == 0:
                back_color = blend_color(LIST_COLOR1, back_color_base, LIST_BLEND_COLOR)
            else:
                back_color = blend_color(LIST_COLOR2, back_color_base, LIST_BLEND_COLOR)
            back_color = back_color + (255, )
            draw_quad(x, y - list_y_size, width, list_y_size, back_color)
            if player is None:
                y -= list_y_size
                continue
            player_id = str(player.id)
            name = player.name
            score = str(player.score)
            ping = str(player.ping)
            try:
                glPushMatrix()
                if player.character and player.character.dead:
                    image = global_images.score_icon_dead
                    score_icon_offset_y = -2
                    score_icon_scale = 1.0
                    glColor4ub(*DEAD_PLAYER_ICON_COLOR)
                else:
                    if player.high_minimap_visibility:
                        image = global_images.score_icon_vip
                        score_icon_offset_y = -2
                        score_icon_scale = 1.0
                    else:
                        if player.get_class():
                            image = global_images.class_icons[player.get_class().id][player.team.id]
                        else:
                            image = None
                        score_icon_offset_y = -1
                        score_icon_scale = 0.11
                    color = blend_color(player.team.color, (255, 255, 255), 0.4)
                    color += (255, )
                    glColor4ub(*color)
                score_icon_x = (score_icon_offset_x + font_size / 2.0) / score_icon_scale
                score_icon_y = (y + LIST_Y_OFFSET + font_size / 2.0 + score_icon_offset_y) / score_icon_scale
                glScalef(score_icon_scale, score_icon_scale, score_icon_scale)
                if image:
                    image.blit(score_icon_x, score_icon_y)
                glPopMatrix()
                glPushMatrix()
                score_icon_scale = 1.0
                score_icon_y = (y + LIST_Y_OFFSET + font_size / 2.0 + score_icon_offset_y) / score_icon_scale
                glScalef(score_icon_scale, score_icon_scale, score_icon_scale)
                if player.dominatingLocalPlayer:
                    glColor4ub(255, 255, 255, 255)
                    image = global_images.score_dominating_image
                    image.blit(dom_offset, score_icon_y)
                elif player.dominatedByLocalPlayer:
                    glColor4ub(*other_team_color)
                    image = global_images.score_dominated_image
                    image.blit(dom_offset, score_icon_y)
                glPopMatrix()
            except IndexError:
                glPopMatrix()
                if player.get_class():
                    print 'score icon not found (IndexError) player class id:', player.get_class().id
            except KeyError:
                glPopMatrix()
                if player.get_class():
                    print 'score icon not found (KeyError) player class id:', player.get_class().id

            if SteamGetCurrentLobby() and name == SteamGetFriendPersonaName(SteamGetLobbyOwner()):
                glPushMatrix()
                host_icon_offset_y = score_icon_offset_y
                host_icon_scale = 1.0
                host_icon_y = (y + LIST_Y_OFFSET + font_size / 2.0 + host_icon_offset_y) / host_icon_scale
                glScalef(host_icon_scale, host_icon_scale, host_icon_scale)
                glColor4ub(255, 255, 255, 255)
                global_images.host_icon.blit(name_offset, host_icon_y)
                name_offset += global_images.host_icon.width + 1
                glPopMatrix()
        name_font = list_font
        if player is not None and strings.language_requires_tuffy(player.local_language):
            name_font = list_font_tuffy
        draw_text_with_size_validation(name, name_offset, y + LIST_Y_OFFSET, score_offset - name_offset - 5, 30, text_color, name_font, center_text=False)
        name_font.draw(score, score_offset, y + LIST_Y_OFFSET, text_color, center=False)
        name_font.draw(ping, ping_offset, y + LIST_Y_OFFSET, text_color, center=False)
        if i == 0:
            y -= 25
        else:
            y -= list_y_size

    return


def draw_game_stats(game_stats_list, team, x, y, width, height, score_x):
    list_y_size = height / 3.0
    base_color = UI_TEAM_COLOURS[team.id]
    team_id = team.id
    color = base_color + (255, )
    team_y = y - 6
    text_area_width = width
    text = None
    score_align = 'left'
    if team.show_score:
        text = '%s' % team.score
        if team.show_max_score:
            text += '/%s' % team.max_score
    else:
        text_area_width += 25
    if team_id == TEAM2:
        head_x = x + width - 23
    else:
        score_align = 'right'
        head_x = x + 23
    head_image, head_color_image = global_images.head_images[team_id]
    head_y = y + 12
    gl.glColor4f(1.0, 1.0, 1.0, 1.0)
    head_image.blit(head_x, head_y)
    gl.glColor4ub(*color)
    head_color_image.blit(head_x, head_y)
    draw_text_with_alignment_and_size_validation(team.name, x, team_y, text_area_width, 30, color, team_list_font, alignment_x='center', alignment_y='center')
    if team.show_score:
        draw_text_with_alignment_and_size_validation(text, score_x, team_y, 100, 30, color, team_list_font, alignment_x=score_align, alignment_y='center')
    local_game_stats = list(game_stats_list)
    score_icon_offset_x = x + LIST_X_OFFSET + LIST_CENTER_PAD
    font_size = 11.0
    name_offset = x + width * 0.01 + LIST_CENTER_PAD
    type_offset = x + width * 0.3 + LIST_CENTER_PAD
    score_offset = x + width * 1.0 + LIST_CENTER_PAD
    y -= 15
    for i in xrange(4):
        if i == 0:
            continue
        try:
            game_stat = local_game_stats.pop(0)
            player = game_stat.player
            if player:
                base_color = UI_TEAM_COLOURS[player.team.id]
                color1 = blend_color(LIST_COLOR1, base_color, LIST_BLEND_COLOR)
                color2 = blend_color(LIST_COLOR2, base_color, LIST_BLEND_COLOR)
                if i % 2 == 0:
                    back_color = color1
                else:
                    back_color = color2
                back_color = back_color + (255, )
                draw_quad(x, y - list_y_size, width, list_y_size, back_color)
        except (KeyError, IndexError):
            y -= list_y_size
            continue

        if player.character:
            text_color = base_color + (255, )
            player_id = str(player.id)
            name = player.name
            type = strings.get_by_id(GAME_STAT_TYPES[game_stat.stat_type])
            draw_text_with_size_validation(name, name_offset, y + LIST_Y_OFFSET, type_offset - name_offset - 5, 30, text_color, list_font, center_text=False)
            draw_text_with_size_validation(type, type_offset, y + LIST_Y_OFFSET, score_offset - type_offset - 15, 30, text_color, list_font, center_text=False)
        if i == 0:
            y -= 25
        else:
            y -= list_y_size

    return

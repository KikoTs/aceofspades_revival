from shared.steam import SteamGetCurrentGameLanguage
from shared.constants import *
from aoslib import text
import sys
import english, german, french, spanish, italian, portuguese_brazil, russian, polish, turkish, spanish_mexico, japanese
LANG_ENGLISH, LANG_GERMAN, LANG_FRENCH, LANG_SPANISH, LANG_ITALIAN, LANG_BRAZILIAN, LANG_RUSSIAN, LANG_POLISH, LANG_TURKISH, LANG_MEXICAN, LANG_JAPANESE = xrange(11)
language_ids = {'english': LANG_ENGLISH,
 'german': LANG_GERMAN,
 'french': LANG_FRENCH,
 'spanish': LANG_SPANISH,
 'italian': LANG_ITALIAN,
 'brazilian': LANG_BRAZILIAN,
 'portuguese_brazil': LANG_BRAZILIAN,
 'russian': LANG_RUSSIAN,
 'polish': LANG_POLISH,
 'turkish': LANG_TURKISH,
 'mexican': LANG_MEXICAN,
 'spanish_mexico': LANG_MEXICAN,
 'japanese': LANG_JAPANESE}
try:
    language_arg = sys.argv.index('+language')
    language = sys.argv[language_arg + 1]
except:
    language = SteamGetCurrentGameLanguage()

print 'Language detected: ', language
if language == '':
    language = 'english'
local_language_id = language_ids[language]
if language == 'brazilian':
    language = 'portuguese_brazil'
elif language == 'mexican':
    language = 'spanish_mexico'
if language == 'russian' or language == 'polish':
    text.EDO_FONT = 'Spades'
    text.STANDARD_FONT = 'Tuffy_Bold'
    text.ALDO_FONT = 'Spades'
if language == 'turkish':
    text.EDO_FONT = 'Edo'
    text.STANDARD_FONT = 'Tuffy_Bold'
    text.ALDO_FONT = 'Edo'
if language == 'japanese':
    text.EDO_FONT = 'Gen_Shin_Gothic_Monospace_Bold'
    text.STANDARD_FONT = 'NotoSansJP-SemiBold'
    text.ALDO_FONT = 'Gen_Shin_Gothic_Monospace_Bold'
text.set_fonts()
try:
    language_strings = __import__(language, globals())
except:
    language_strings = __import__('english', globals())

for key, value in language_strings.__dict__.iteritems():
    globals()[key] = value

def language_requires_tuffy(language):
    return language == LANG_POLISH or language == LANG_TURKISH or language == LANG_RUSSIAN or language == LANG_JAPANESE


def get_by_id(id):
    try:
        return globals()[id]
    except:
        if A2298:
            return 'Missing string ' + id
        else:
            return id


def get_by_id_or_except(id):
    return globals()[id]

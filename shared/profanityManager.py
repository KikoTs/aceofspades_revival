import os, re, random

class ProfanityManager:
    profanity_dictionary = []
    sanitise_regex = []

    def __init__(self, owner=None):
        self.owner = owner
        self.__load_dictionary()

    def __read_file(self, file):
        try:
            dict_file = open(file, 'rb')
            dict_data = dict_file.read()
            dict_file.close()
        except IOError:
            print "Couldn't find file profanity dictionary.", file

        return dict_data

    def __load_dictionary(self):
        if self.owner == None:
            dict_file_name = os.path.join(os.getcwd(), 'list.pnq')
            dict_data = self.__read_file(dict_file_name)
            xor_val = 85
            out_data = ''
            for value in dict_data:
                int_value = ord(value)
                outval = (int_value ^ xor_val) & 255
                xor_val = xor_val + outval & 255
                outchar = chr(outval)
                out_data += outchar

            profanity_words = out_data.splitlines()
        else:
            dict_file_name = os.path.join(os.getcwd(), 'profanitydict.txt')
            dict_data = self.__read_file(dict_file_name)
            profanity_words = dict_data.splitlines()
        self.profanity_dictionary = []
        for word in profanity_words:
            self.profanity_dictionary.append(self.anglicise_word(word))

        self.profanity_dictionary = set(self.profanity_dictionary)
        regexes = [
         '\\w+|[^\\w]',
         '[a-zA-Z0-9$@]+|[^a-zA-Z0-9$@]',
         '[a-zA-Z0-9!$@]+|[^a-zA-Z0-9!$@]']
        self.sanitise_regex = []
        for regex in regexes:
            self.sanitise_regex.append(re.compile(regex))

        return

    def sanitise_string(self, value, replacement_word=u'#*%!'):
        safe_string = value
        for regex in self.sanitise_regex:
            words = regex.findall(safe_string)
            safe_string = ''
            for word in words:
                if len(word) > 1 and self.anglicise_word(word) in self.profanity_dictionary:
                    temp = ''
                    for i in xrange(0, len(word)):
                        if len(replacement_word) > 1:
                            char_index = i % 4
                            temp += replacement_word[char_index]
                        else:
                            temp += replacement_word[0]

                    word = temp
                safe_string += word

        return safe_string

    def anglicise_word(self, word):
        result = word.lower()
        replacements = {'1': 'l', 'i': 'l', '!': 'l', '5': 's', 
           '$': 's', '0': 'o', 
           '@': 'a', 
           '4': 'a', '3': 'e', 
           '7': 't'}
        for value, replacement in replacements.iteritems():
            result = result.replace(value, replacement)

        return result

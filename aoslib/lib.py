import os, re, sys, ctypes, ctypes.util

class LibraryLoader(object):

    def load_library(self, *names, **kwargs):
        if 'framework' in kwargs and self.platform == 'darwin':
            return self.load_framework(kwargs['framework'])
        platform_names = kwargs.get(self.platform, [])
        if type(platform_names) in (str, unicode):
            platform_names = [
             platform_names]
        elif type(platform_names) is tuple:
            platform_names = list(platform_names)
        if self.platform == 'linux2':
            for name in names:
                libname = ctypes.util.find_library(name)
                platform_names.append(libname or 'lib%s.so' % name)

        platform_names.extend(names)
        for name in platform_names:
            try:
                lib = ctypes.cdll.LoadLibrary(name)
                return lib
            except OSError:
                path = self.find_library(name)
                if path:
                    try:
                        lib = ctypes.cdll.LoadLibrary(path)
                        return lib
                    except OSError:
                        pass

        raise ImportError('Library "%s" not found.' % names[0])

    find_library = lambda self, name: ctypes.util.find_library(name)
    platform = sys.platform
    if platform == 'cygwin':
        platform = 'win32'

    def load_framework(self, path):
        raise RuntimeError("Can't load framework on this platform.")


class MachOLibraryLoader(LibraryLoader):

    def __init__(self):
        if 'LD_LIBRARY_PATH' in os.environ:
            self.ld_library_path = os.environ['LD_LIBRARY_PATH'].split(':')
        else:
            self.ld_library_path = []
        if 'DYLD_LIBRARY_PATH' in os.environ:
            self.dyld_library_path = os.environ['DYLD_LIBRARY_PATH'].split(':')
        else:
            self.dyld_library_path = []
        if 'DYLD_FALLBACK_LIBRARY_PATH' in os.environ:
            self.dyld_fallback_library_path = os.environ['DYLD_FALLBACK_LIBRARY_PATH'].split(':')
        else:
            self.dyld_fallback_library_path = [
             os.path.expanduser('~/lib'),
             '/usr/local/lib',
             '/usr/lib']

    def find_library(self, path):
        libname = os.path.basename(path)
        search_path = []
        if hasattr(sys, 'frozen') and sys.frozen == 'macosx_app':
            search_path.append(os.path.join(os.environ['RESOURCEPATH'], '..', 'Frameworks', libname))
        if '/' in path:
            search_path.extend([os.path.join(p, libname) for p in self.dyld_library_path])
            search_path.append(path)
            search_path.extend([os.path.join(p, libname) for p in self.dyld_fallback_library_path])
        else:
            search_path.extend([os.path.join(p, libname) for p in self.ld_library_path])
            search_path.extend([os.path.join(p, libname) for p in self.dyld_library_path])
            search_path.append(path)
            search_path.extend([os.path.join(p, libname) for p in self.dyld_fallback_library_path])
        for path in search_path:
            if os.path.exists(path):
                return path

        return

    def find_framework(self, path):
        name = os.path.splitext(os.path.split(path)[1])[0]
        realpath = os.path.join(path, name)
        if os.path.exists(realpath):
            return realpath
        else:
            for dir in ('/Library/Frameworks', '/System/Library/Frameworks'):
                realpath = os.path.join(dir, '%s.framework' % name, name)
                if os.path.exists(realpath):
                    return realpath

            return

    def load_framework(self, path):
        realpath = self.find_framework(path)
        if realpath:
            lib = ctypes.cdll.LoadLibrary(realpath)
            return lib
        raise ImportError("Can't find framework %s." % path)


class LinuxLibraryLoader(LibraryLoader):
    _ld_so_cache = None

    def _create_ld_so_cache(self):
        directories = []
        try:
            directories.extend(os.environ['LD_LIBRARY_PATH'].split(':'))
        except KeyError:
            pass

        try:
            directories.extend([dir.strip() for dir in open('/etc/ld.so.conf')])
        except IOError:
            pass

        directories.extend(['/lib', '/usr/lib'])
        cache = {}
        lib_re = re.compile('lib(.*)\\.so')
        for dir in directories:
            try:
                for file in os.listdir(dir):
                    if '.so' not in file:
                        continue
                    path = os.path.join(dir, file)
                    if file not in cache:
                        cache[file] = path
                    match = lib_re.match(file)
                    if match:
                        library = match.group(1)
                        if library not in cache:
                            cache[library] = path

            except OSError:
                pass

        self._ld_so_cache = cache

    def find_library(self, path):
        result = ctypes.util.find_library(path)
        if result:
            return result
        else:
            if self._ld_so_cache is None:
                self._create_ld_so_cache()
            return self._ld_so_cache.get(path)


if sys.platform == 'darwin':
    loader = MachOLibraryLoader()
elif sys.platform == 'linux2':
    loader = LinuxLibraryLoader()
else:
    loader = LibraryLoader()
load_library = loader.load_library

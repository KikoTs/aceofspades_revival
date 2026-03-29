import imp, sys, os

def __import_pywin32_system_module__(modname, globs):
    if not sys.platform.startswith('win32'):
        for ext, mode, ext_type in imp.get_suffixes():
            if ext_type == imp.C_EXTENSION:
                for path in sys.path:
                    look = os.path.join(path, 'lib' + modname + ext)
                    if os.path.isfile(look):
                        mod = imp.load_module(modname, None, look, (
                         ext, mode, ext_type))
                        globs.update(mod.__dict__)
                        return

        raise ImportError('No dynamic module ' + modname)
    for suffix_item in imp.get_suffixes():
        if suffix_item[0] == '_d.pyd':
            suffix = '_d'
            break
    else:
        suffix = ''

    filename = '%s%d%d%s.dll' % (
     modname, sys.version_info[0], sys.version_info[1], suffix)
    if hasattr(sys, 'frozen'):
        for look in sys.path:
            if os.path.isfile(look):
                look = os.path.dirname(look)
            found = os.path.join(look, filename)
            if os.path.isfile(found):
                break
        else:
            raise ImportError("Module '%s' isn't in frozen sys.path %s" % (modname, sys.path))

    else:
        import _win32sysloader
        found = _win32sysloader.GetModuleFilename(filename)
        if found is None:
            found = _win32sysloader.LoadModule(filename)
        if found is None:
            if os.path.isfile(os.path.join(sys.prefix, filename)):
                found = os.path.join(sys.prefix, filename)
        if found is None:
            if os.path.isfile(os.path.join(os.path.dirname(__file__), filename)):
                found = os.path.join(os.path.dirname(__file__), filename)
        if found is None:
            raise ImportError("No system module '%s' (%s)" % (modname, filename))
    old_mod = sys.modules[modname]
    mod = imp.load_dynamic(modname, found)
    if sys.version_info < (3, 0):
        pass
    else:
        sys.modules[modname] = old_mod
        globs.update(mod.__dict__)
    return


__import_pywin32_system_module__('pywintypes', globals())

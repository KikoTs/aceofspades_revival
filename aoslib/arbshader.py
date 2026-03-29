from pyglet.gl import *
from ctypes import *

def get_arb_log():
    return string_at(glGetString(GL_PROGRAM_ERROR_STRING_ARB))


class CompileError(Exception):

    def __init__(self, shader, gl_error):
        text = get_arb_log()
        filename = shader.filename
        if filename:
            text = '%s: OpenGL error %s: %s' % (filename, gl_error, text)
        Exception.__init__(self, text)


class Shader(object):

    def __init__(self, vert=[], frag=[], filename=None):
        self.vert = vert
        self.frag = frag
        self.uniforms = {}
        self.filename = filename

    def initialize(self):
        vert = self.vert
        frag = self.frag
        self.fragment_shader = self.create_shader(frag, GL_FRAGMENT_PROGRAM_ARB)
        self.vertex_shader = self.create_shader(vert, GL_VERTEX_PROGRAM_ARB)

    def create_shader(self, item, type):
        uniforms = self.uniforms
        lines = item.splitlines()
        for line in lines:
            if line.startswith('!!') or line.startswith("''"):
                continue
            elif not line.startswith('#'):
                continue
            line = line[1:]
            command, arguments = line.split(' ', 1)
            if command == 'semantic':
                if arguments.startswith('gl_'):
                    continue
                uniforms[arguments] = None
            elif command == 'var':
                var_type, arguments = arguments.split(' ', 1)
                arguments = arguments.split(' : ')
                var_name = arguments[0]
                if var_name not in uniforms:
                    continue
                new_name = arguments[2]
                if not new_name:
                    del uniforms[var_name]
                    continue
                if new_name.startswith('c['):
                    new_name = new_name[2:-1]
                elif new_name.startswith('texunit '):
                    new_name = new_name[8:]
                uniforms[var_name] = (
                 type, int(new_name))
            else:
                continue

        glEnable(type)
        shader = GLuint()
        glGenProgramsARB(1, byref(shader))
        glBindProgramARB(type, shader)
        src = c_char_p(item)
        glProgramStringARB(type, GL_PROGRAM_FORMAT_ASCII_ARB, len(item), src)
        error = glGetError()
        if error:
            raise CompileError(self, error)
        glDisable(type)
        return shader

    def bind(self, size=None):
        glEnable(GL_VERTEX_PROGRAM_ARB)
        glEnable(GL_FRAGMENT_PROGRAM_ARB)
        glBindProgramARB(GL_FRAGMENT_PROGRAM_ARB, self.fragment_shader)
        glBindProgramARB(GL_VERTEX_PROGRAM_ARB, self.vertex_shader)

    def bind_attrib(self, index, name):
        pass

    def link(self):
        pass

    @staticmethod
    def unbind():
        glDisable(GL_VERTEX_PROGRAM_ARB)
        glDisable(GL_FRAGMENT_PROGRAM_ARB)

    def get_uniform_location(self, name):
        try:
            type, local_id = self.uniforms[name]
            return (
             type, local_id)
        except KeyError:
            return

        return

    def uniformf_loc(self, loc, *vals):
        if loc is None:
            return
        else:
            vals += (0.0, ) * (4 - len(vals))
            type, local_id = loc
            glProgramLocalParameter4dARB(type, local_id, *vals)
            return

    def uniformi_loc(self, loc, *vals):
        if loc is None:
            return
        else:
            vals += (0.0, ) * (4 - len(vals))
            type, local_id = loc
            glProgramLocalParameter4dARB(type, local_id, *vals)
            return

    def uniformf(self, name, *vals):
        vals += (0.0, ) * (4 - len(vals))
        try:
            type, local_id = self.uniforms[name]
        except KeyError:
            return

        glProgramLocalParameter4dARB(type, local_id, *vals)

    def uniformi(self, name, *vals):
        self.uniformf(name, *[float(val) for val in vals])

    def uniform_vec2(self, name, mat):
        raise NotImplementedError
        loc = glGetUniformLocationARB(self.handle, name)
        glUniformMatrix2fvARB(loc, 1, False, (c_float * 4)(*mat))

    def uniform_vec3(self, name, mat):
        raise NotImplementedError
        loc = glGetUniformLocationARB(self.handle, name)
        glUniformMatrix3fvARB(loc, 1, False, (c_float * 9)(*mat))

    def uniform_vec4(self, name, mat):
        raise NotImplementedError
        loc = glGetUniformLocationARB(self.handle, name)
        glUniformMatrix4fvARB(loc, 1, False, (c_float * 16)(*mat))

    def delete_shader(self):
        glDeleteProgramsARB(1, self.vertex_shader)
        glDeleteProgramsARB(1, self.fragment_shader)

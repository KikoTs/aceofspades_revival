from pyglet.gl import *
from ctypes import *

class CompileError(Exception):

    def __init__(self, shader, text):
        filename = shader.filename
        if filename:
            text = '%s: %s' % (filename, text)
        Exception.__init__(self, text)


def get_glsl_log(handle):
    temp = c_int(0)
    glGetObjectParameterivARB(handle, GL_OBJECT_INFO_LOG_LENGTH_ARB, byref(temp))
    buffer = create_string_buffer(temp.value)
    glGetInfoLogARB(handle, temp, None, buffer)
    return buffer.value


class Shader(object):
    initialized = False
    shader = None

    def __init__(self, vert=[], frag=[], filename=None):
        self.vert = vert
        self.frag = frag
        self.filename = filename

    def initialize(self):
        self.handle = glCreateProgramObjectARB()
        for item in self.vert:
            self.create_shader(item, GL_VERTEX_SHADER_ARB)

        for item in self.frag:
            self.create_shader(item, GL_FRAGMENT_SHADER_ARB)

    def create_shader(self, item, type):
        self.shader = glCreateShaderObjectARB(type)
        src = (c_char_p * 1)(item)
        glShaderSourceARB(self.shader, 1, cast(pointer(src), POINTER(POINTER(c_char))), None)
        glCompileShaderARB(self.shader)
        temp = c_int(0)
        glGetObjectParameterivARB(self.shader, GL_OBJECT_COMPILE_STATUS_ARB, byref(temp))
        if not temp:
            raise CompileError(self, get_glsl_log(self.shader))
        else:
            glAttachObjectARB(self.handle, self.shader)
        return

    def delete_shader(self):
        glDetachObjectARB(self.handle, self.shader)
        glDeleteObjectARB(self.handle)

    def link(self):
        glLinkProgramARB(self.handle)
        temp = c_int(0)
        glGetObjectParameterivARB(self.handle, GL_OBJECT_LINK_STATUS_ARB, byref(temp))
        if not temp:
            raise CompileError(self, get_glsl_log(self.handle))

    def bind(self, size=None):
        glUseProgramObjectARB(self.handle)

    def bind_attrib(self, index, name):
        glBindAttribLocationARB(self.handle, index, name)

    @staticmethod
    def unbind():
        glUseProgramObjectARB(0)

    def get_uniform_location(self, name):
        loc = glGetUniformLocationARB(self.handle, name)
        return loc

    def uniformf_loc(self, loc, *vals):
        if len(vals) in range(1, 5):
            {1: glUniform1fARB, 2: glUniform2fARB, 3: glUniform3fARB, 
               4: glUniform4fARB}[len(vals)](loc, *vals)

    def uniformi_loc(self, loc, *vals):
        if len(vals) in range(1, 5):
            {1: glUniform1iARB, 2: glUniform2iARB, 
               3: glUniform3iARB, 
               4: glUniform4iARB}[len(vals)](loc, *vals)

    def uniformf(self, name, *vals):
        if len(vals) in range(1, 5):
            loc = glGetUniformLocationARB(self.handle, name)
            {1: glUniform1fARB, 2: glUniform2fARB, 
               3: glUniform3fARB, 
               4: glUniform4fARB}[len(vals)](loc, *vals)

    def uniformi(self, name, *vals):
        if len(vals) in range(1, 5):
            loc = glGetUniformLocationARB(self.handle, name)
            {1: glUniform1iARB, 
               2: glUniform2iARB, 
               3: glUniform3iARB, 
               4: glUniform4iARB}[len(vals)](loc, *vals)

    def uniform_vec2(self, name, mat):
        loc = glGetUniformLocationARB(self.handle, name)
        glUniformMatrix2fvARB(loc, 1, False, (c_float * 4)(*mat))

    def uniform_vec3(self, name, mat):
        loc = glGetUniformLocationARB(self.handle, name)
        glUniformMatrix3fvARB(loc, 1, False, (c_float * 9)(*mat))

    def uniform_vec4(self, name, mat):
        loc = glGetUniformLocationARB(self.handle, name)
        glUniformMatrix4fvARB(loc, 1, False, (c_float * 16)(*mat))

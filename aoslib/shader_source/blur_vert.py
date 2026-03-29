blur_vert = '\n#version 110\n\nvoid main() {\n    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;\n    gl_TexCoord[0] = gl_MultiTexCoord0;\n    gl_FrontColor = gl_Color;\n}\n'

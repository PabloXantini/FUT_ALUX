#pragma once

#include <windows.h>
#include <GL/gl.h>

// --- OpenGL Extension Definitions ---
typedef char GLchar;
typedef ptrdiff_t GLintptr;
typedef ptrdiff_t GLsizeiptr;

#ifndef APIENTRY
#define APIENTRY __stdcall
#endif
#ifndef APIENTRYP
#define APIENTRYP APIENTRY *
#endif
#ifndef GLAPI
#define GLAPI extern
#endif

#define GL_ARRAY_BUFFER                   0x8892
#define GL_STATIC_DRAW                    0x88E4
#define GL_DYNAMIC_DRAW                   0x88E8
#define GL_FRAGMENT_SHADER                0x8B30
#define GL_VERTEX_SHADER                  0x8B31
#define GL_COMPILE_STATUS                 0x8B81
#define GL_LINK_STATUS                    0x8B82
#define GL_INFO_LOG_LENGTH                0x8B84
#define GL_FRAMEBUFFER                    0x8D40
#define GL_COLOR_ATTACHMENT0              0x8CE0
#define GL_DEPTH_ATTACHMENT               0x8D00
#define GL_FRAMEBUFFER_COMPLETE           0x8CD5
#define GL_READ_FRAMEBUFFER               0x8CA8
#define GL_DRAW_FRAMEBUFFER               0x8CA9
#define GL_DEPTH_COMPONENT24              0x81A6
#define GL_PIXEL_PACK_BUFFER              0x88EB
#define GL_STREAM_READ                    0x88E1
#define GL_READ_ONLY                      0x88B8
#define GL_TEXTURE0                       0x84C0
#define GL_TEXTURE1                       0x84C1
#define GL_CLAMP_TO_EDGE                  0x812F

typedef void (APIENTRYP PFNGLGENVERTEXARRAYSPROC) (GLsizei n, GLuint *arrays);
typedef void (APIENTRYP PFNGLBINDVERTEXARRAYPROC) (GLuint array);
typedef void (APIENTRYP PFNGLGENBUFFERSPROC) (GLsizei n, GLuint *buffers);
typedef void (APIENTRYP PFNGLBINDBUFFERPROC) (GLenum target, GLuint buffer);
typedef void (APIENTRYP PFNGLBUFFERDATAPROC) (GLenum target, GLsizeiptr size, const void *data, GLenum usage);
typedef void (APIENTRYP PFNGLBUFFERSUBDATAPROC) (GLenum target, GLintptr offset, GLsizeiptr size, const void *data);
typedef void (APIENTRYP PFNGLVERTEXATTRIBPOINTERPROC) (GLuint index, GLint size, GLenum type, GLboolean normalized, GLsizei stride, const void *pointer);
typedef void (APIENTRYP PFNGLENABLEVERTEXATTRIBARRAYPROC) (GLuint index);
typedef GLuint (APIENTRYP PFNGLCREATESHADERPROC) (GLenum type);
typedef void (APIENTRYP PFNGLSHADERSOURCEPROC) (GLuint shader, GLsizei count, const GLchar *const*string, const GLint *length);
typedef void (APIENTRYP PFNGLCOMPILESHADERPROC) (GLuint shader);
typedef void (APIENTRYP PFNGLGETSHADERIVPROC) (GLuint shader, GLenum pname, GLint *params);
typedef void (APIENTRYP PFNGLGETSHADERINFOLOGPROC) (GLuint shader, GLsizei bufSize, GLsizei *length, GLchar *infoLog);
typedef GLuint (APIENTRYP PFNGLCREATEPROGRAMPROC) (void);
typedef void (APIENTRYP PFNGLATTACHSHADERPROC) (GLuint program, GLuint shader);
typedef void (APIENTRYP PFNGLLINKPROGRAMPROC) (GLuint program);
typedef void (APIENTRYP PFNGLGETPROGRAMIVPROC) (GLuint program, GLenum pname, GLint *params);
typedef void (APIENTRYP PFNGLGETPROGRAMINFOLOGPROC) (GLuint program, GLsizei bufSize, GLsizei *length, GLchar *infoLog);
typedef void (APIENTRYP PFNGLUSEPROGRAMPROC) (GLuint program);
typedef void (APIENTRYP PFNGLGENFRAMEBUFFERSPROC) (GLsizei n, GLuint *framebuffers);
typedef void (APIENTRYP PFNGLBINDFRAMEBUFFERPROC) (GLenum target, GLuint framebuffer);
typedef void (APIENTRYP PFNGLFRAMEBUFFERTEXTURE2DPROC) (GLenum target, GLenum attachment, GLenum textarget, GLuint texture, GLint level);
typedef GLenum (APIENTRYP PFNGLCHECKFRAMEBUFFERSTATUSPROC) (GLenum target);
typedef void (APIENTRYP PFNGLBLITFRAMEBUFFERPROC) (GLint srcX0, GLint srcY0, GLint srcX1, GLint srcY1, GLint dstX0, GLint dstY0, GLint dstX1, GLint dstY1, GLbitfield mask, GLenum filter);
typedef GLint (APIENTRYP PFNGLGETUNIFORMLOCATIONPROC) (GLuint program, const GLchar *name);
typedef void (APIENTRYP PFNGLUNIFORM1FPROC) (GLint location, GLfloat v0);
typedef void (APIENTRYP PFNGLUNIFORM1IPROC) (GLint location, GLint v0);
typedef void (APIENTRYP PFNGLUNIFORM2FPROC) (GLint location, GLfloat v0, GLfloat v1);
typedef void (APIENTRYP PFNGLUNIFORM3FPROC) (GLint location, GLfloat v0, GLfloat v1, GLfloat v2);
typedef void (APIENTRYP PFNGLUNIFORM4FPROC) (GLint location, GLfloat v0, GLfloat v1, GLfloat v2, GLfloat v3);
typedef void (APIENTRYP PFNGLUNIFORMMATRIX4FVPROC) (GLint location, GLsizei count, GLboolean transpose, const GLfloat *value);
typedef void (APIENTRYP PFNGLDELETEPROGRAMPROC) (GLuint program);
typedef void* (APIENTRYP PFNGLMAPBUFFERPROC) (GLenum target, GLenum access);
typedef GLboolean (APIENTRYP PFNGLUNMAPBUFFERPROC) (GLenum target);
typedef void (APIENTRYP PFNGLDELETEVERTEXARRAYSPROC) (GLsizei n, const GLuint *arrays);
typedef void (APIENTRYP PFNGLDELETEBUFFERSPROC) (GLsizei n, const GLuint *buffers);
typedef void (APIENTRYP PFNGLACTIVETEXTUREPROC) (GLenum texture);

#define GL_FUNC_DECL(name) extern PFNGL##name##PROC gl##name;
GL_FUNC_DECL(GENVERTEXARRAYS)
GL_FUNC_DECL(BINDVERTEXARRAY)
GL_FUNC_DECL(DELETEVERTEXARRAYS)
GL_FUNC_DECL(GENBUFFERS)
GL_FUNC_DECL(BINDBUFFER)
GL_FUNC_DECL(DELETEBUFFERS)
GL_FUNC_DECL(BUFFERDATA)
GL_FUNC_DECL(BUFFERSUBDATA)
GL_FUNC_DECL(VERTEXATTRIBPOINTER)
GL_FUNC_DECL(ENABLEVERTEXATTRIBARRAY)
GL_FUNC_DECL(CREATESHADER)
GL_FUNC_DECL(SHADERSOURCE)
GL_FUNC_DECL(COMPILESHADER)
GL_FUNC_DECL(GETSHADERIV)
GL_FUNC_DECL(GETSHADERINFOLOG)
GL_FUNC_DECL(CREATEPROGRAM)
GL_FUNC_DECL(ATTACHSHADER)
GL_FUNC_DECL(LINKPROGRAM)
GL_FUNC_DECL(GETPROGRAMIV)
GL_FUNC_DECL(GETPROGRAMINFOLOG)
GL_FUNC_DECL(USEPROGRAM)
GL_FUNC_DECL(GENFRAMEBUFFERS)
GL_FUNC_DECL(BINDFRAMEBUFFER)
GL_FUNC_DECL(FRAMEBUFFERTEXTURE2D)
GL_FUNC_DECL(CHECKFRAMEBUFFERSTATUS)
GL_FUNC_DECL(BLITFRAMEBUFFER)
GL_FUNC_DECL(GETUNIFORMLOCATION)
GL_FUNC_DECL(UNIFORM1F)
GL_FUNC_DECL(UNIFORM1I)
GL_FUNC_DECL(UNIFORM2F)
GL_FUNC_DECL(UNIFORM3F)
GL_FUNC_DECL(UNIFORM4F)
GL_FUNC_DECL(UNIFORMMATRIX4FV)
GL_FUNC_DECL(DELETEPROGRAM)
GL_FUNC_DECL(MAPBUFFER)
GL_FUNC_DECL(UNMAPBUFFER)
GL_FUNC_DECL(ACTIVETEXTURE)

#define glGenVertexArrays glGENVERTEXARRAYS
#define glBindVertexArray glBINDVERTEXARRAY
#define glDeleteVertexArrays glDELETEVERTEXARRAYS
#define glGenBuffers glGENBUFFERS
#define glBindBuffer glBINDBUFFER
#define glDeleteBuffers glDELETEBUFFERS
#define glBufferData glBUFFERDATA
#define glBufferSubData glBUFFERSUBDATA
#define glVertexAttribPointer glVERTEXATTRIBPOINTER
#define glEnableVertexAttribArray glENABLEVERTEXATTRIBARRAY
#define glCreateShader glCREATESHADER
#define glShaderSource glSHADERSOURCE
#define glCompileShader glCOMPILESHADER
#define glGetShaderiv glGETSHADERIV
#define glGetShaderInfoLog glGETSHADERINFOLOG
#define glCreateProgram glCREATEPROGRAM
#define glAttachShader glATTACHSHADER
#define glLinkProgram glLINKPROGRAM
#define glGetProgramiv glGETPROGRAMIV
#define glGetProgramInfoLog glGETPROGRAMINFOLOG
#define glUseProgram glUSEPROGRAM
#define glGenFramebuffers glGENFRAMEBUFFERS
#define glBindFramebuffer glBINDFRAMEBUFFER
#define glFramebufferTexture2D glFRAMEBUFFERTEXTURE2D
#define glCheckFramebufferStatus glCHECKFRAMEBUFFERSTATUS
#define glBlitFramebuffer glBLITFRAMEBUFFER
#define glGetUniformLocation glGETUNIFORMLOCATION
#define glUniform1f glUNIFORM1F
#define glUniform1i glUNIFORM1I
#define glUniform2f glUNIFORM2F
#define glUniform3f glUNIFORM3F
#define glUniform4f glUNIFORM4F
#define glUniformMatrix4fv glUNIFORMMATRIX4FV
#define glDeleteProgram glDELETEPROGRAM
#define glMapBuffer glMAPBUFFER
#define glUnmapBuffer glUNMAPBUFFER
#define glActiveTexture glACTIVETEXTURE

void loadGLFunctions();

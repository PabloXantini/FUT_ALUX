#include "renderer.hpp"
#include "gl_loader.hpp"
#include "math_utils.hpp"
#include "primitives.hpp"

namespace vision {

// --- Mesh Implementation ---

Mesh::Mesh() : vao(0), vbo(0), count(0) {}

Mesh::~Mesh() {
    if (vao) glDeleteVertexArrays(1, &vao);
    if (vbo) glDeleteBuffers(1, &vbo);
}

void Mesh::setup(const std::vector<float>& data, bool dynamic) {
    if (!vao) glGenVertexArrays(1, &vao);
    if (!vbo) glGenBuffers(1, &vbo);
    glBindVertexArray(vao);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, data.size() * sizeof(float), data.data(), dynamic ? GL_DYNAMIC_DRAW : GL_STATIC_DRAW);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * sizeof(float), (void*)(3 * sizeof(float)));
    glEnableVertexAttribArray(1);
    count = (int)data.size() / 6;
}

void Mesh::setupCustom(const std::vector<float>& data, int stride, int posSize, int texSize) {
    if (!vao) glGenVertexArrays(1, &vao);
    if (!vbo) glGenBuffers(1, &vbo);
    glBindVertexArray(vao);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, data.size() * sizeof(float), data.data(), GL_STATIC_DRAW);
    
    // Position
    glVertexAttribPointer(0, posSize, GL_FLOAT, GL_FALSE, stride * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);
    
    // TexCoords
    if (texSize > 0) {
        glVertexAttribPointer(1, texSize, GL_FLOAT, GL_FALSE, stride * sizeof(float), (void*)(posSize * sizeof(float)));
        glEnableVertexAttribArray(1);
    }
    count = (int)data.size() / stride;
}

void Mesh::setup(const std::vector<Vertex>& vertices, bool dynamic) {
    if (!vao) glGenVertexArrays(1, &vao);
    if (!vbo) glGenBuffers(1, &vbo);
    glBindVertexArray(vao);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, vertices.size() * sizeof(Vertex), vertices.data(), dynamic ? GL_DYNAMIC_DRAW : GL_STATIC_DRAW);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex), (void*)0);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex), (void*)(3 * sizeof(float)));
    glEnableVertexAttribArray(1);
    count = (int)vertices.size();
}

void Mesh::update(const std::vector<Vertex>& vertices) {
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferSubData(GL_ARRAY_BUFFER, 0, vertices.size() * sizeof(Vertex), vertices.data());
    count = (int)vertices.size();
}

void Mesh::draw(GLenum mode) const {
    glBindVertexArray(vao);
    glDrawArrays(mode, 0, count);
}

// --- Win32Context Implementation ---
class Win32Context : public IGraphicsContext {
public:
    bool initialize(int width, int height) override {
        HINSTANCE hInstance = GetModuleHandle(NULL);
        WNDCLASS wc = {0};
        wc.lpfnWndProc = DefWindowProc;
        wc.hInstance = hInstance;
        wc.lpszClassName = "HeadlessGL";
        RegisterClass(&wc);
        m_hwnd = CreateWindow(wc.lpszClassName, "HeadlessGL", 0, 0, 0, width, height, NULL, NULL, hInstance, NULL);
        m_hdc = GetDC(m_hwnd);
        PIXELFORMATDESCRIPTOR pfd = {0};
        pfd.nSize = sizeof(pfd);
        pfd.nVersion = 1;
        pfd.dwFlags = PFD_SUPPORT_OPENGL | PFD_DRAW_TO_WINDOW;
        pfd.iPixelType = PFD_TYPE_RGBA;
        pfd.cColorBits = 32;
        pfd.cDepthBits = 24;
        pfd.cStencilBits = 8;
        int pixelFormat = ChoosePixelFormat(m_hdc, &pfd);
        SetPixelFormat(m_hdc, pixelFormat, &pfd);
        m_hrc = wglCreateContext(m_hdc);
        wglMakeCurrent(m_hdc, m_hrc);
        loadGLFunctions();
        return true;
    }
    void makeCurrent() override { wglMakeCurrent(m_hdc, m_hrc); }
    void swapBuffers() override { SwapBuffers(m_hdc); }
    ~Win32Context() {
        wglMakeCurrent(NULL, NULL);
        wglDeleteContext(m_hrc);
        ReleaseDC(m_hwnd, m_hdc);
        DestroyWindow(m_hwnd);
    }
private:
    HWND m_hwnd; HDC m_hdc; HGLRC m_hrc;
};

// Renderer Implementation
Renderer::Renderer(int width, int height) : m_width(width), m_height(height) {
    m_context = std::make_unique<Win32Context>();
    m_frameBuffer.resize(width * height * 4);
}

Renderer::~Renderer() {}

bool Renderer::initialize() {
    if (!m_context->initialize(m_width, m_height)) return false;
    setupBuffers();
    setupShaders();
    setupPrimitives();
    return true;
}

// BUFFERS
static GLuint createColorTexture(int w, int h) {
    GLuint tex;
    glGenTextures(1, &tex);
    glBindTexture(GL_TEXTURE_2D, tex);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, NULL);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    return tex;
}

void Renderer::setupBuffers() {
    // --- Scene FBO ---
    glGenFramebuffers(1, &m_fbo);
    glBindFramebuffer(GL_FRAMEBUFFER, m_fbo);

    m_colorTex = createColorTexture(m_width, m_height);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, m_colorTex, 0);

    glGenTextures(1, &m_depthTex);
    glBindTexture(GL_TEXTURE_2D, m_depthTex);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, m_width, m_height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, NULL);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, m_depthTex, 0);

    glGenBuffers(1, &m_pbo);
    glBindBuffer(GL_PIXEL_PACK_BUFFER, m_pbo);
    glBufferData(GL_PIXEL_PACK_BUFFER, m_width * m_height * 4, NULL, GL_STREAM_READ);
    glBindBuffer(GL_PIXEL_PACK_BUFFER, 0);

    // POST-PROCESSING FBO (salida final: fisheye + motion blur)
    glGenFramebuffers(1, &m_postFbo);
    glBindFramebuffer(GL_FRAMEBUFFER, m_postFbo);
    m_postTex = createColorTexture(m_width, m_height);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, m_postTex, 0);

    // Motion blur: ring-buffer de texturas de historial
    glGenFramebuffers(MAX_BLUR_HISTORY, m_historyFbo);
    for (int i = 0; i < MAX_BLUR_HISTORY; i++) {
        m_historyTex[i] = createColorTexture(m_width, m_height);
        // Inicializar con negro
        std::vector<unsigned char> black(m_width * m_height * 4, 0);
        glBindTexture(GL_TEXTURE_2D, m_historyTex[i]);
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, m_width, m_height, GL_RGBA, GL_UNSIGNED_BYTE, black.data());
        // Asociar FBO para poder copiar frames previos ahí
        glBindFramebuffer(GL_FRAMEBUFFER, m_historyFbo[i]);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, m_historyTex[i], 0);
    }

    glBindFramebuffer(GL_FRAMEBUFFER, 0);
}

// SHADERS
void Renderer::setupShaders() {
    m_baseShader = std::make_unique<Shader>();
    m_baseShader->load("sandbox/vision_cpp/shaders/base.vert",
                       "sandbox/vision_cpp/shaders/base.frag");

    // Shader de post-procesamiento (fisheye + motion blur)
    m_postShader = std::make_unique<Shader>();
    m_postShader->load("sandbox/vision_cpp/shaders/post_processing.vert",
                       "sandbox/vision_cpp/shaders/post_processing.frag");
}

// PRIMITIVES
void Renderer::setupPrimitives() {
    // Cube
    m_cubeMesh = std::make_unique<Mesh>();
    m_cubeMesh->setup(Primitives::createCube());

    // Cylinder
    m_cylinderMesh = std::make_unique<Mesh>();
    m_cylinderMesh->setup(Primitives::createCylinder());

    // Vertical Quad for circles (in XY plane for billboarding)
    std::vector<float> quadData = {
        -0.5f, -0.5f, 0.0f, 0, 0, 1,  0.5f, -0.5f, 0.0f, 0, 0, 1,  0.5f,  0.5f, 0.0f, 0, 0, 1,
        -0.5f, -0.5f, 0.0f, 0, 0, 1,  0.5f,  0.5f, 0.0f, 0, 0, 1, -0.5f,  0.5f, 0.0f, 0, 0, 1
    };
    m_quadMesh = std::make_unique<Mesh>();
    m_quadMesh->setup(quadData);

    // Screen Quad specifically for fisheye.vert (2D Pos, 2D Tex)
    std::vector<float> screenQuadData = {
        -1.0f, -1.0f,  0.0f, 0.0f,
         1.0f, -1.0f,  1.0f, 0.0f,
         1.0f,  1.0f,  1.0f, 1.0f,
        -1.0f, -1.0f,  0.0f, 0.0f,
         1.0f,  1.0f,  1.0f, 1.0f,
        -1.0f,  1.0f,  0.0f, 1.0f
    };
    m_screenQuadMesh = std::make_unique<Mesh>();
    m_screenQuadMesh->setupCustom(screenQuadData, 4, 2, 2);

    m_dynamicMesh = std::make_unique<Mesh>();
    // Pre-allocate a large buffer (10000 vertices)
    std::vector<Vertex> largeBuffer(10000);
    m_dynamicMesh->setup(largeBuffer, true);
    m_dynamicMesh->count = 0;
}

// SET MOTION BLUR
void Renderer::setMotionBlur(float strength, int samples) {
    m_motionBlurStrength = strength;
    m_motionBlurSamples  = (samples < 0) ? 0 : (samples > MAX_BLUR_HISTORY ? MAX_BLUR_HISTORY : samples);
}

// ROTATE HISTORY: copies current frame (m_colorTex) to the oldest slot in the ring-buffer
void Renderer::rotateHistory() {
    // Blit m_colorTex → m_historyTex[m_historyHead]
    glBindFramebuffer(GL_READ_FRAMEBUFFER, m_fbo);
    glBindFramebuffer(GL_DRAW_FRAMEBUFFER, m_historyFbo[m_historyHead]);
    glBlitFramebuffer(0, 0, m_width, m_height,
                      0, 0, m_width, m_height,
                      GL_COLOR_BUFFER_BIT, GL_NEAREST);
    // Advance ring-buffer head
    m_historyHead = (m_historyHead + 1) % MAX_BLUR_HISTORY;
}

// RENDER
void Renderer::render(const CameraState& cam, const std::vector<RenderObject>& objects) {
    m_context->makeCurrent();
    // PASS 1: 3D Scene → m_fbo / m_colorTex
    glBindFramebuffer(GL_FRAMEBUFFER, m_fbo);
    glViewport(0, 0, m_width, m_height);
    glEnable(GL_DEPTH_TEST);
    glClearColor(0.1f, 0.1f, 0.1f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    m_baseShader->use();
    m_baseShader->setVec3("lightPos", m_light.position.x, m_light.position.y, m_light.position.z);
    m_baseShader->setFloat("ambient", m_light.ambient);
    m_baseShader->setFloat("diffuseIntensity", m_light.diffuse);

    float v_fov = 2.0f * atanf((float)m_height / (2.0f * cam.focal_length));
    glm::mat4 proj = glm::perspective(v_fov, (float)m_width / m_height, cam.near_plane, cam.far_plane);
    glm::vec3 eye(cam.x, cam.y, cam.z);
    glm::vec3 forward(cosf(cam.yaw) * cosf(cam.pitch), sinf(cam.yaw) * cosf(cam.pitch), -sinf(cam.pitch));
    glm::mat4 view = glm::lookAt(eye, eye + forward, glm::vec3(0, 0, 1));
    glm::mat4 viewProj = proj * view;

    for (const auto& obj : objects) {
        m_baseShader->setVec4("color", obj.color.r, obj.color.g, obj.color.b, obj.color.a);

        switch (obj.type) {
            case RenderType::CIRCLE: {
                m_baseShader->setInt("isCircle", 1);
                glm::mat4 model;
                model = glm::translate(model, glm::vec3(obj.position.x, obj.position.y, obj.position.z));
                model.m[0] = view.m[0]; model.m[1] = view.m[4]; model.m[2] = view.m[8];
                model.m[4] = view.m[1]; model.m[5] = view.m[5]; model.m[6] = view.m[9];
                model.m[8] = view.m[2]; model.m[9] = view.m[6]; model.m[10] = view.m[10];
                model = glm::scale(model, glm::vec3(obj.size.x, obj.size.y, obj.size.z));
                m_baseShader->setMat4("model", model.ptr());
                m_baseShader->setMat4("mvp", (viewProj * model).ptr());
                m_quadMesh->draw();
                break;
            }
            case RenderType::CYLINDER: {
                m_baseShader->setInt("isCircle", 0);
                glm::mat4 model;
                model = glm::translate(model, glm::vec3(obj.position.x, obj.position.y, obj.position.z));
                model = glm::scale(model, glm::vec3(obj.size.x, obj.size.y, obj.size.z));
                m_baseShader->setMat4("model", model.ptr());
                m_baseShader->setMat4("mvp", (viewProj * model).ptr());
                m_cylinderMesh->draw();
                break;
            }
            case RenderType::MESH: {
                m_baseShader->setInt("isCircle", 0);
                glm::mat4 model;
                m_baseShader->setMat4("model", model.ptr());
                m_baseShader->setMat4("mvp", viewProj.ptr());
                m_dynamicMesh->update(obj.vertices);
                m_dynamicMesh->draw();
                break;
            }
            case RenderType::RECT:
            default: {
                m_baseShader->setInt("isCircle", 0);
                glm::mat4 model;
                model = glm::translate(model, glm::vec3(obj.position.x, obj.position.y, obj.position.z));
                model = glm::scale(model, glm::vec3(obj.size.x, obj.size.y, obj.size.z));
                m_baseShader->setMat4("model", model.ptr());
                m_baseShader->setMat4("mvp", (viewProj * model).ptr());
                m_cubeMesh->draw();
                break;
            }
        }
    }

    // PASS 2: Post-processing (fisheye + motion blur) → m_postFbo / m_postTex
    glBindFramebuffer(GL_FRAMEBUFFER, m_postFbo);
    glClear(GL_COLOR_BUFFER_BIT);
    glDisable(GL_DEPTH_TEST);

    m_postShader->use();

    // Bind frame on 0
    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, m_colorTex);
    m_postShader->setInt("screenTexture", 0);
    // Bind history on 1..MAX_BLUR_HISTORY
    // The history is ordered from most recent to oldest:
    // slot (head-1) = frame N-1, slot (head-2) = frame N-2, etc.
    for (int i = 0; i < MAX_BLUR_HISTORY; i++) {
        int slot = (m_historyHead - 1 - i + MAX_BLUR_HISTORY) % MAX_BLUR_HISTORY;
        glActiveTexture(GL_TEXTURE1 + i);
        glBindTexture(GL_TEXTURE_2D, m_historyTex[slot]);
        // historyTex[i] en el shader
        std::string name = "historyTex[" + std::to_string(i) + "]";
        m_postShader->setInt(name, 1 + i);
    }

    m_postShader->setFloat("k",                  m_fisheyeK);
    m_postShader->setFloat("zoom",               m_fisheyeZoom);
    m_postShader->setInt  ("motionBlurSamples",  m_motionBlurSamples);
    m_postShader->setFloat("motionBlurStrength", m_motionBlurStrength);
    m_screenQuadMesh->draw();
    // Save current frame in history (AFTER post-process)
    if (m_motionBlurSamples > 0) {
        rotateHistory();
    }
}

// GET FRAME
const std::vector<unsigned char>& Renderer::getFrame() {
    glBindFramebuffer(GL_FRAMEBUFFER, m_postFbo);
    glBindBuffer(GL_PIXEL_PACK_BUFFER, m_pbo);
    glReadPixels(0, 0, m_width, m_height, GL_RGBA, GL_UNSIGNED_BYTE, 0);
    unsigned char* ptr = (unsigned char*)glMapBuffer(GL_PIXEL_PACK_BUFFER, GL_READ_ONLY);
    if (ptr) {
        memcpy(m_frameBuffer.data(), ptr, m_frameBuffer.size());
        glUnmapBuffer(GL_PIXEL_PACK_BUFFER);
    }
    glBindBuffer(GL_PIXEL_PACK_BUFFER, 0);
    return m_frameBuffer;
}

} // namespace vision

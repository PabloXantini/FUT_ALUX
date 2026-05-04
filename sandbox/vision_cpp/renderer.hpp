#pragma once
#include <vector>
#include <memory>
#include "types.hpp"
#include "shader.hpp"
#include "gl_loader.hpp"

namespace vision {

static constexpr int MAX_BLUR_HISTORY = 7;

class Mesh {
public:
    Mesh();
    ~Mesh();
    void setup(const std::vector<float>& data, bool dynamic = false);
    void setupCustom(const std::vector<float>& data, int stride, int posSize, int texSize);
    void setup(const std::vector<Vertex>& vertices, bool dynamic = false);
    void draw(GLenum mode = GL_TRIANGLES) const;
    void update(const std::vector<Vertex>& vertices);

    GLuint vao, vbo;
    int count;
};

class Renderer {
public:
    Renderer(int width, int height);
    ~Renderer();

    bool initialize();
    void render(const CameraState& cam, const std::vector<RenderObject>& objects);
    void setLight(const LightState& light) { m_light = light; }

    // Post-processing controls
    void setFisheye(float k, float zoom) { m_fisheyeK = k; m_fisheyeZoom = zoom; }
    // strength: 0.0 (sin blur) .. 1.0 (blur máximo). samples: 1..MAX_BLUR_HISTORY.
    void setMotionBlur(float strength, int samples);

    const std::vector<unsigned char>& getFrame();

private:
    void setupBuffers();
    void setupShaders();
    void setupPrimitives();
    void rotateHistory();   // Desplaza el ring-buffer de texturas de historial

    int m_width, m_height;
    std::unique_ptr<IGraphicsContext> m_context;
    std::unique_ptr<Shader> m_baseShader;
    std::unique_ptr<Shader> m_postShader;

    // Scene FBO
    GLuint m_fbo, m_colorTex, m_depthTex;

    // Post-process FBO
    GLuint m_postFbo, m_postTex;

    // Motion blur: ring-buffer of history textures
    GLuint m_historyTex[MAX_BLUR_HISTORY];
    GLuint m_historyFbo[MAX_BLUR_HISTORY];
    int    m_historyHead = 0;  // Index of the oldest slot (will be overwritten first)

    GLuint m_pbo;
    std::vector<unsigned char> m_frameBuffer;

    std::unique_ptr<Mesh> m_cubeMesh;
    std::unique_ptr<Mesh> m_quadMesh;
    std::unique_ptr<Mesh> m_cylinderMesh;
    std::unique_ptr<Mesh> m_screenQuadMesh;
    std::unique_ptr<Mesh> m_dynamicMesh;

    LightState m_light;

    // Fisheye
    float m_fisheyeK    = -0.4f;
    float m_fisheyeZoom = 1.0f;

    // Motion blur
    float m_motionBlurStrength = 0.0f;
    int   m_motionBlurSamples  = 3;
};

} // namespace vision

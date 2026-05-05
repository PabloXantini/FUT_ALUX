#pragma once
#include <vector>

namespace vision {

struct Vec3 {
    float x, y, z;
    Vec3(float _x=0, float _y=0, float _z=0) : x(_x), y(_y), z(_z) {}
};

struct Vec4 {
    float r, g, b, a;
    Vec4(float _r=0, float _g=0, float _b=0, float _a=1) : r(_r), g(_g), b(_b), a(_a) {}
};

struct Vertex {
    float x, y, z;
    float nx, ny, nz;
    Vertex(float _x=0, float _y=0, float _z=0, float _nx=0, float _ny=0, float _nz=1) 
        : x(_x), y(_y), z(_z), nx(_nx), ny(_ny), nz(_nz) {}
};

enum class RenderType {
    CIRCLE,
    RECT, // Cube
    MESH,
    CYLINDER
};

struct RenderObject {
    RenderType type;
    Vec3 position;
    Vec3 size;
    Vec4 color;
    std::vector<Vertex> vertices; // Used for MESH
};

struct LightState {
    float ambient;
    float diffuse;
    Vec3 position;
    LightState() : ambient(0.4f), diffuse(0.8f), position(320, 240, 500) {}
};

struct CameraState {
    float x, y, z;
    float yaw, pitch, roll;
    float focal_length;
    float cx, cy;
    int width, height;
    float near_plane, far_plane;
    bool use_fisheye;
    bool use_motion_blur;
};

class IGraphicsContext {
public:
    virtual ~IGraphicsContext() = default;
    virtual bool initialize(int width, int height) = 0;
    virtual void makeCurrent() = 0;
    virtual void swapBuffers() = 0;
};

} // namespace vision

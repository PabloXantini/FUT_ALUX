#pragma once

#include <string>
#include <map>

namespace vision {

class Shader {
public:
    Shader() : m_id(0) {}
    ~Shader();

    bool load(const std::string& vertPath, const std::string& fragPath);
    void use();

    void setBool(const std::string& name, bool value);
    void setInt(const std::string& name, int value);
    void setFloat(const std::string& name, float value);
    void setVec2(const std::string& name, float x, float y);
    void setVec3(const std::string& name, float x, float y, float z);
    void setVec4(const std::string& name, float x, float y, float z, float w);
    void setMat4(const std::string& name, const float* matrix);

private:
    unsigned int m_id;
    std::map<std::string, int> m_uniformLocations;

    int getUniform(const std::string& name);
    std::string loadFile(const std::string& path);
    unsigned int compileShader(unsigned int type, const std::string& source);
};

} // namespace vision

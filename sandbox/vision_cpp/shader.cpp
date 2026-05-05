#include "shader.hpp"
#include "gl_loader.hpp"
#include <fstream>
#include <iostream>
#include <sstream>

namespace vision {

Shader::~Shader() {
  if (m_id != 0)
    glDeleteProgram(m_id);
}

bool Shader::load(const std::string &vertPath, const std::string &fragPath) {
  std::string vSrc = loadFile(vertPath);
  std::string fSrc = loadFile(fragPath);
  if (vSrc.empty() || fSrc.empty())
    return false;

  unsigned int vs = compileShader(GL_VERTEX_SHADER, vSrc);
  unsigned int fs = compileShader(GL_FRAGMENT_SHADER, fSrc);

  m_id = glCreateProgram();
  glAttachShader(m_id, vs);
  glAttachShader(m_id, fs);
  glLinkProgram(m_id);

  int success;
  glGetProgramiv(m_id, GL_LINK_STATUS, &success);
  if (!success) {
    char info[512];
    glGetProgramInfoLog(m_id, 512, NULL, info);
    std::cerr << "Shader linking error: " << info << std::endl;
    return false;
  }
  return true;
}

void Shader::use() { glUseProgram(m_id); }

int Shader::getUniform(const std::string &name) {
  if (m_uniformLocations.find(name) != m_uniformLocations.end())
    return m_uniformLocations[name];

  int loc = glGetUniformLocation(m_id, name.c_str());
  m_uniformLocations[name] = loc;
  return loc;
}

void Shader::setBool(const std::string &name, bool value) {
  glUniform1i(getUniform(name), (int)value);
}

void Shader::setInt(const std::string &name, int value) {
  glUniform1i(getUniform(name), value);
}

void Shader::setFloat(const std::string &name, float value) {
  glUniform1f(getUniform(name), value);
}

void Shader::setVec2(const std::string &name, float x, float y) {
  glUniform2f(getUniform(name), x, y);
}

void Shader::setVec3(const std::string &name, float x, float y, float z) {
  glUniform3f(getUniform(name), x, y, z);
}

void Shader::setVec4(const std::string &name, float x, float y, float z,
                     float w) {
  glUniform4f(getUniform(name), x, y, z, w);
}

void Shader::setMat4(const std::string &name, const float *matrix) {
  glUniformMatrix4fv(getUniform(name), 1, GL_FALSE, matrix);
}

std::string Shader::loadFile(const std::string &path) {
  std::ifstream file(path);
  if (!file.is_open()) {
    std::cerr << "Failed to open shader file: " << path << std::endl;
    return "";
  }
  std::stringstream buffer;
  buffer << file.rdbuf();
  return buffer.str();
}

unsigned int Shader::compileShader(unsigned int type,
                                   const std::string &source) {
  const char *src = source.c_str();
  unsigned int shader = glCreateShader(type);
  glShaderSource(shader, 1, &src, NULL);
  glCompileShader(shader);
  int success;
  glGetShaderiv(shader, GL_COMPILE_STATUS, &success);
  if (!success) {
    char info[512];
    glGetShaderInfoLog(shader, 512, NULL, info);
    std::cerr << "Shader compilation error (" << type << "): " << info
              << std::endl;
  }
  return shader;
}

} // namespace vision

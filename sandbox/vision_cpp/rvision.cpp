#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "renderer.hpp"

namespace py = pybind11;
using namespace vision;

PYBIND11_MODULE(rvision, m) {
    py::enum_<RenderType>(m, "RenderType")
        .value("CIRCLE", RenderType::CIRCLE)
        .value("RECT", RenderType::RECT)
        .value("MESH", RenderType::MESH)
        .value("CYLINDER", RenderType::CYLINDER)
        .export_values();

    py::class_<Vec3>(m, "Vec3")
        .def(py::init<float, float, float>())
        .def_readwrite("x", &Vec3::x)
        .def_readwrite("y", &Vec3::y)
        .def_readwrite("z", &Vec3::z);

    py::class_<Vec4>(m, "Vec4")
        .def(py::init<float, float, float, float>())
        .def_readwrite("r", &Vec4::r)
        .def_readwrite("g", &Vec4::g)
        .def_readwrite("b", &Vec4::b)
        .def_readwrite("a", &Vec4::a);

    py::class_<Vertex>(m, "Vertex")
        .def(py::init<float, float, float, float, float, float>(), 
             py::arg("x")=0, py::arg("y")=0, py::arg("z")=0, 
             py::arg("nx")=0, py::arg("ny")=0, py::arg("nz")=1)
        .def_readwrite("x", &Vertex::x)
        .def_readwrite("y", &Vertex::y)
        .def_readwrite("z", &Vertex::z)
        .def_readwrite("nx", &Vertex::nx)
        .def_readwrite("ny", &Vertex::ny)
        .def_readwrite("nz", &Vertex::nz);

    py::class_<RenderObject>(m, "RenderObject")
        .def(py::init<>())
        .def_readwrite("type", &RenderObject::type)
        .def_readwrite("vertices", &RenderObject::vertices)
        .def_readwrite("position", &RenderObject::position)
        .def_readwrite("size", &RenderObject::size)
        .def_readwrite("color", &RenderObject::color);

    py::class_<CameraState>(m, "CameraState")
        .def(py::init<>())
        .def_readwrite("x", &CameraState::x)
        .def_readwrite("y", &CameraState::y)
        .def_readwrite("z", &CameraState::z)
        .def_readwrite("yaw", &CameraState::yaw)
        .def_readwrite("pitch", &CameraState::pitch)
        .def_readwrite("roll", &CameraState::roll)
        .def_readwrite("focal_length", &CameraState::focal_length)
        .def_readwrite("cx", &CameraState::cx)
        .def_readwrite("cy", &CameraState::cy)
        .def_readwrite("width", &CameraState::width)
        .def_readwrite("height", &CameraState::height)
        .def_readwrite("near_plane", &CameraState::near_plane)
        .def_readwrite("far_plane", &CameraState::far_plane);

    py::class_<LightState>(m, "LightState")
        .def(py::init<>())
        .def_readwrite("ambient", &LightState::ambient)
        .def_readwrite("diffuse", &LightState::diffuse)
        .def_readwrite("position", &LightState::position);

    py::class_<Renderer>(m, "Renderer")
        .def(py::init<int, int>())
        .def("initialize", &Renderer::initialize)
        .def("render", &Renderer::render)
        .def("set_light", &Renderer::setLight)
        // Post-processing
        .def("set_fisheye", &Renderer::setFisheye,
             py::arg("k")=-0.4f, py::arg("zoom")=1.0f)
        .def("set_motion_blur", &Renderer::setMotionBlur,
             py::arg("strength")=0.5f, py::arg("samples")=3,
             "strength: 0.0 (sin blur) .. 1.0 (blur máximo). "
             "samples: cantidad de frames del historial a mezclar (1..7).")
        .def("get_frame", [](Renderer& self) {
            const auto& frame = self.getFrame();
            return py::array_t<unsigned char>(
                { (size_t)frame.size() / 4, (size_t)4 },
                frame.data()
            );
        });
}

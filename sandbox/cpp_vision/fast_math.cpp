#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>

namespace py = pybind11;

py::array_t<double> project_3d_vectorized(
    py::array_t<double> points,
    double obs_x, double obs_y, double obs_rangle,
    double camera_height, double yaw_off, double pitch,
    double _near, double _far,
    double focal_length, double cx, double cy) {

    auto buf = points.request();
    if (buf.ndim != 2 || buf.shape[1] != 3) {
        throw std::runtime_error("Points must be an Nx3 array");
    }

    size_t N = buf.shape[0];
    auto result = py::array_t<double>({N, (size_t)3});
    auto res_buf = result.request();

    double* ptr = static_cast<double*>(buf.ptr);
    double* out = static_cast<double*>(res_buf.ptr);

    double total_yaw = obs_rangle + yaw_off;
    double cos_y = std::cos(total_yaw);
    double sin_y = std::sin(total_yaw);

    double cos_p = std::cos(pitch);
    double sin_p = std::sin(pitch);

    for (size_t i = 0; i < N; i++) {
        double px = ptr[i * 3 + 0];
        double py = ptr[i * 3 + 1];
        double pz = ptr[i * 3 + 2];

        double dx = px - obs_x;
        double dy = py - obs_y;
        double dz = pz - camera_height;

        double y_rel = dx * cos_y + dy * sin_y;
        double x_rel = -dx * sin_y + dy * cos_y;
        double z_rel = dz;

        double y_p = y_rel * cos_p - z_rel * sin_p;
        double z_p = y_rel * sin_p + z_rel * cos_p;

        double x_cam = x_rel;
        double y_cam = -z_p;
        double z_cam = y_p;

        if (z_cam > _near && z_cam < _far) {
            out[i * 3 + 0] = (focal_length * x_cam / z_cam) + cx;
            out[i * 3 + 1] = (focal_length * y_cam / z_cam) + cy;
            out[i * 3 + 2] = z_cam;
        } else {
            out[i * 3 + 0] = 0;
            out[i * 3 + 1] = 0;
            out[i * 3 + 2] = 0;
        }
    }

    return result;
}

py::tuple project_3d_scalar(
    double px, double py, double pz,
    double obs_x, double obs_y, double obs_rangle,
    double camera_height, double yaw_off, double pitch,
    double _near, double _far,
    double focal_length, double cx, double cy) {
    
    double dx = px - obs_x;
    double dy = py - obs_y;
    double dz = pz - camera_height;

    double total_yaw = obs_rangle + yaw_off;
    double cos_y = std::cos(total_yaw);
    double sin_y = std::sin(total_yaw);

    double y_rel = dx * cos_y + dy * sin_y;
    double x_rel = -dx * sin_y + dy * cos_y;
    double z_rel = dz;

    double cos_p = std::cos(pitch);
    double sin_p = std::sin(pitch);

    double y_p = y_rel * cos_p - z_rel * sin_p;
    double z_p = y_rel * sin_p + z_rel * cos_p;

    double x_cam = x_rel;
    double y_cam = -z_p;
    double z_cam = y_p;

    if (z_cam > _near && z_cam < _far) {
        return py::make_tuple((focal_length * x_cam / z_cam) + cx, (focal_length * y_cam / z_cam) + cy, z_cam);
    }
    return py::make_tuple(0.0, 0.0, 0.0);
}

PYBIND11_MODULE(fast_math, m) {
    m.def("project_3d_vectorized", &project_3d_vectorized, "Project 3D points to 2D using camera parameters");
    m.def("project_3d_scalar", &project_3d_scalar, "Project single 3D point to 2D using camera parameters");
}

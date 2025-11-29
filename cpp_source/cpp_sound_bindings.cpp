#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "sound_player.h"

namespace py = pybind11;

PYBIND11_MODULE(cpp_sound, m) {
    py::class_<SoundPlayer>(m, "SoundPlayer")
        .def(py::init<const std::map<std::string, std::string>&>())
        .def("play", &SoundPlayer::play)
        .def("set_volume", &SoundPlayer::set_volume)
        .def("set_master_volume", &SoundPlayer::set_master_volume)
        .def("volume_up", &SoundPlayer::volume_up, py::arg("key"), py::arg("step") = 0.1f)
        .def("volume_down", &SoundPlayer::volume_down, py::arg("key"), py::arg("step") = 0.1f)
        .def("master_volume_up", &SoundPlayer::master_volume_up, py::arg("step") = 0.1f)
        .def("master_volume_down", &SoundPlayer::master_volume_down, py::arg("step") = 0.1f)
        .def("set_max_volume", &SoundPlayer::set_max_volume, py::arg("max_vol"))
        .def("set_min_volume", &SoundPlayer::set_min_volume, py::arg("min_vol"))
        .def("get_max_volume", &SoundPlayer::get_max_volume) // these return float
        .def("get_min_volume", &SoundPlayer::get_min_volume);
}

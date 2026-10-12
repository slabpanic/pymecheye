#include "bindings.h"

template <typename T, typename Function>
std::pair<eye::ErrorStatus, T> user_get(const UserSetHandle &h, Function f) {
    return sdk_call([&] {
        T value{};
        if (!valid_handle(h))
            return std::make_pair(invalid_device(), value);
        auto status = f(h.state->camera->currentUserSet(), value);
        return std::make_pair(status, std::move(value));
    });
}
template <typename Function> eye::ErrorStatus user_set(const UserSetHandle &h, Function f) {
    return sdk_call([&] {
        if (!valid_handle(h))
            return invalid_device();
        return f(h.state->camera->currentUserSet());
    });
}
template <typename P, typename T, typename Function>
std::pair<eye::ErrorStatus, T> parameter_get(const ParameterHandle &h, Function f) {
    return sdk_call([&] {
        T value{};
        if (!valid_handle(h))
            return std::make_pair(invalid_device(), value);
        auto *p =
            dynamic_cast<P *>(h.state->camera->currentUserSet().getParameter(h.parameter_name));
        if (!p)
            return std::make_pair(invalid_parameter(), value);
        auto status = f(*p, value);
        return std::make_pair(status, std::move(value));
    });
}
template <typename P, typename Function>
eye::ErrorStatus parameter_set(const ParameterHandle &h, Function f) {
    return sdk_call([&] {
        if (!valid_handle(h))
            return invalid_device();
        auto *p =
            dynamic_cast<P *>(h.state->camera->currentUserSet().getParameter(h.parameter_name));
        if (!p)
            return invalid_parameter();
        return f(*p);
    });
}

void bind_parameters(nb::module_ &m) {
    auto u = nb::class_<UserSetHandle>(m, "UserSet");
    auto g = nb::class_<ManagerHandle>(m, "UserSetManager");
    auto p = nb::class_<ParameterHandle>(m, "Parameter");
    u.def("get_name", [](const UserSetHandle &h) {
        return user_get<std::string>(h,
                                     [](eye::UserSet &u, std::string &v) { return u.getName(v); });
    });
    u.def("get_available_parameter_names", [](const UserSetHandle &h) {
        return user_get<std::vector<std::string>>(h,
                                                  [](eye::UserSet &u, std::vector<std::string> &v) {
                                                      return u.getAvailableParameterNames(v);
                                                  });
    });
    u.def("rename", [](const UserSetHandle &h, const std::string &name) {
        return user_set(h, [&](eye::UserSet &u) { return u.rename(name); });
    });
    u.def("reset_all_parameters_to_default_values", [](const UserSetHandle &h) {
        return user_set(h, [](eye::UserSet &u) { return u.resetAllParametersToDefaultValues(); });
    });
    u.def("save_all_parameters_to_device", [](const UserSetHandle &h) {
        return user_set(h, [](eye::UserSet &u) { return u.saveAllParametersToDevice(); });
    });
    u.def("get_available_parameters", [](const UserSetHandle &h) {
        return sdk_call([&] {
            std::vector<ParameterHandle> result;
            if (!valid_handle(h))
                return result;
            for (auto *parameter : h.state->camera->currentUserSet().getAvailableParameters()) {
                if (parameter) {
                    ParameterHandle v;
                    v.state = h.state;
                    v.generation = h.generation;
                    v.parameter_name = parameter->name();
                    result.push_back(std::move(v));
                }
            }
            return result;
        });
    });
    u.def("get_parameter", [](const UserSetHandle &h, const std::string &name) -> nb::object {
        const bool exists = sdk_call([&] {
            return valid_handle(h) &&
                   h.state->camera->currentUserSet().getParameter(name) != nullptr;
        });
        if (!exists)
            return nb::none();
        ParameterHandle p;
        p.state = h.state;
        p.generation = h.generation;
        p.parameter_name = name;
        return nb::cast(p);
    });
    g.def("current_user_set",
          [](const ManagerHandle &h) { return UserSetHandle{h.state, h.generation}; });
    g.def("get_all_user_set_names", [](const ManagerHandle &h) {
        return sdk_call([&] {
            std::vector<std::string> names;
            if (!valid_handle(h))
                return std::make_pair(invalid_device(), names);
            auto status = h.state->camera->userSetManager().getAllUserSetNames(names);
            return std::make_pair(status, names);
        });
    });

    g.def("select_user_set", [](const ManagerHandle &h, const std::string &value) {
        return sdk_call([&] {
            if (!valid_handle(h))
                return invalid_device();
            return h.state->camera->userSetManager().selectUserSet(value);
        });
    });
    g.def("add_user_set", [](const ManagerHandle &h, const std::string &value) {
        return sdk_call([&] {
            if (!valid_handle(h))
                return invalid_device();
            return h.state->camera->userSetManager().addUserSet(value);
        });
    });
    g.def("delete_user_set", [](const ManagerHandle &h, const std::string &value) {
        return sdk_call([&] {
            if (!valid_handle(h))
                return invalid_device();
            return h.state->camera->userSetManager().deleteUserSet(value);
        });
    });
    g.def("save_to_file", [](const ManagerHandle &h, const std::string &value) {
        return sdk_call([&] {
            if (!valid_handle(h))
                return invalid_device();
            return h.state->camera->userSetManager().saveToFile(value);
        });
    });
    g.def("load_from_file", [](const ManagerHandle &h, const std::string &value) {
        return sdk_call([&] {
            if (!valid_handle(h))
                return invalid_device();
            return h.state->camera->userSetManager().loadFromFile(value);
        });
    });
    p.def("name", [](const ParameterHandle &h) {
        return sdk_call([&] {
            if (!valid_handle(h))
                throw std::runtime_error(
                    "Parameter handle expired after camera disconnect or reconnect");
            auto *value = h.state->camera->currentUserSet().getParameter(h.parameter_name);
            if (!value)
                throw std::runtime_error("Parameter is no longer available");
            return value->name();
        });
    });
    p.def("description", [](const ParameterHandle &h) {
        return sdk_call([&] {
            if (!valid_handle(h))
                throw std::runtime_error(
                    "Parameter handle expired after camera disconnect or reconnect");
            auto *value = h.state->camera->currentUserSet().getParameter(h.parameter_name);
            if (!value)
                throw std::runtime_error("Parameter is no longer available");
            return value->description();
        });
    });
    p.def("is_writable", [](const ParameterHandle &h) {
        return sdk_call([&] {
            if (!valid_handle(h))
                throw std::runtime_error(
                    "Parameter handle expired after camera disconnect or reconnect");
            auto *value = h.state->camera->currentUserSet().getParameter(h.parameter_name);
            if (!value)
                throw std::runtime_error("Parameter is no longer available");
            return value->isWritable();
        });
    });
    p.def("is_readable", [](const ParameterHandle &h) {
        return sdk_call([&] {
            if (!valid_handle(h))
                throw std::runtime_error(
                    "Parameter handle expired after camera disconnect or reconnect");
            auto *value = h.state->camera->currentUserSet().getParameter(h.parameter_name);
            if (!value)
                throw std::runtime_error("Parameter is no longer available");
            return value->isReadable();
        });
    });
    p.def("type", [](const ParameterHandle &h) {
        return sdk_call([&] {
            if (!valid_handle(h))
                throw std::runtime_error(
                    "Parameter handle expired after camera disconnect or reconnect");
            auto *value = h.state->camera->currentUserSet().getParameter(h.parameter_name);
            if (!value)
                throw std::runtime_error("Parameter is no longer available");
            return int(value->type());
        });
    });
    u.def("get_int_value", [](const UserSetHandle &h, const std::string &name) {
        return user_get<int>(h, [&](eye::UserSet &u, int &v) { return u.getIntValue(name, v); });
    });
    p.def("get_int_value", [](const ParameterHandle &h) {
        return parameter_get<eye::IntParameter, int>(
            h, [](eye::IntParameter &p, int &v) { return p.getValue(v); });
    });
    u.def("set_int_value", [](const UserSetHandle &h, const std::string &name, const int &v) {
        return user_set(h, [&](eye::UserSet &u) { return u.setIntValue(name, v); });
    });
    p.def("set_int_value", [](const ParameterHandle &h, const int &v) {
        return parameter_set<eye::IntParameter>(
            h, [&](eye::IntParameter &p) { return p.setValue(v); });
    });
    u.def("get_float_value", [](const UserSetHandle &h, const std::string &name) {
        return user_get<double>(
            h, [&](eye::UserSet &u, double &v) { return u.getFloatValue(name, v); });
    });
    p.def("get_float_value", [](const ParameterHandle &h) {
        return parameter_get<eye::FloatParameter, double>(
            h, [](eye::FloatParameter &p, double &v) { return p.getValue(v); });
    });
    u.def("set_float_value", [](const UserSetHandle &h, const std::string &name, const double &v) {
        return user_set(h, [&](eye::UserSet &u) { return u.setFloatValue(name, v); });
    });
    p.def("set_float_value", [](const ParameterHandle &h, const double &v) {
        return parameter_set<eye::FloatParameter>(
            h, [&](eye::FloatParameter &p) { return p.setValue(v); });
    });
    u.def("get_bool_value", [](const UserSetHandle &h, const std::string &name) {
        return user_get<bool>(h, [&](eye::UserSet &u, bool &v) { return u.getBoolValue(name, v); });
    });
    p.def("get_bool_value", [](const ParameterHandle &h) {
        return parameter_get<eye::BoolParameter, bool>(
            h, [](eye::BoolParameter &p, bool &v) { return p.getValue(v); });
    });
    u.def("set_bool_value", [](const UserSetHandle &h, const std::string &name, const bool &v) {
        return user_set(h, [&](eye::UserSet &u) { return u.setBoolValue(name, v); });
    });
    p.def("set_bool_value", [](const ParameterHandle &h, const bool &v) {
        return parameter_set<eye::BoolParameter>(
            h, [&](eye::BoolParameter &p) { return p.setValue(v); });
    });
    u.def("get_enum_value", [](const UserSetHandle &h, const std::string &name) {
        return user_get<int>(h, [&](eye::UserSet &u, int &v) { return u.getEnumValue(name, v); });
    });
    p.def("get_enum_value", [](const ParameterHandle &h) {
        return parameter_get<eye::EnumParameter, int>(
            h, [](eye::EnumParameter &p, int &v) { return p.getValue(v); });
    });
    u.def("set_enum_value", [](const UserSetHandle &h, const std::string &name, const int &v) {
        return user_set(h, [&](eye::UserSet &u) { return u.setEnumValue(name, v); });
    });
    p.def("set_enum_value", [](const ParameterHandle &h, const int &v) {
        return parameter_set<eye::EnumParameter>(
            h, [&](eye::EnumParameter &p) { return p.setValue(v); });
    });
    u.def("get_enum_value_string", [](const UserSetHandle &h, const std::string &name) {
        return user_get<std::string>(
            h, [&](eye::UserSet &u, std::string &v) { return u.getEnumValue(name, v); });
    });
    p.def("get_enum_value_string", [](const ParameterHandle &h) {
        return parameter_get<eye::EnumParameter, std::string>(
            h, [](eye::EnumParameter &p, std::string &v) { return p.getValue(v); });
    });
    u.def("set_enum_value",
          [](const UserSetHandle &h, const std::string &name, const std::string &v) {
              return user_set(h, [&](eye::UserSet &u) { return u.setEnumValue(name, v); });
          });
    p.def("set_enum_value", [](const ParameterHandle &h, const std::string &v) {
        return parameter_set<eye::EnumParameter>(
            h, [&](eye::EnumParameter &p) { return p.setValue(v); });
    });
    u.def("get_roi_value", [](const UserSetHandle &h, const std::string &name) {
        return user_get<eye::ROI>(
            h, [&](eye::UserSet &u, eye::ROI &v) { return u.getRoiValue(name, v); });
    });
    p.def("get_roi_value", [](const ParameterHandle &h) {
        return parameter_get<eye::RoiParameter, eye::ROI>(
            h, [](eye::RoiParameter &p, eye::ROI &v) { return p.getValue(v); });
    });
    u.def("set_roi_value", [](const UserSetHandle &h, const std::string &name, const eye::ROI &v) {
        return user_set(h, [&](eye::UserSet &u) { return u.setRoiValue(name, v); });
    });
    p.def("set_roi_value", [](const ParameterHandle &h, const eye::ROI &v) {
        return parameter_set<eye::RoiParameter>(
            h, [&](eye::RoiParameter &p) { return p.setValue(v); });
    });
    u.def("get_profile_roi_value", [](const UserSetHandle &h, const std::string &name) {
        return user_get<eye::ProfileROI>(
            h, [&](eye::UserSet &u, eye::ProfileROI &v) { return u.getProfileRoiValue(name, v); });
    });
    p.def("get_profile_roi_value", [](const ParameterHandle &h) {
        return parameter_get<eye::ProfileRoiParameter, eye::ProfileROI>(
            h, [](eye::ProfileRoiParameter &p, eye::ProfileROI &v) { return p.getValue(v); });
    });
    u.def("set_profile_roi_value",
          [](const UserSetHandle &h, const std::string &name, const eye::ProfileROI &v) {
              return user_set(h, [&](eye::UserSet &u) { return u.setProfileRoiValue(name, v); });
          });
    p.def("set_profile_roi_value", [](const ParameterHandle &h, const eye::ProfileROI &v) {
        return parameter_set<eye::ProfileRoiParameter>(
            h, [&](eye::ProfileRoiParameter &p) { return p.setValue(v); });
    });
    u.def("get_range_value", [](const UserSetHandle &h, const std::string &name) {
        return user_get<eye::Range<int>>(
            h, [&](eye::UserSet &u, eye::Range<int> &v) { return u.getRangeValue(name, v); });
    });
    p.def("get_range_value", [](const ParameterHandle &h) {
        return parameter_get<eye::RangeParameter, eye::Range<int>>(
            h, [](eye::RangeParameter &p, eye::Range<int> &v) { return p.getValue(v); });
    });
    u.def("set_range_value",
          [](const UserSetHandle &h, const std::string &name, const eye::Range<int> &v) {
              return user_set(h, [&](eye::UserSet &u) { return u.setRangeValue(name, v); });
          });
    p.def("set_range_value", [](const ParameterHandle &h, const eye::Range<int> &v) {
        return parameter_set<eye::RangeParameter>(
            h, [&](eye::RangeParameter &p) { return p.setValue(v); });
    });
    u.def("get_float_array_value", [](const UserSetHandle &h, const std::string &name) {
        return user_get<std::vector<double>>(h, [&](eye::UserSet &u, std::vector<double> &v) {
            return u.getFloatArrayValue(name, v);
        });
    });
    p.def("get_float_array_value", [](const ParameterHandle &h) {
        return parameter_get<eye::FloatArrayParameter, std::vector<double>>(
            h, [](eye::FloatArrayParameter &p, std::vector<double> &v) { return p.getValue(v); });
    });
    u.def("set_float_array_value",
          [](const UserSetHandle &h, const std::string &name, const std::vector<double> &v) {
              return user_set(h, [&](eye::UserSet &u) { return u.setFloatArrayValue(name, v); });
          });
    p.def("set_float_array_value", [](const ParameterHandle &h, const std::vector<double> &v) {
        return parameter_set<eye::FloatArrayParameter>(
            h, [&](eye::FloatArrayParameter &p) { return p.setValue(v); });
    });
    u.def("get_roi_array_value", [](const UserSetHandle &h, const std::string &name) {
        return user_get<std::vector<eye::ROI>>(h, [&](eye::UserSet &u, std::vector<eye::ROI> &v) {
            return u.getRoiArrayValue(name, v);
        });
    });
    p.def("get_roi_array_value", [](const ParameterHandle &h) {
        return parameter_get<eye::RoiArrayParameter, std::vector<eye::ROI>>(
            h, [](eye::RoiArrayParameter &p, std::vector<eye::ROI> &v) { return p.getValue(v); });
    });
    p.def("int_get_min", [](const ParameterHandle &h) {
        return parameter_get<eye::IntParameter, int>(
            h, [](eye::IntParameter &p, int &v) { return p.getMin(v); });
    });
    p.def("int_get_max", [](const ParameterHandle &h) {
        return parameter_get<eye::IntParameter, int>(
            h, [](eye::IntParameter &p, int &v) { return p.getMax(v); });
    });
    p.def("int_get_step", [](const ParameterHandle &h) {
        return parameter_get<eye::IntParameter, int>(
            h, [](eye::IntParameter &p, int &v) { return p.getStep(v); });
    });
    p.def("int_get_unit", [](const ParameterHandle &h) {
        return parameter_get<eye::IntParameter, std::string>(
            h, [](eye::IntParameter &p, std::string &v) { return p.getUnit(v); });
    });
    p.def("float_get_min", [](const ParameterHandle &h) {
        return parameter_get<eye::FloatParameter, double>(
            h, [](eye::FloatParameter &p, double &v) { return p.getMin(v); });
    });
    p.def("float_get_max", [](const ParameterHandle &h) {
        return parameter_get<eye::FloatParameter, double>(
            h, [](eye::FloatParameter &p, double &v) { return p.getMax(v); });
    });
    p.def("float_get_step", [](const ParameterHandle &h) {
        return parameter_get<eye::FloatParameter, double>(
            h, [](eye::FloatParameter &p, double &v) { return p.getStep(v); });
    });
    p.def("float_get_unit", [](const ParameterHandle &h) {
        return parameter_get<eye::FloatParameter, std::string>(
            h, [](eye::FloatParameter &p, std::string &v) { return p.getUnit(v); });
    });
    p.def("range_get_min", [](const ParameterHandle &h) {
        return parameter_get<eye::RangeParameter, int>(
            h, [](eye::RangeParameter &p, int &v) { return p.getMin(v); });
    });
    p.def("range_get_max", [](const ParameterHandle &h) {
        return parameter_get<eye::RangeParameter, int>(
            h, [](eye::RangeParameter &p, int &v) { return p.getMax(v); });
    });
    p.def("range_get_step", [](const ParameterHandle &h) {
        return parameter_get<eye::RangeParameter, int>(
            h, [](eye::RangeParameter &p, int &v) { return p.getStep(v); });
    });
    p.def("range_get_unit", [](const ParameterHandle &h) {
        return parameter_get<eye::RangeParameter, std::string>(
            h, [](eye::RangeParameter &p, std::string &v) { return p.getUnit(v); });
    });
    p.def("float_array_get_min", [](const ParameterHandle &h) {
        return parameter_get<eye::FloatArrayParameter, double>(
            h, [](eye::FloatArrayParameter &p, double &v) { return p.getMin(v); });
    });
    p.def("float_array_get_max", [](const ParameterHandle &h) {
        return parameter_get<eye::FloatArrayParameter, double>(
            h, [](eye::FloatArrayParameter &p, double &v) { return p.getMax(v); });
    });
    p.def("float_array_get_step", [](const ParameterHandle &h) {
        return parameter_get<eye::FloatArrayParameter, double>(
            h, [](eye::FloatArrayParameter &p, double &v) { return p.getStep(v); });
    });
    p.def("float_array_get_unit", [](const ParameterHandle &h) {
        return parameter_get<eye::FloatArrayParameter, std::string>(
            h, [](eye::FloatArrayParameter &p, std::string &v) { return p.getUnit(v); });
    });

    p.def("get_enum_values", [](const ParameterHandle &h) {
        return parameter_get<eye::EnumParameter, std::map<std::string, int>>(
            h, [](eye::EnumParameter &p, std::map<std::string, int> &v) { return p.getValues(v); });
    });
    p.def("get_max_array_size", [](const ParameterHandle &h) {
        return parameter_get<eye::FloatArrayParameter, int>(
            h, [](eye::FloatArrayParameter &p, int &v) { return p.getMaxArraySize(v); });
    });
    p.def("get_max_roi_size", [](const ParameterHandle &h, eye::Size &size) {
        auto result = parameter_get<eye::RoiParameter, eye::Size>(
            h, [](eye::RoiParameter &p, eye::Size &v) { return p.getMaxRoiSize(v); });
        size = result.second;
        return result.first;
    });
    p.def("get_max_profile_roi_size", [](const ParameterHandle &h, eye::SizeF &size) {
        auto result = parameter_get<eye::ProfileRoiParameter, eye::SizeF>(
            h, [](eye::ProfileRoiParameter &p, eye::SizeF &v) { return p.getMaxRoiSize(v); });
        size = result.second;
        return result.first;
    });
    p.def("get_min_profile_roi_size", [](const ParameterHandle &h, eye::SizeF &size) {
        auto result = parameter_get<eye::ProfileRoiParameter, eye::SizeF>(
            h, [](eye::ProfileRoiParameter &p, eye::SizeF &v) { return p.getMinRoiSize(v); });
        size = result.second;
        return result.first;
    });
}

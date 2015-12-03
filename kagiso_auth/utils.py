from inspect import isfunction


def get_setting(setting, request):
    value = setting

    if isfunction(value):
        value = value(request)

    return value

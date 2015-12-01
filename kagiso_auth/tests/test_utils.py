from ..utils import get_setting


def test_get_setting_with_primitive():
    setting = 'abc'

    result = get_setting(setting, None)

    assert result == setting


def test_get_setting_with_lambda():
    setting = lambda request: request
    request = object()

    result = get_setting(setting, request)

    assert result == request

import re

import pytest

from .. import config


def test_api():
    class MyConfig(config.Config):

        test_float = config.FLOAT()
        test_number = config.NUMBER()

        class personal_details(config.Section):
            name = config.STR()
            age = config.INT(default=30)
            postcode = config.STR(test=lambda x: re.search(r'[A-Za-z]\d\d\s?\d[A-Za-z][A-Za-z]', x))


    c = MyConfig({"personal_details": {"name": "Jeremy", "postcode": "X45 4DF"}, "test_float": 3.6, "test_number": 3.45})
    assert c['personal_details.name'] == "Jeremy"
    assert c['personal_details.age'] == 30
    assert c['personal_details.postcode'] == "X45 4DF"
    assert c['test_float'] == 3.6
    assert c['test_number'] == 3.45


def test_failure():
    class MyConfig(config.Config):

        test_int = config.INT(test=lambda x: x > 5)

    # Missing required val
    with pytest.raises(ValueError):
        MyConfig({})

    # Wrong type
    with pytest.raises(ValueError):
        MyConfig({'test_int': 'hello'})
    with pytest.raises(ValueError):
        MyConfig({'test_int': 7.8})

    # Doesn't pass test
    with pytest.raises(ValueError):
        MyConfig({'test_int': 2})


def test_other_formats():
    class JSONConfig(config.Config):
        test_int = config.INT()

    c = JSONConfig('{"test_int": 3}', format=config.Format.JSON)
    assert c['test_int'] == 3


    class YAMLConfig(config.Config):
        test_int = config.INT()

    c = YAMLConfig('test_int: 7', format=config.Format.YAML)
    assert c['test_int'] == 7


    class INIConfig(config.Config):

        class section(config.Section):
            test_int = config.INT()

    c = INIConfig('''
        [section]
        test_int = 9''', format='ini')

    assert c['section.test_int'] == 9


def test_load_from_file():
    class MyConfig(config.Config):
        test_str = config.STR()

    c = MyConfig('myfile.json', format=config.Format.JSON)
    assert c['test_str'] == "something witty"


def test_dotify():
    assert config.dotify({
        "name": "value",
        "key": {
                "subkey": "value",
                "other_subkey": "value2"
            }
        }) == {"name": "value", "key.subkey": "value", "key.other_subkey": "value2"}
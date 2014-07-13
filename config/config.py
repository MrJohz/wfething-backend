import configparser
import enum

import kaptan

from .options import *
from .iniparser import IniHandler

kaptan.Kaptan.HANDLER_MAP['ini'] = IniHandler


class Format(enum.Enum):
    INI = 'ini'
    DICT = 'dict'
    JSON = 'json'
    YAML = 'yaml'


def dotify(dct, *, initial_key='', sep='.'):
    ret = {}
    for rkey, val in dct.items():
        key = initial_key + rkey
        if isinstance(val, dict):
            ret.update(dotify(val, initial_key=key+sep))
        else:
            ret[key] = val
    return ret


def recurse_config(dct):
    config_dict = {}

    for key, value in dct.items():
        if isinstance(value, type) and issubclass(value, Section):
            config_dict[key] = recurse_config(value.__dict__)
        elif isinstance(value, Option):
            config_dict[key] = value

    return dotify(config_dict)


class MetaConfig(type):

    def __new__(meta, name, bases, dct):
        config_dict = recurse_config(dct)

        dct['__config_init__'] = config_dict
        dct['__config__'] = {}

        return super(MetaConfig, meta).__new__(meta, name, bases, dct)

    def __call__(cls, config, *, format=Format.DICT):
        if isinstance(format, Format):
            format = format.value

        config = kaptan.Kaptan(handler=format).import_config(config).configuration_data

        flat_config = dotify(config, sep=".")
        for name, option in cls.__config_init__.items():
            if name in flat_config:
                value = flat_config[name]
                if format == Format.INI.value:
                    value = option.convert(value)

                if option.is_valid(value):
                    cls.__config__[name] = value
                else:
                    raise ValueError("Config with key {name} is invalid".format(name=name))
                    
            elif option.has_default and option.is_valid(option.default):
                cls.__config__[name] = option.default
            else:
                raise ValueError("Config does not have all required values")

        return super(MetaConfig, cls).__call__(config)


class Config(metaclass=MetaConfig):
    def __new__(cls, *args, **kwargs):
        return super(Config, cls).__new__(cls)

    def __init__(self, *args, **kwargs):
        pass

    def __getitem__(self, key):
        return self.__config__[key]
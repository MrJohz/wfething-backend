import configparser
from io import StringIO

from kaptan.handlers import BaseHandler


class KaptanIniParser(configparser.ConfigParser):

    def as_dict(self):
        d = dict(self._sections)
        for k in d:
            d[k] = dict(self._defaults, **d[k])
            d[k].pop('__name__', None)
        return d


class IniHandler(BaseHandler):

    def load(self, value):
        config = KaptanIniParser(interpolation=configparser.ExtendedInterpolation())
        # ConfigParser.ConfigParser wants to read value as file / IO
        config.read_file(StringIO(value))
        return config.as_dict()

    def dump(self, file_):
        raise NotImplementedError("Exporting .ini files is not supported.")
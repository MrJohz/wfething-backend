from numbers import Number

NOOP = lambda ret: lambda *args, **kwargs: ret

class Section():
    pass

class Option():

    sentinal = object()

    def __init__(self, **kwargs):
        self.custom_test = kwargs.get('test', NOOP(True))

        self.default = kwargs.get('default', self.sentinal)
        if self.default is self.sentinal:
            self.has_default = False
        else:
            self.has_default = True

    def is_valid(self, var):
        return self.test(var) and self.custom_test(var)

    def convert(self, var):
        return var

    def test(self):
        return True


class INT(Option):

    def convert(self, var:str):
        try:
            return int(var)
        except ValueError:
            return None
    
    def test(self, var):
        return True if isinstance(var, int) else False


class STR(Option):

    def convert(self, var:str):
        return var
    
    def test(self, var):
        return True if isinstance(var, str) else False


class NUMBER(Option):

    def convert(self, var:str):
        try:
            return int(i)
        except ValueError:
            try:
                return float(i)
            except ValueError:
                return None

    def test(self, var):
        return True if isinstance(var, Number) else False


class FLOAT(Option):

    def convert(self, var:str):
        try:
            return float(i)
        except ValueError:
            return None

    def test(self, var):
        return True if isinstance(var, float) else False
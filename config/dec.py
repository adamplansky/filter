
class Kls(object):
    a = False
    @classmethod
    def __init__(cls):
        cls.a = True
        print("init")

    @classmethod
    def aa(cls):
        if(cls.a == False):
            Kls.__init__()
        print("aa")

Kls.aa()
Kls.aa()
Kls.aa()
Kls.aa()

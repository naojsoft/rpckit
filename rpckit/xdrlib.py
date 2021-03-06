"""Implements (a subset of) Sun XDR -- eXternal Data Representation.

See: RFC 1014

"""
import struct
import string
from types import *

long = int

from io import BytesIO as _StringIO

__all__ = ["Error", "Packer", "Unpacker", "ConversionError"]

str_encoding = 'latin1'

# exceptions
class Error(Exception):
    """Exception class for this module. Use:

    except xdrlib.Error, var:
        # var has the Error instance for the exception

    Public ivars:
        msg -- contains the message

    """
    def __init__(self, msg):
        self.msg = msg
    def __repr__(self):
        return repr(self.msg)
    def __str__(self):
        return str(self.msg)

class XDRError(Error):
    pass

class ConversionError(Error):
    pass

def assert_int(x):
    try:
        val = long(x)
    except:
        badinput = repr(x)
        if len(badinput) > 10:
            badinput = badinput[0:10] + "..."
        raise XDRError("Expected int, got %s %s" % (badinput, type(x)))
    return val

def assert_long(x):
    try:
        val = long(x)
    except:
        badinput = repr(x)
        if len(badinput) > 10:
            badinput = badinput[0:10] + "..."
        raise XDRError("Expected long, got %s %s" % (badinput, type(x)))
    return val

def assert_float(x):
    try:
        val = float(x)
    except:
        badinput = repr(x)
        if len(badinput) > 10:
            badinput = badinput[0:10] + "..."
        raise XDRError("Expected float, got %s %s" % (badinput, type(x)))
    return val

def assert_double(x):
    try:
        val = float(x)
    except:
        badinput = repr(x)
        if len(badinput) > 10:
            badinput = badinput[0:10] + "..."
        raise XDRError("Expected double, got %s %s" % (badinput, type(x)))
    return val

def assert_list(x):
    try:
        val = list(x)
    except:
        badinput = repr(x)
        if len(badinput) > 10:
            badinput = badinput[0:10] + "..."
        raise XDRError("Expected list, got %s %s" % (badinput, type(x)))
    return val

def assert_string(x):
    try:
        val = str(x)
    except:
        badinput = repr(x)
        if len(badinput) > 10:
            badinput = badinput[0:10] + "..."
        raise XDRError("Expected string, got %s %s" % (badinput, type(x)))
    return val

def assert_bytes(x):
    try:
        val = bytes(x)
    except:
        badinput = repr(x)
        if len(badinput) > 10:
            badinput = badinput[0:10] + "..."
        raise XDRError("Expected bytes, got %s %s" % (badinput, type(x)))
    return val



class Packer:
    """Pack various data representations into a buffer."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.__buf = _StringIO()

    def get_buffer(self):
        return self.__buf.getvalue()
    # backwards compatibility
    get_buf = get_buffer

    def pack_uint(self, x):
        val = assert_int(x)
        try:
            self.__buf.write(struct.pack('>L', val))
        except OverflowError: #hack to get around problem with 0xFFFFFFFF being interpreted as -1L
            self.__buf.write(struct.pack('>l', val))

    pack_int = pack_uint
    pack_enum = pack_int

    def pack_bool(self, x):
        try:
            val = assert_int(x)
        except XDRError as msg:
            raise XDRError("pack_bool " + repr(msg))
        if val:
            self.__buf.write(b'\0\0\0\1')
        else:
            self.__buf.write(b'\0\0\0\0')

    def pack_uhyper(self, x):
        try:
            val = assert_long(x)
        except XDRError as msg:
            raise XDRError("pack_uhyper " + str(msg.msg))
        self.__buf.write(struct.pack('>Q', val))

    pack_hyper = pack_uhyper

    def pack_float(self, x):
        try:
            val = assert_float(x)
        except XDRError as msg:
            raise XDRError("pack_float " + str(msg))
        self.__buf.write(struct.pack('>f', val))

    def pack_double(self, x):
        try:
            val = assert_double(x)
        except XDRError as msg:
            raise XDRError("pack_double " + str(msg))
        self.__buf.write(struct.pack('>d', x))

    def pack_fopaque(self, n, s):
        try:
            n = assert_int(n)
        except XDRError as msg:
            raise XDRError("pack_fopaque " + str(msg))
        try:
            s = assert_bytes(s)
        except XDRError as msg:
            raise XDRErrorr("pack_fopaque " + str(msg))
        if n < 0:
            raise XDRError('pack_fopaque size must be nonnegative')
        n = ((n + 3 ) // 4) * 4
        data = s[:n]
        data = data + b''.join([b'\0' for x in range(n - len(data))])
        self.__buf.write(data)

    def pack_fstring(self, n, s):
        try:
            s = assert_string(s)
            s = s.encode(str_encoding)
        except XDRError as msg:
            raise XDRError("pack_fstring " + str(msg))
        self.pack_fopaque(n, s)

    def pack_bytes(self, s):
        try:
            s = assert_bytes(s)
        except XDRError as msg:
            raise XDRError("pack_bytes " + str(msg))
        n = len(s)
        try:
            self.pack_uint(n)
        except XDRError as msg:
            raise XDRError("pack_bytes " + str(msg))
        try:
            self.pack_fopaque(n, s)
        except XDRError as msg:
            raise XDRError("pack_bytes " + str(msg))

    def pack_string(self, s):
        try:
            s = assert_string(s)
            s = s.encode(str_encoding)
        except XDRError as msg:
            raise XDRError("pack_string " + str(msg))
        self.pack_bytes(s)

    pack_opaque = pack_bytes

    def pack_list(self, list, pack_item):
        list = assert_list(list)
        for item in list:
            self.pack_uint(1)
            pack_item(item)
        self.pack_uint(0)

    def pack_farray(self, n, list, pack_item):
        n = assert_int(n)
        list = assert_list(list)
        if len(list) != n:
            raise XDRError('wrong array size')
        for item in list:
            pack_item(item)

    def pack_array(self, list, pack_item):
        list = assert_list(list)
        n = len(list)
        self.pack_uint(n)
        self.pack_farray(n, list, pack_item)

    def pack_void(self):
        pass

class Unpacker:
    """Unpacks various data representations from the given buffer."""

    def __init__(self, data):
        self.reset(data)

    def reset(self, data):
        if isinstance(data, str) and not isinstance(data, bytes):
            raise ValueError("Data type should be bytes not str: '%s'" % data)
        self.__buf = data
        self.__pos = 0

    def get_position(self):
        return self.__pos

    def set_position(self, position):
        self.__pos = position

    def get_buffer(self):
        return self.__buf

    def done(self):
        if self.__pos < len(self.__buf):
            raise XDRError('unextracted data remains')

    def unpack_uint(self):
        i = self.__pos
        self.__pos = j = i+4
        data = self.__buf[i:j]
        if len(data) < 4:
            raise XDRError("Data len (%d) less than needed (4)." % len(data))
        x = struct.unpack('>L', data)[0]
        try:
            return int(x)
        except OverflowError:
            return x

    def unpack_int(self):
        i = self.__pos
        self.__pos = j = i+4
        data = self.__buf[i:j]
        if len(data) < 4:
            raise XDRError("Data len (%d) less than needed (4)." % len(data))
        return struct.unpack('>l', data)[0]

    unpack_enum = unpack_int
    unpack_bool = unpack_int

    def unpack_void(self):
        return None

    def unpack_uhyper(self):
        i = self.__pos
        self.__pos = j = i+8
        data = self.__buf[i:j]
        if len(data) < 8:
            raise XDRError("Data len (%d) less than needed (8)." % len(data))
        try:
            ret = struct.unpack(">Q", data)[0]
        except Exception as excep:
            raise XDRError("Caught: %s, data = %s." % (excep, repr(data)))

        return ret

    def unpack_hyper(self):
        x = self.unpack_uhyper()
        if x >= 0x8000000000000000:
            x = x - 0x10000000000000000
        return x

    def unpack_float(self):
        i = self.__pos
        self.__pos = j = i+4
        data = self.__buf[i:j]
        if len(data) < 4:
            raise XDRError("Data len (%d) less than needed (4)." % len(data))
        return struct.unpack('>f', data)[0]

    def unpack_double(self):
        i = self.__pos
        self.__pos = j = i+8
        data = self.__buf[i:j]
        if len(data) < 8:
            raise XDRError("Caught end of file, %d characters remaining." % len(data))
            raise XDRError("Data len (%d) less than needed (8)." % len(data))
        return struct.unpack('>d', data)[0]

    def unpack_fopaque(self, n):
        if n < 0:
            raise XDRError('size must be nonnegative')
        i = self.__pos
        j = i + (n + 3) // 4 * 4
        pad_len = 0
        if j > len(self.__buf):
            pad_len = j - len(self.__buf)
            # raise XDRError, "Packet len (%d) less than needed (%d)." % (len(self.__buf),j)
        self.__pos = j
        data = (self.__buf + (b'\x00' * pad_len))[i:i+n]
        return data

    def unpack_fstring(self, n):
        data = self.unpack_fopaque(n)
        data = data.decode(str_encoding)
        return data

    def unpack_string(self):
        try:
            n = self.unpack_uint()
        except XDRError as msg:
            raise XDRError("unpack_string: unpacking integer" + str(msg))
        data = self.unpack_fstring(n)
        return data

    def unpack_bytes(self):
        try:
            n = self.unpack_uint()
        except XDRError as msg:
            raise XDRError("unpack_string: unpacking integer" + str(msg))
        return self.unpack_fopaque(n)

    unpack_opaque = unpack_bytes

    def unpack_list(self, unpack_item):
        list = []
        while 1:
            try:
                x = self.unpack_uint()
            except XDRError as msg:
                raise XDRError("unpack_list: " + str(msg))
            if x == 0: break
            if x != 1:
                    raise XDRError("0 or 1 expected, got %s %s" % ( repr(x), type(x) ))
            try:
                item = unpack_item()
            except XDRError as msg:
                raise XDRError("unpack_list: " + str(msg))
            list.append(item)
        return list

    def unpack_farray(self, n, unpack_item):
        list = []
        for i in range(n):
            list.append(unpack_item())
        return list

    def unpack_array(self, unpack_item):
        n = self.unpack_uint()
        return self.unpack_farray(n, unpack_item)


# test suite
def _test():
    p = Packer()
    packtest = [
        (p.pack_uint,    (9,)),
        (p.pack_bool,    (None,)),
        (p.pack_bool,    ('hello',)),
        (p.pack_uhyper,  (45,)),
        (p.pack_float,   (1.9,)),
        (p.pack_double,  (1.9,)),
        (p.pack_string,  ('hello world',)),
        (p.pack_list,    (list(range(5)), p.pack_uint)),
        (p.pack_array,   (['what', 'is', 'hapnin', 'doctor'], p.pack_string)),
        ]
    succeedlist = [1] * len(packtest)
    count = 0
    for method, args in packtest:
        print('pack test', count, end=' ')
        try:
            method(*args)
            print('succeeded')
        except ConversionError as var:
            print('ConversionError:', var.msg)
            succeedlist[count] = 0
        except XDRError as var:
            print('Error: ', str(var))
            succeedlist[count] = 0
        count = count + 1
    data = p.get_buffer()
    # now verify
    up = Unpacker(data)
    unpacktest = [
        (up.unpack_uint,   (), lambda x: x == 9),
        (up.unpack_bool,   (), lambda x: not x),
        (up.unpack_bool,   (), lambda x: x),
        (up.unpack_uhyper, (), lambda x: x == 45),
        (up.unpack_float,  (), lambda x: 1.89 < x < 1.91),
        (up.unpack_double, (), lambda x: 1.89 < x < 1.91),
        (up.unpack_string, (), lambda x: x == 'hello world'),
        (up.unpack_list,   (up.unpack_uint,), lambda x: x == list(range(5))),
        (up.unpack_array,  (up.unpack_string,),
         lambda x: x == ['what', 'is', 'hapnin', 'doctor']),
        ]
    count = 0
    for method, args, pred in unpacktest:
        print('unpack test', count, end=' ')
        try:
            if succeedlist[count]:
                x = method(*args)
                print(pred(x) and 'succeeded' or 'failed', ':', x)
            else:
                print('skipping')
        except ConversionError as var:
            print('ConversionError:', var.msg)
        except XDRError as msg:
            print('Error:', str(var))
        count = count + 1

import unittest

class UnpackerTestCase(unittest.TestCase):
    def testUnpack_fstring(self):
        ''' Test the modified unpack_fstring() method
        to make sure that it can handle the packet
        length less than specified length in the
        xdr file.
         '''
        up = Unpacker('01234\x00\x00\x00')
        s = up.unpack_fstring(6)
        self.assertEqual('01234\x00', s)

        up = Unpacker('01234\x00\x00\x00')
        s = up.unpack_fstring(10)
        self.assertEqual('01234\x00\x00\x00\x00\x00', s)


if __name__ == '__main__':
    _test()
    unittest.main()

import os

import six
from cffi import FFI

from ssdeep.__about__ import (
    __author__, __copyright__, __email__, __license__, __summary__, __title__,
    __uri__, __version__
)

ffi = FFI()

ffi.cdef(
    """
    static const long FUZZY_FLAG_ELIMSEQ;
    static const long FUZZY_FLAG_NOTRUNC;
    static const long FUZZY_MAX_RESULT;

    struct fuzzy_state;
    struct fuzzy_state *fuzzy_new(void);
    int fuzzy_update(
        struct fuzzy_state *,
        const unsigned char *,
        size_t
    );

    int fuzzy_digest(
        const struct fuzzy_state *,
        char *,
        unsigned int
    );
    void fuzzy_free(struct fuzzy_state *);

    int fuzzy_hash_buf(
        const unsigned char *,
        uint32_t,
        char *
    );

    int fuzzy_hash_file(
        FILE *,
        char *
    );

    int fuzzy_hash_stream(
        FILE *,
        char *
    );

    int fuzzy_hash_filename(
        const char *,
        char *
    );

    int fuzzy_compare(
        const char *,
        const char *
    );
    """
)

_lib = ffi.verify(
    """
    #include "fuzzy.h"
    """,
    ext_package="ssdeep",
    libraries=["fuzzy"],
)


class BaseError(Exception):
    pass

class Error(Exception):
    def __init__(self, errno=None):
        self.errno = errno

    def __str__(self):
        return "Error: %s" % os.strerror(self.errno)

    def __repr__(self):
        try:
            return "Error(errno.%s)" % errno.errorcode[self.errno]
        except KeyError:
            return "Error(%d)" % self.errno


class Hash(object):
    def __init__(self):
        self._state = _lib.fuzzy_new()
#        if self.state == NULL:
#            raise Error(libc.errno.errno)

    def update(self, buf):
        buf = buf.encode("utf-8")

#        if self._state == N:
#           raise Error(libc.errno.EINVAL)
        if _lib.fuzzy_update(self._state, buf, len(buf)) != 0:
            _lib.fuzzy_free(self._state)
            self._state = None
            # raise Error(libc.errno.errno)

    def digest(self, elimseq=False, notrunc=False):
        # if self.state == NULL:
        #    raise Error(libc.errno.EINVAL)

        flags = (_lib.FUZZY_FLAG_ELIMSEQ if elimseq else 0) | \
                (_lib.FUZZY_FLAG_NOTRUNC if notrunc else 0)

        result = ffi.new("char[]", _lib.FUZZY_MAX_RESULT)
        if _lib.fuzzy_digest(self._state, result, flags) != 0:
            # raise Error(libc.errno.errno)
            pass

        return ffi.string(result).decode("utf-8")

    def __del__(self):
        if self._state is not None:
            _lib.fuzzy_free(self._state)


def compare(sig1, sig2):
    return _lib.fuzzy_compare(sig1.encode("utf-8"), sig2.encode("utf-8"))


def hash(buf):
    buf = buf.encode("utf-8")
    result = ffi.new("char[]", _lib.FUZZY_MAX_RESULT)
    _lib.fuzzy_hash_buf(buf, len(buf), result)
    return ffi.string(result).decode("utf-8")


def hash_from_file(filename):
    if not os.path.exists(filename):
        raise IOError("Path not found")
    if not os.path.isfile(filename):
        raise IOError("File not found")
    if not os.access(filename, os.R_OK):
        raise IOError("File is not readable")

    result = ffi.new("char[]", _lib.FUZZY_MAX_RESULT)
    if _lib.fuzzy_hash_filename(filename.encode("utf-8"), result) != 0:
        raise BaseError()

    return ffi.string(result).decode("utf-8")

"""
    Package is wrapper for the libshr C library implemented using CFFI
"""
from __future__ import print_function
import math
import signal
import sys

from __about__ import (__author__, __email__, __libshr_version__, __license__,
                       __summary__, __title__, __uri__, __version__)
from _pyshr import ffi, lib

__all__ = [
    "__title__", "__summary__", "__uri__", "__version__", "__author__",
    "__email__", "__license__", "__libshr_version__", 'ShareException',
    'SQMode', 'SQEvent', 'SharedQueue'
]



class ShareException(Exception):
    pass


class ShareError():
    text = [
        "success",
        "retry",
        "no items on queue",
        "depth limit reached",
        "invalid argument",
        "not enough memory to satisfy request",
        "permission error",
        "existence error",
        "invalid state",
        "problem with path name",
        "required operation not supported",
        "system error"
    ]


class SHStatus():
    SH_OK = 0                  # success
    SH_RETRY = 1               # retry previous
    SH_ERR_EMPTY = 2           # no items available
    SH_ERR_LIMIT = 3           # depth limit reached
    SH_ERR_ARG = 4             # invalid argument
    SH_ERR_NOMEM = 5           # not enough memory to satisfy request
    SH_ERR_ACCESS = 6          # permission error
    SH_ERR_EXIST = 7           # existence error
    SH_ERR_STATE = 8           # invalid state
    SH_ERR_PATH = 9            # problem with path name
    SH_ERR_NOSUPPORT = 10      # required operation not supported
    SH_ERR_SYS = 11            # system error
    SH_ERR_CONFLICT = 12       # update conflict
    SH_ERR_NO_MATCH = 13       # no match found for key
    SH_ERR_MAX = 14

    @staticmethod
    def is_valid(status):
        if status is None:
            return False
        if not isinstance(status, int):
            return False
        if status >= SHStatus.SH_OK and status < SHStatus.SH_ERR_MAX:
            return True
        return False


class SQMode():
    IMMUTABLE = 0
    READ_ONLY = 1
    WRITE_ONLY = 2
    READWRITE = 3

    @staticmethod
    def is_valid(mode):
        if mode is None:
            return False
        if not isinstance(mode, int):
            return False
        if mode >= SQMode.IMMUTABLE and mode <= SQMode.READWRITE:
            return True
        return False


class SQEvent():
    ALL = 0         # not an event, used to simplify subscription
    NONE = 0        # non-event
    INIT = 1        # first item added to queue
    LIMIT = 2       # queue limit reached
    TIME = 3        # max time limit reached
    LEVEL = 4       # depth level reached
    EMPTY = 5       # last item on queue removed
    NONEMPTY = 6    # item added to empty queue

    @staticmethod
    def is_valid(event):
        if event is None:
            return False
        if not isinstance(event, int):
            return False
        if event >= SQEvent.NONE and event <= SQEvent.NONEMPTY:
            return True
        return False


class SHType():
    VECTOR_T = 0            # vector of multiple types
    STRM_T = 1              # unspecified byte stream
    INTEGER_T = 2           # integer data type determined by length
    FLOAT_T = 3             # floating point type determined by length
    ASCII_T = 4             # ascii string (char values 0-127)
    UTF8_T = 5              # utf-8 string
    UTF16_T = 6             # utf-16 string
    JSON_T = 7              # json string
    XML_T = 8               # xml string
    STRUCT_T = 9            # binary struct

    @staticmethod
    def is_valid(sqtype):
        if sqtype is None:
            return False
        if not isinstance(sqtype, int):
            return False
        if sqtype >= SHType.VECTOR_T and sqtype <= SHType.STRUCT_T:
            return True
        return False


class SharedQueue:

    @staticmethod
    def is_valid(name):
        ''' checks that name matches an existing = 1 valid queue '''
        if name is None or not isinstance(name, str):
            raise ShareException('is_valid', ShareError.text[lib.SH_ERR_ARG])
        return lib.shr_q_is_valid(name)

    def __init__(self, name, mode, size=0):
        ''' constructor for queue object
            name - string name of queue
            mode - SQMode instance for access
            size - max size if creating new queue, 0 defaults to system max
        '''
        if not SQMode.is_valid(mode):
            raise ShareException('constructor',
                                 ShareError.text[lib.SH_ERR_ARG],
                                 mode)
        if name is None or not (isinstance(name, str) or isinstance(name, unicode)):
            raise ShareException('constructor',
                                 ShareError.text[lib.SH_ERR_ARG],
                                 name)
        if not isinstance(size, int):
            raise ShareException('constructor',
                                 ShareError.text[lib.SH_ERR_ARG],
                                 size)

        name = name.encode()
        self.pq = ffi.new("shr_q_s *[1]")
        if lib.shr_q_is_valid(name) and size == 0:
            status = lib.shr_q_open(self.pq, name, mode)
            if status:
                raise ShareException('open', ShareError.text[status])
        else:
            status = lib.shr_q_create(self.pq, name, size, mode)
            if status:
                raise ShareException('create', ShareError.text[status])
        self.buff = ffi.new("void *[1]")
        self.buff_sz = ffi.new('size_t *')
        self.buff[0] = ffi.NULL
        self.buff_sz[0] = 0

    def destroy(self):
        ''' destroy queue
        '''
        if self.pq[0] == ffi.NULL:
            raise ShareException('destroy', ShareError.text[lib.SH_ERR_ARG])
        status = lib.shr_q_destroy(self.pq)
        if status:
            raise ShareException(ShareError.text[status])
        if self.buff[0]:
            lib.free(self.buff[0])

    def close(self):
        ''' close queue instance, preserves queue
        '''
        if self.pq[0] == ffi.NULL:
            raise ShareException('close', ShareError.text[lib.SH_ERR_ARG])
        status = lib.shr_q_close(self.pq)
        if status:
            raise ShareException(ShareError.text[status])
        if self.buff[0]:
            lib.free(self.buff[0])

    def add(self, data):
        ''' add data stream to queue
        '''
        if not isinstance(data, bytes) and not isinstance(data, str) and \
            not isinstance(data, unicode):
            raise ShareException('add', 'incompatible data type', data)
        data = data.encode()
        status = lib.shr_q_add(self.pq[0], data, len(data))
        if status:
            raise ShareException('add', ShareError.text[status])

    def add_wait(self, data):
        ''' add data stream to queue, block if full
        '''
        if not isinstance(data, bytes) and not isinstance(data, str) and \
            not isinstance(data, unicode):
            raise ShareException('add_wait', 'incompatible data type', data)
        data = data.encode()
        status = lib.shr_q_add_wait(self.pq[0], data, len(data))
        if status:
            raise ShareException('add_wait', ShareError.text[status])

    def add_timedwait(self, data, time):
        '''
        add data stream to queue, block for time if full
        data - string or bytes to put on queue
        time - float of time to wait
        '''
        if not isinstance(data, bytes) and not isinstance(data, str) and \
            not isinstance(data, unicode):
            raise ShareException('add_wait', 'incompatible data type', data)
        data = data.encode()
        ts = ffi.new('struct timespec *')
        split = math.modf(time)
        ts.tv_sec = int(split[1])
        ts.tv_nsec = int(split[0] * 1000000000)
        status = lib.shr_q_add_timedwait(self.pq[0], data, len(data), ts)
        if status:
            raise ShareException('add_timedwait', ShareError.text[status])

    def __to_vector(self, items, vector, vcnt, buffers):
        for i in xrange(vcnt):
            d_type = type(items[i])
            data = items[i]
            if d_type == tuple:
                d_type = items[i][0]
                if not SHType.is_valid(d_type) or len(items[i]) != 2:
                    raise ShareException('__to_vector',
                                         ShareError.text[lib.SH_ERR_ARG], items[i])
                data = items[i][1]

            if d_type == int or (d_type == SHType.INTEGER_T and isinstance(data, int)):
                vector[i].type = lib.SH_INTEGER_T
                vector[i].len = 4
                buffers.append(ffi.new("int *", data))
                vector[i].base = buffers[i]
            elif d_type == long or (d_type == SHType.INTEGER_T and isinstance(data, long)):
                vector[i].type = lib.SH_INTEGER_T
                vector[i].len = 8
                buffers.append(ffi.new("long long *", data))
                vector[i].base = buffers[i]
            elif d_type == float or d_type == SHType.FLOAT_T:
                vector[i].type = lib.SH_FLOAT_T
                vector[i].len = 8
                buffers.append(ffi.new("double *", data))
                vector[i].base = buffers[i]
            elif d_type == str or d_type == SHType.ASCII_T:
                vector[i].type = lib.SH_ASCII_T
                vector[i].len = len(data)
                buffers.append(ffi.new('char[]', data))
                vector[i].base = buffers[i]
            elif d_type == SHType.XML_T:
                if isinstance(data, unicode):
                    data = data.encode()
                vector[i].type = lib.SH_XML_T
                vector[i].len = len(data)
                buffers.append(ffi.new('char[]', data))
                vector[i].base = buffers[i]
            elif d_type == unicode or d_type == SHType.UTF8_T:
                vector[i].type = lib.SH_UTF8_T
                data = data.encode()
                vector[i].len = len(data)
                buffers.append(ffi.new('char[]', data))
                vector[i].base = buffers[i]
            elif d_type == SHType.JSON_T:
                vector[i].type = lib.SH_JSON_T
                data = data.encode()
                vector[i].len = len(data)
                buffers.append(ffi.new('char[]', data))
                vector[i].base = buffers[i]
            elif d_type == bytes or d_type == SHType.STRM_T:
                vector[i].type = lib.SH_STRM_T
                vector[i].len = len(data)
                buffers.append(ffi.new('char[]', data))
                vector[i].base = buffers[i]
            elif '__len__' in dir(data):
                vector[i].type = lib.SH_STRM_T
                vector[i].len = len(data)
                buffers.append(ffi.new('char[]', data))
                vector[i].base = buffers[i]
            else:
                raise ShareException('__to_vector', ShareError.text[lib.SH_ERR_ARG],
                                     data)

    def addv(self, items):
        ''' add list to queue
        '''
        if not isinstance(items, (list, tuple)):
            raise ShareException('add', 'incompatible data type', items)
        vcnt = len(items)
        vector = ffi.new('sq_vec_s[]', vcnt)
        buffers = []
        self.__to_vector(items, vector, vcnt, buffers)
        status = lib.shr_q_addv(self.pq[0], vector, vcnt)
        if status:
            raise ShareException('add', ShareError.text[status])

    def addv_wait(self, items):
        ''' add arbitrary data to queue, block if full
        '''
        if not isinstance(items, (list, tuple)):
            raise ShareException('add', 'incompatible data type', items)
        vcnt = len(items)
        vector = ffi.new('sq_vec_s[]', vcnt)
        buffers = []
        self.__to_vector(items, vector, vcnt, buffers)
        status = lib.shr_q_addv_wait(self.pq[0], vector, vcnt)
        if status:
            raise ShareException('add_wait', ShareError.text[status])

    def addv_timedwait(self, items, time):
        ''' add arbitrary data to queue, block for time if full
            items - list of items to put on queue
            time - float of time to wait
        '''
        if not isinstance(items, (list, tuple)):
            raise ShareException('add', 'incompatible data type', items)
        ts = ffi.new('struct timespec *')
        split = math.modf(time)
        ts.tv_sec = int(split[1])
        ts.tv_nsec = int(split[0] * 1000000000)
        vcnt = len(items)
        vector = ffi.new('sq_vec_s[]', vcnt)
        buffers = []
        self.__to_vector(items, vector, vcnt, buffers)
        status = lib.shr_q_addv_timedwait(self.pq[0], vector, vcnt, ts)
        if status:
            raise ShareException('add_timedwait', ShareError.text[status])

    def __to_list(self, item):
        #import pdb; pdb.set_trace()
        result = []
        for i in xrange(item.vcount):
            d_type = item.vector[i].type
            d_base = item.vector[i].base
            d_len = item.vector[i].len
            if d_type == lib.SH_INTEGER_T:
                if d_len == 4:
                    result.append(int(ffi.cast('int *', d_base)[0]))
                else:
                    result.append(long(ffi.cast('long *', d_base)[0]))
            elif d_type == lib.SH_FLOAT_T:
                if d_len == 8:
                    result.append(float(ffi.cast('double *', d_base)[0]))
                else:
                    raise ShareException('__to_list', 'incompatible float type')
            elif d_type == lib.SH_ASCII_T:
                result.append(str(ffi.buffer(d_base, d_len)))
            elif d_type == lib.SH_STRM_T:
                result.append(bytes(ffi.buffer(d_base, d_len)))
            elif d_type == lib.SH_XML_T:
                result.append((d_type, bytes(ffi.buffer(d_base, d_len))))
            elif d_type == lib.SH_UTF8_T:
                result.append(unicode(ffi.buffer(d_base, d_len), 'utf-8'))
            elif d_type == lib.SH_JSON_T:
                result.append((d_type, unicode(ffi.buffer(d_base, d_len), 'utf-8')))
            elif d_type == lib.SH_UTF16_T:
                result.append(unicode(ffi.buffer(d_base, d_len), 'utf-16'))
            else:
                raise ShareException('__to_list', 'incompatible data type')
        return result

    def remove(self):
        ''' remove item from queue without blocking
        '''
        item = ffi.new('sq_item_s *')
        item = lib.shr_q_remove(self.pq[0], self.buff, self.buff_sz)
        if item.status == lib.SH_ERR_EMPTY:
            return []
        if item.status:
            raise ShareException('remove', ShareError.text[item.status])
        return self.__to_list(item)

    def remove_wait(self):
        ''' remove item from queue, block if empty
        '''
        item = ffi.new('sq_item_s *')
        item = lib.shr_q_remove_wait(self.pq[0], self.buff, self.buff_sz)
        if item.status == lib.SH_ERR_EMPTY:
            return []
        if item.status:
            raise ShareException('remove_wait', ShareError.text[item.status])
        return self.__to_list(item)

    def remove_timedwait(self, time):
        ''' remove item from queue, block for time if empty
            time - float of time to wait
        '''
        item = ffi.new('sq_item_s *')
        ts = ffi.new('struct timespec *')
        ts.tv_sec = math.trunc(time)
        ts.tv_nsec = int(math.modf(time)[0] * 1000000000)
        item = lib.shr_q_remove_timedwait(self.pq[0], self.buff, self.buff_sz, ts)
        if item.status == lib.SH_ERR_EMPTY:
            return []
        if item.status:
            raise ShareException('remove_timedwait',
                                 ShareError.text[item.status])
        return self.__to_list(item)

    def monitor(self, signo):
        ''' registers as monitoring process using specified signal
        '''
        if signo is None or not isinstance(signo, int):
            raise ShareException('monitor', ShareError.text[lib.SH_ERR_ARG])
        status = lib.shr_q_monitor(self.pq[0], signo)
        if status:
            raise ShareException('monitor', ShareError.text[status])

    def listen(self, signo):
        ''' registers as listening process for arrivals using specified signal
        '''
        if signo is None or not isinstance(signo, int):
            raise ShareException('monitor', ShareError.text[lib.SH_ERR_ARG])
        status = lib.shr_q_listen(self.pq[0], signo)
        if status:
            raise ShareException('monitor', ShareError.text[status])

    def call(self, signo):
        ''' registers as called process for blocked removes using specified signal
        '''
        if signo is None or not isinstance(signo, int):
            raise ShareException('monitor', ShareError.text[lib.SH_ERR_ARG])
        status = lib.shr_q_call(self.pq[0], signo)
        if status:
            raise ShareException('monitor', ShareError.text[status])

    def event(self):
        ''' return active event
        '''
        return int(lib.shr_q_event(self.pq[0]))

    def exceeds_idle_time(self, time):
        ''' tests to see if no item has been added within the specified time
        '''
        ts = ffi.new('struct timespec *')
        ts.tv_sec = math.trunc(time)
        ts.tv_nsec = int(math.modf(time)[0] * 1000000000)
        return lib.shr_q_exceeds_idle_time(self.pq[0], ts)

    def count(self):
        ''' count of items on queue
        '''
        return int(lib.shr_q_count(self.pq[0]))

    def level(self, depth):
        ''' sets value for queue depth level event generation and for adaptive LIFO
        '''
        if depth is None or not isinstance(depth, int):
            raise ShareException('level', ShareError.text[lib.SH_ERR_ARG])
        status = lib.shr_q_level(self.pq[0], depth)
        if status:
            raise ShareException('level', ShareError.text[status])

    def timelimit(self, time):
        ''' sets time limit of item on queue before producing a max time limit event
        '''
        ts = ffi.new('struct timespec *')
        ts.tv_sec = math.trunc(time)
        ts.tv_nsec = int(math.modf(time)[0] * 1000000000)
        status = lib.shr_q_timelimit(self.pq[0], ts)
        if status:
            raise ShareException('timelimit', ShareError.text[status])

    def clean(self, time):
        ''' remove items from front of queue that have exceeded timelimit
        '''
        ts = ffi.new('struct timespec *')
        ts.tv_sec = math.trunc(time)
        ts.tv_nsec = int(math.modf(time)[0] * 1000000000)
        status = lib.shr_q_clean(self.pq[0], ts)
        if status:
            raise ShareException('clean', ShareError.text[status])

    def last_empty(self):
        ''' returns timestamp of last time queue became non-empty
        '''
        ts = ffi.new('struct timespec *')
        ts.tv_sec = 0
        ts.tv_nsec = 0
        status = lib.shr_q_last_empty(self.pq[0], ts)
        if status:
            raise ShareException('last_empty', ShareError.text[status])
        return (ts.tv_sec, ts.tv_nsec)

    def discard(self, flag):
        ''' discard items that exceed expiration time limit
        '''
        if flag is None or not isinstance(flag, bool):
            raise ShareException('discard', ShareError.text[lib.SH_ERR_ARG])
        status = lib.shr_q_discard(self.pq[0], flag)
        if status:
            raise ShareException('discard', ShareError.text[status])

    def will_discard(self):
        ''' tests to see if queue will discard expired items
        '''
        return lib.shr_q_will_discard(self.pq[0])

    def limit_lifo(self, flag):
        ''' treat depth limit as limit for adaptive LIFO behavior
        '''
        if flag is None or not isinstance(flag, bool):
            raise ShareException('limit_lifo', ShareError.text[lib.SH_ERR_ARG])

        status = lib.shr_q_limit_lifo(self.pq[0], flag)
        if status:
            raise ShareException('limit_lifo', ShareError.text[status])

    def will_lifo(self):
        ''' tests to see if queue will used adaptive LIFO
        '''
        return lib.shr_q_will_lifo(self.pq[0])

    def subscribe(self, event):
        ''' subscribe to see specified event
        '''
        if not SQEvent.is_valid(event):
            raise ShareException('subscribe', ShareError.text[lib.SH_ERR_ARG])

        status = lib.shr_q_subscribe(self.pq[0], event)
        if status:
            raise ShareException('subscribe', ShareError.text[status])

    def unsubscribe(self, event):
        ''' remove subscription for specified event
        '''
        if not SQEvent.is_valid(event):
            raise ShareException('unsubscribe', ShareError.text[lib.SH_ERR_ARG])
        status = lib.shr_q_subscribe(self.pq[0], event)
        if status:
            raise ShareException('unsubscribe', ShareError.text[status])

    def is_subscribed(self, event):
        ''' returns true if event subscribed, otherwise false
        '''
        if not SQEvent.is_valid(event):
            raise ShareException('is_subscribed',
                                 ShareError.text[lib.SH_ERR_ARG])
        return lib.shr_q_is_subscribed(self.pq[0], event)

    def prod(self):
        ''' activates at least one blocked caller
        '''
        status = lib.shr_q_prod(self.pq[0])
        if status:
            raise ShareException('prod', ShareError.text[status])

    def call_count(self):
        ''' count of blocked remove calls
        '''
        return int(lib.shr_q_call_count(self.pq[0]))

    def target_delay(self, time):
        ''' sets target delay and activates CoDel algorithm
        '''
        ts = ffi.new('struct timespec *')
        ts.tv_sec = math.trunc(time)
        ts.tv_nsec = int(math.modf(time)[0] * 1000000000)
        status = lib.shr_q_target_delay(self.pq[0], ts)
        if status:
            raise ShareException('target_delay', ShareError.text[status])

if __name__ == '__main__':
    try:
        if not SharedQueue.is_valid('testq'):
            print("queue doesn't exist")
        q = SharedQueue('testq', SQMode.READWRITE)
        print("queue count ", q.count())
        #import pdb; pdb.set_trace()
        q.addv([(SHType.INTEGER_T, 4), (SHType.JSON_T, u'{"test":"value"}'), (SHType.XML_T, '<doc/>')])
        q.addv(((SHType.INTEGER_T, 4), (SHType.JSON_T, u'{"test":"value"}'), (SHType.XML_T, '<doc/>')))
        q.addv_wait([(SHType.INTEGER_T, 4), (SHType.JSON_T, u'{"test":"value"}'), (SHType.XML_T, '<doc/>')])
        q.addv_timedwait([(SHType.INTEGER_T, 4), (SHType.JSON_T, u'{"test":"value"}'), (SHType.XML_T, '<doc/>')], 0.01)
        q.add_wait("add wait test data")
        q.add_timedwait("add timedwait test data", 0.01)
        print("queue count ", q.count())
        item = q.remove()
        print(item)
        item = q.remove_wait()
        print(item)
        item = q.remove_timedwait(0.01)
        print(item)
        print("queue count ", q.count())
        q.destroy()
    except ShareException as exc:
        print('queue ops failed:  ', exc)

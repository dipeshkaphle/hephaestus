# pylint: disable=protected-access,dangerous-default-value
import ctypes
import inspect
import sys
import threading
import time

from src.ir.visitors import DefaultVisitorUpdate


class TimeoutError(Exception):
    pass


# https://stackoverflow.com/questions/323972/is-there-any-way-to-kill-a-thread
def _async_raise(tid, exctype):
    """raises the exception, exctype, in the thread with id tid"""
    if not inspect.isclass(exctype):
        raise TypeError("Only types can be raised (not instances)")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # "if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), 0)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def timeout_function(log, entity, timeouted, thread_to_kill):
    log("{}: took too long (timeout)".format(entity))
    sys.stderr.flush()  # Python 3 stderr is likely buffered.
    timeouted[0] = True
    _async_raise(thread_to_kill.ident, TimeoutError)


def visitor_logging_and_timeout_with_args(*args):
    def wrap_visitor_func(visitor_func):
        def wrapped_visitor(self, node):
            if len(args) > 0:
                self.log(*args)
            transformation_name = self.__class__.__name__
            visitor_name = visitor_func.__name__
            entity = transformation_name + "-" + visitor_name
            self.log("{}: Begin".format(entity))

            timeouted = [False]
            start = time.time()
            new_node = node
            main_thread = threading.current_thread()
            timer = threading.Timer(
                self.timeout, timeout_function,
                args=[self.log, entity, timeouted, main_thread])
            try:
                timer.start()
                new_node = visitor_func(self, node)
            except TimeoutError:
                self.log(f"{entity}: Timed out!")
                # new_node is already node
            finally:
                timer.cancel()
            end = time.time()
            if timeouted[0]:
                new_node = node
            self.log("{}: {} elapsed time".format(entity, str(end - start)))
            self.log("{}: End".format(entity))
            return new_node

        return wrapped_visitor

    return wrap_visitor_func


def change_namespace(visit):
    def inner(self, node):
        initial_namespace = self._namespace
        self._namespace += (node.name,)
        new_node = visit(self, node)
        self._namespace = initial_namespace
        return new_node

    return inner


def change_depth(visit):
    def inner(self, node):
        initial_depth = self.depth
        self.depth += 1
        new_node = visit(self, node)
        self.depth = initial_depth
        return new_node

    return inner


class Transformation(DefaultVisitorUpdate):
    CORRECTNESS_PRESERVING = None

    def __init__(self, program, language, logger=None, options={}):
        assert program is not None, 'The given program must not be None'
        self.is_transformed = False
        self.language = language
        self.program = program
        self.types = self.program.get_types()
        self.logger = logger
        self.options = options
        self.timeout = options.get("timeout", 600)
        if self.logger:
            self.logger.log_info()

    def transform(self):
        self.program = self.visit(self.program)

    def result(self):
        return self.program

    def log(self, msg):
        if self.logger is None:
            pass
        else:
            self.logger.log(msg)

    @classmethod
    def get_name(cls):
        return cls.__name__

    @classmethod
    def preserve_correctness(cls):
        return cls.CORRECTNESS_PRESERVING

    @visitor_logging_and_timeout_with_args()
    def visit_program(self, node):
        return super().visit_program(node)

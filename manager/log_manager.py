from enum import IntEnum
from datetime import datetime

class LogLevel(IntEnum):
    TRACE = 1
    DEBUG = 2
    INFO = 3
    WARN = 4
    ERROR = 5
    FATAL = 6

class LogType(IntEnum):
    BUILD = 1
    DEBUG = 2

class Logger:
    def __init__(self, log_type: LogType):
        self.log_type = log_type
        self.log_stack = []
        
    def log_trace(self, log_msg):
        if self.log_type >= 2:
            now = datetime.now()
            msg = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}][{LogLevel.TRACE.name}]{log_msg}"
            self.log_stack.append(msg)
    
    def log_debug(self, log_msg):
        if self.log_type >= 2:
            now = datetime.now()
            msg = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}][{LogLevel.DEBUG.name}]{log_msg}"
            self.log_stack.append(msg)
            
    def log_info(self, log_msg):
        now = datetime.now()
        msg = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}][{LogLevel.INFO.name}]{log_msg}"
        self.log_stack.append(msg)
        
    def log_warn(self, log_msg):
        now = datetime.now()
        msg = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}][{LogLevel.WARN.name}]{log_msg}"
        self.log_stack.append(msg)
        
    def log_error(self, log_msg):
        now = datetime.now()
        msg = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}][{LogLevel.ERROR.name}]{log_msg}"
        self.log_stack.append(msg)
        
    def log_fatal(self, log_msg):
        now = datetime.now()
        msg = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}][{LogLevel.FATAL.name}]{log_msg}"
        self.log_stack.append(msg)
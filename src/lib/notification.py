import os
import inspect
import logging

logging.basicConfig(
    filename="photo-tools.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)
class Notification:
    def __init__(self, logger_name=__name__):
        self.color_red = "\033[91m"
        self.color_green = "\033[92m"
        self.color_yellow = "\033[93m"
        self.color_reset = "\033[0m"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(console_handler)

    @staticmethod
    def _caller_filename_lineno(skip=2):
        """Return (basename(filename), lineno) for the frame `skip` steps above.

        Default `skip=2` returns the caller of the caller (useful when called
        from a small helper inside a class method).
        """
        frame = inspect.currentframe()
        try:
            for _ in range(skip):
                if frame is None:
                    return ("<unknown>", 0)
                frame = frame.f_back
            if frame is None:
                return ("<unknown>", 0)
            info = inspect.getframeinfo(frame)
            filename = os.path.basename(info.filename) if info.filename else "<unknown>"
            lineno = frame.f_lineno
            return filename, lineno
        finally:
            # break reference cycles
            try:
                del frame
            except Exception:
                pass

    def __error__(self, error_message, filename=None, lineno=None):
        ''' Handle database errors '''
        classname = self.__class__.__name__
        if filename is None or lineno is None:
            filename, line_number = Notification._caller_filename_lineno()
        else:
            line_number = lineno
        self.logger.error(f"{self.color_red}ERROR {classname} (\"{filename}\", line {line_number}):{self.color_reset} {error_message}")

    def __info__(self, info_message):
        ''' Handle database info messages '''
        classname = self.__class__.__name__
        filename, line_number = self._caller_filename_lineno()
        self.logger.info(f"{self.color_yellow}INFO {classname} ({filename}, line {line_number}):{self.color_reset} {info_message}")

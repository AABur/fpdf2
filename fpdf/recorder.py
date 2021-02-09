from copy import deepcopy

from .errors import FPDFException


class FPDFRecorder:
    """
    The class is aimed to be used as wrapper around fpdf.FPDF:

        pdf = FPDF()
        recorder = FPDFRecorder(pdf)

    Its aim is dual:
      * allow to **rewind** to the state of the FPDF instance passed to its constructor,
        reverting all changes made to its internal state
      * allow to **replay** again all the methods calls performed
        on the recorder instance between its creation and the last call to rewind()

    Note that using this class means to duplicate the FPDF `bytearray` buffer:
    when generating large PDFs, doubling memory usage may be troublesome.
    """

    def __init__(self, pdf, accept_page_break=True):
        self._pdf = pdf
        self._initial = deepcopy(pdf.__dict__)
        self._calls = []
        if not accept_page_break:
            self.accept_page_break = False

    def __getattr__(self, name):
        attr = getattr(self._pdf, name)
        if callable(attr):
            return CallRecorder(attr, self._calls)
        return attr

    def rewind(self):
        self._pdf.__dict__ = self._initial

    def replay(self):
        for call in self._calls:
            func, args, kwargs = call
            try:
                func(*args, **kwargs)
            except Exception as error:
                raise FPDFException(
                    f"Failed to replay FPDF call: {func}(*{args}, **{kwargs})"
                ) from error
        self._calls = []


class CallRecorder:
    def __init__(self, func, calls):
        self._func = func
        self._calls = calls

    def __call__(self, *args, **kwargs):
        self._calls.append((self._func, args, kwargs))
        return self._func(*args, **kwargs)

class OfbError(Exception):
    pass


class OfbNoDeviceError(OfbError):
    pass


class OfbPackageChecksumError(OfbError):
    pass


class OfbNotSupportedError(OfbError):
    pass


class OfbDriverError(OfbError):
    pass


class FbNotReadyError(OfbDriverError):
    pass


class FbMissingHandlerError(OfbDriverError):
    pass


class FbStartupError(OfbDriverError):
    pass


class OfbServerDeadError(OfbError):
    pass


class OfbAlreadyRunningError(OfbError):
    pass


class OfbSystemError(OfbError):
    pass

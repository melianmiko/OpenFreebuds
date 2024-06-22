class FbNoDeviceError(Exception):
    pass


class FbNotSupportedError(Exception):
    pass


class FbDriverError(Exception):
    pass


class FbNotReadyError(FbDriverError):
    pass


class FbMissingHandlerError(FbDriverError):
    pass


class FbStartupError(FbDriverError):
    pass

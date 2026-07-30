class OSFVError(Exception):
    """
    Base class for errors this library raises for a bad configuration or a
    device that will not do what was asked.

    Callers that drive a device, the CLI and the Robot library, catch this to
    report the problem rather than letting a traceback reach the user. A bug in
    the library itself still raises a plain exception and surfaces as one.
    """

    pass

"""
A module containing different exceptions related to the traj subpackage.
"""

from multimethod import multimethod

from PQAnalysis.exceptions import PQException, BaseEnumFormatError


class TrajectoryFormatError(BaseEnumFormatError):
    """
    Exception raised if the given enum is not valid
    """

    pass


class MDEngineFormatError(BaseEnumFormatError):
    """
    Exception raised if the given enum is not valid
    """

    pass


class FrameError(PQException):
    """
    Exception raised for errors related to the Frame class
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class TrajectoryError(PQException):
    """
    Exception raised for errors related to the Trajectory class
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)

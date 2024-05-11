"""
A module containing different format types of the trajectory.
"""

from beartype.typing import Any

from PQAnalysis.formats import BaseEnumFormat
from .exceptions import TrajectoryFormatError, MDEngineFormatError



class TrajectoryFormat(BaseEnumFormat):

    """
    An enumeration of the supported trajectory formats.
    """

    #: inference of the trajectory format from the file extension
    AUTO = "auto"

    #: The xyz trajectory format.
    XYZ = "XYZ"

    #: The vel trajectory format.
    VEL = "VEL"

    #: The force trajectory format.
    FORCE = "FORCE"

    #: The charge trajectory format.
    CHARGE = "CHARGE"

    @classmethod
    def _missing_(cls, values: Any) -> Any:  # pylint: disable=arguments-differ
        """
        This method returns the missing value of the enumeration.

        Parameters
        ----------
        values : Tuple[Any | str] | Any
            The value to be converted to the enumeration or 
            a tuple containing the value and the filename.

        Returns
        -------
        Any
            The value to return.
        """

        if isinstance(values, tuple):
            value = values[0]
            filename = values[1]
        else:
            value = values
            filename = None

        traj_format = super()._missing_(value, TrajectoryFormatError)

        if traj_format == cls.AUTO and filename is None:
            raise TrajectoryFormatError(
                "The trajectory format could not be inferred from the file extension."
            )

        if traj_format == cls.AUTO:
            return cls.infer_format_from_extension(filename)

        return traj_format

    @classmethod
    def infer_format_from_extension(cls, file_path: str) -> "TrajectoryFormat":
        """
        Infer the trajectory format from the file extension.

        Parameters
        ----------
        file_path : str
            The file path to infer the trajectory format from.

        Returns
        -------
        TrajectoryFormat
            The inferred trajectory format.
        """
        if file_path.endswith(".xyz"):
            return cls.XYZ

        if (file_path.endswith(".vel") or file_path.endswith(".velocs")):
            return cls.VEL

        if (file_path.endswith(".force") or file_path.endswith(".forces")
                or file_path.endswith(".frc")):
            return cls.FORCE

        if (file_path.endswith(".charge") or file_path.endswith(".chrg")):
            return cls.CHARGE

        raise TrajectoryFormatError(
            "Could not infer the trajectory format from the file "
            f"extension of the file {file_path}."
        )

    def lower(self) -> str:
        """
        This method returns the lower case representation of the enumeration.

        Returns
        -------
        str
            The lower case representation of the enumeration.
        """

        return self.value.lower()



class MDEngineFormat(BaseEnumFormat):

    """
    An enumeration of the supported MD engine formats.
    """

    PQ = "PQ"
    QMCFC = "QMCFC"

    @classmethod
    def _missing_(cls, value: Any) -> Any:  # pylint: disable=arguments-differ
        """
        This method returns the missing value of the enumeration.

        Parameters
        ----------
        value : Any
            The value to return.

        Returns
        -------
        Any
            The value to return.
        """

        return super()._missing_(value, MDEngineFormatError)

    @classmethod
    def is_qmcfc_type(cls, engine_format: Any) -> bool:
        """
        This method checks if the given format is a QMCF format.

        Parameters
        ----------
        engine_format : Any
            The format to check.

        Returns
        -------
        bool
            True if the format is a QMCF format, False otherwise.
        """
        return engine_format in [cls.PQ, cls.QMCFC]

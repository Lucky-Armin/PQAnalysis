"""
A module containing different functions to read and write .gen files.
"""

from .genFileReader import GenFileReader
from .genFileWriter import GenFileWriter
from PQAnalysis.atomicSystem import AtomicSystem
from PQAnalysis.io.formats import FileWritingMode


def read_gen_file(filename: str) -> AtomicSystem:
    """
    Function to read a gen file.

    Parameters
    ----------
    filename : str
        The filename of the gen file.

    Returns
    -------
    AtomicSystem
        The AtomicSystem including the Cell object.
    """

    return GenFileReader(filename).read()


def write_gen_file(filename: str,
                   system: AtomicSystem,
                   periodic: bool | None = None,
                   mode: FileWritingMode | str = "w"
                   ) -> None:
    """
    Function to write a gen file.

    Parameters
    ----------
    filename : str
        The filename of the gen file.
    system : AtomicSystem
        The system to write.
    periodic : bool, optional
        The periodicity of the system. If True, the system is considered periodic. If False, the system is considered non-periodic. If None, the periodicity is inferred from the system, by default None.
    mode : FileWritingMode | str, optional
        The writing mode, by default "w". The following modes are available:
        - "w": write
        - "a": append
        - "o": overwrite
    """

    GenFileWriter(filename, mode=mode).write(system, periodic)

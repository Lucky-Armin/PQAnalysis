"""
A module containing classes for reading a trajectory from a file.
"""

from __future__ import annotations

# 3rd party modules
import logging
import os
from beartype.typing import List, Generator
from tqdm.auto import tqdm

# Local absolute imports
from PQAnalysis.config import with_progress_bar
from PQAnalysis.atomic_system import AtomicSystem
from PQAnalysis.traj import Trajectory, TrajectoryFormat, MDEngineFormat
from PQAnalysis.core import Cell
from PQAnalysis.topology import Topology
from PQAnalysis.io.base import BaseReader
from PQAnalysis.utils.custom_logging import setup_logger
from PQAnalysis import __package_name__

# Local relative modules
from .exceptions import TrajectoryReaderError
from .frame_reader import FrameReader


class TrajectoryReader(BaseReader):
    """
    A class for reading a trajectory from a file.

    Inherited from BaseReader.
    """

    # Set up the logger
    logger = logging.getLogger(__package_name__).getChild(__qualname__)

    def __init__(
        self,
        filename: str | List[str],
        traj_format: TrajectoryFormat | str = TrajectoryFormat.AUTO,
        md_format: MDEngineFormat | str = MDEngineFormat.PQ,
        topology: Topology | None = None,
        constant_topology: bool = True,
    ) -> None:
        """
        Parameters
        ----------
        filename : str or list of str
            The name of the file to read from or a list of filenames to read from.
        traj_format : TrajectoryFormat | str, optional
            The format of the trajectory. Default is TrajectoryFormat.AUTO.
            The format is inferred from the file extension.
        md_format : MDEngineFormat | str, optional
            The format of the trajectory. Default is MDEngineFormat.PQ.
        topology : Topology, optional
            The topology of the trajectory. Default is None.
        constant_topology : bool, optional
            Whether the topology is constant over the trajectory or does change. Default is True.
        """
        super().__init__(filename)

        # Set up the logger
        self.logger = setup_logger(self.logger)

        if not self.multiple_files:
            self.filenames = [self.filename]

        self.file = None

        self.frames = []
        self.topology = topology
        self.constant_topology = constant_topology

        self.traj_format = TrajectoryFormat((traj_format, self.filenames[0]))

        self.md_format = MDEngineFormat(md_format)
        self.frame_reader = FrameReader(md_format=self.md_format)

        # Calculate the number of frames in the trajectory
        self.length_of_traj = self.calculate_number_of_frames()

        # NOTE: Progress bar is disabled by default
        #       This way the frame_generator can be used in other functions
        #       without the need to disable the progress bar
        #       The global config.with_progress_bar is only set in the read function
        self.with_progress_bar = False

    def read(self, topology: Topology | None = None) -> Trajectory:
        """
        Reads the trajectory from the file.

        It reads the trajectory from the file and concatenates the lines of the
        same frame. The frame information is then read from the concatenated
        string with the FrameReader class and a Frame object is created.

        In order to read the cell information given in the file, the cell
        information of the last frame is used for all following frames that
        do not have cell information.

        If the trajectory is split into multiple files, the files are read one
        after another and the frames are concatenated into a single trajectory.

        Parameters
        ----------
        topology : Topology, optional
            The topology of the trajectory. Default is None.

        Returns
        -------
        Trajectory
            The trajectory read from the file.
        """

        self.with_progress_bar = with_progress_bar
        self.topology = topology

        traj = Trajectory()
        for frame in self.frame_generator():
            traj.append(frame)

        return traj

    def frame_generator(
        self,
        trajectory_start: int = 0,
        trajectory_stop: int | None = None,
    ) -> Generator[AtomicSystem]:
        """
        A generator that yields the frames of the trajectory.

        The difference to the read method is that the read method returns the whole
        trajectory at once, while the frame_generator yields the frames one after
        another. This is useful if the trajectory is very large and cannot be stored
        in memory.

        This method is used to read the trajectory from the file. It reads the
        trajectory from the file and concatenates the lines of the same frame.
        The frame information is then read from the concatenated string with the
        FrameReader class and a Frame object is created.

        Parameters
        ----------
        trajectory_start : int, optional
            The start index of the trajectory, by default 0.
        trajectory_stop : int | None, optional
            The last index of the trajectory, by default None, which then
            set to the length of the trajectory.

        Exceptions
        ----------
        IndexError
            If trajectory_start is less than 0 or greater than the length
            of the trajectory.
            If trajectory_stop is less than 0 or greater than the length
            of the trajectory.

        Yields
        ------
        Generator[AtomicSystem]
            The frames of the trajectory.
        """

        if trajectory_stop is None:
            trajectory_stop = self.length_of_traj

        # If trajectory_start is less than 0 or greater than the
        # length of the trajectory, raise an IndexError
        if trajectory_start < 0 or trajectory_start > self.length_of_traj:
            self.logger.error(
                "start index is less than 0 or greater than the length of the trajectory",
                exception=IndexError,
            )

        # If trajectory_stop is less than 0 or greater than the
        # length of the trajectory, raise an IndexError
        if trajectory_stop < 0 or trajectory_stop > self.length_of_traj:
            self.logger.error(
                "stop index is less than 0 or greater than the length of the trajectory",
                exception=IndexError,
            )

        # If trajectory_start is greater than or equal to trajectory_stop,
        # raise an IndexError
        if trajectory_start >= trajectory_stop:
            self.logger.error(
                "start index is greater than or equal to the stop index",
                exception=IndexError,
            )

        # Track the number of frames that have been yielded
        frame_index = 0

        last_cell = None

        for filename in self.filenames:

            # Read the number of lines in the file
            with open(filename, "r", encoding="utf-8") as self.file:
                sum_lines = sum(1 for _ in self.file)

            # Read the file again to get the frames
            with open(filename, "r", encoding="utf-8") as self.file:
                frame_lines = []

                # Read the lines of the file using tqdm for progress bar
                for line in tqdm(
                    self.file, total=sum_lines, disable=not self.with_progress_bar
                ):
                    stripped_line = line.strip()
                    if stripped_line == "" or not stripped_line[0].isdigit():
                        frame_lines.append(line)
                    else:
                        if frame_lines:
                            frame = self._read_single_frame(
                                "".join(frame_lines), self.topology
                            )
                            if frame.cell.is_vacuum and last_cell is not None:
                                frame.cell = last_cell
                            last_cell = frame.cell


                            # TODO: Implement the trajectory_start and trajectory_stop more efficiently
                            # Check if the number of frames yielded is equal to the total number of frames
                            if not (
                                frame_index < trajectory_start
                                or frame_index >= trajectory_stop
                            ):
                                yield frame # only yield the frame if it is within the range

                            # then increment the frame index
                            frame_index += 1

                            if self.constant_topology and self.topology is not None:
                                self.topology = frame.topology

                        frame_lines = [line]

                if frame_lines:
                    frame = self._read_single_frame("".join(frame_lines), self.topology)

                    if frame.cell.is_vacuum and last_cell is not None:
                        frame.cell = last_cell

                    last_cell = frame.cell

                    # TODO: Implement the trajectory_start and trajectory_stop more efficiently
                    # Check if the number of frames yielded is equal to the total number of frames
                    if not (
                        frame_index < trajectory_start
                        or frame_index >= trajectory_stop
                    ):
                        yield frame # only yield the frame if it is within the range

                    # then increment the frame index
                    frame_index += 1

                if self.constant_topology and self.topology is not None:
                    self.topology = frame.topology

    def window_generator(
        self,
        window_size: int,
        window_gap: int = 1,
        trajectory_start: int = 0,
        trajectory_stop: int | None = None,
    ) -> Generator[Trajectory]:
        """
        A generator that yields the windows of the trajectory using the specified
        window size and gap. The windows are generated by sliding a window of the
        specified size over the trajectory with the specified gap. It uses the
        frame_generator method to read the frames of the trajectory.

        Parameters
        ----------
        window_size : int
            The size of the window.
        window_gap : int, optional
            The gap size between two windows, by default 1
        trajectory_start : int, optional
            The start index of the first window, by default 0
        trajectory_stop : int | None, optional
            Stop index of the window generator, by default None, which then
            set to the length of the trajectory.

        Raises
        ------
        IndexError
            If window_size is less than 1 or greater than the length of
            the trajectory.
            If window_gap is less than 1 or greater than the length of
            the trajectory.
            If window_size is greater than trajectory_stop - trajectory_start.

        Warning
        -------
        If not all frames are included in the windows, a warning is issued.

        Yields
        ------
        Generator[Trajectory]
            An generator over the windows of the trajectory with the specified
            window size and gap.
        """

        # If trajectory_stop is not provided, set it to the length of the trajectory
        if trajectory_stop is None:
            trajectory_stop = self.length_of_traj

        # If trajectory_start is less than 0 or greater than the
        # length of the trajectory, raise an IndexError
        if trajectory_start < 0 or trajectory_start > self.length_of_traj:
            self.logger.error(
                "start index is less than 0 or greater than the length of the trajectory",
                exception=IndexError,
            )

        # If trajectory_stop is less than 0 or greater than the
        # length of the trajectory, raise an IndexError
        if trajectory_stop < 0 or trajectory_stop > self.length_of_traj:
            self.logger.error(
                "stop index is less than 0 or greater than the length of the trajectory",
                exception=IndexError,
            )

        # If trajectory_start is greater than or equal to trajectory_stop,
        # raise an IndexError
        if trajectory_start >= trajectory_stop:
            self.logger.error(
                "start index is greater than or equal to the stop index",
                exception=IndexError,
            )

        # If window_step is less than 1 or greater than
        # the length of the trajectory, raise an IndexError
        if window_size < 1 or window_size > self.length_of_traj:
            self.logger.error(
                "window size can not be less than 1 or greater than the length of the trajectory",
                exception=IndexError,
            )

        # If window_gap is less than 1 or greater than
        # the length of the trajectory, raise an IndexError
        if window_gap < 1 or window_gap > self.length_of_traj:
            self.logger.error(
                "window gap can not be less than 1 or greater than the length of the trajectory",
                exception=IndexError,
            )

        # If window_size is greater than trajectory_stop - trajectory_start, raise an IndexError
        if window_size > trajectory_stop - trajectory_start:
            self.logger.error(
                "window size is greater than the trajectory_stop - trajectory_start",
                exception=IndexError,
            )

        # Check if all frames are included in the windows
        # Length of the trajectory - window_size should be divisible by window_gap
        if ((trajectory_stop - trajectory_start) - window_size) % window_gap != 0:
            self.logger.warning(
                "Not all frames are included in the windows. Check the window size and gap."
            )

        generator = self.frame_generator(trajectory_start=trajectory_start, trajectory_stop=trajectory_stop)

        # reads first window and converts it to a queue
        window = Trajectory([next(generator) for _ in range(window_size)])

        # yield the first window
        yield window.copy()

        # generate the rest of the windows up to trajectory_stop
        for _ in range(
            trajectory_start + window_gap, trajectory_stop - window_size + 1, window_gap
        ):

            # pop the first frame and append the next frame for window_gap times to
            # get the next window
            for _ in range(window_gap):
                window.pop(0)
                window.append(next(generator))

            # yield the next window
            yield window.copy()

    def calculate_number_of_frames(self) -> int:
        """
        Calculates the number of frames in the trajectory file.

        Returns
        -------
        int
            The number of frames in the trajectory file.
        """

        n_frames = 0

        for filename in self.filenames:
            
            # TODO: Add check to BaseReader to check if the file is empty            
            if os.path.getsize(filename) == 0:
                continue

            with open(filename, "r", encoding="utf-8") as f:

                # Read the lines
                lines = f.readlines()

            # +2 for the cell and atom count lines
            n_frames += int(len(lines) / (int(lines[0].split()[0]) + 2))

        return n_frames

    @property
    def cells(self) -> list[Cell]:
        """
        Returns the cells of the trajectory.

        Returns
        -------
        list of Cell
            The list of cells of the trajectory.
        """
        return list(self._cell_generator())

    def _cell_generator(self) -> Generator[List[Cell]]:
        """
        A generator that yields the cells of the trajectory.

        This method is used to read the cells from the file.
        It reads the cells from the file and yields them one after
        another. If the cell information is not given in the
        file, the cell information of the last frame is used
        for all following frames that do not have cell information.

        Yields
        ------
        list of Cell
            The list of cells read from the trajectory.
        """
        last_cell = None
        with open(self.filenames[0], "r", encoding="utf-8") as f:
            line = f.readline()
            n_atoms = int(line.split()[0])

        for filename in self.filenames:
            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    stripped_line = line.strip()
                    splitted_line = stripped_line.split()

                    if len(splitted_line) == 1 and cell is None:
                        cell = Cell()

                        if last_cell is not None:
                            cell = last_cell

                        yield cell

                    elif len(splitted_line) == 4:

                        cell = Cell(
                            float(splitted_line[1]),
                            float(splitted_line[2]),
                            float(splitted_line[3]),
                        )

                        yield cell

                    elif len(splitted_line) == 7:

                        cell = Cell(
                            float(splitted_line[1]),
                            float(splitted_line[2]),
                            float(splitted_line[3]),
                            float(splitted_line[4]),
                            float(splitted_line[5]),
                            float(splitted_line[6]),
                        )

                        yield cell

                    else:

                        raise TrajectoryReaderError(
                            "Invalid number of arguments for box: "
                            f"{len(splitted_line)} encountered in file "
                            f"{filename} {stripped_line}."
                        )

                    last_cell = cell

                    for _ in range(n_atoms + 1):
                        next(f, None)  # Skip the next n_atoms+1 lines

    def _read_single_frame(
        self, frame_string: str, topology: Topology | None = None
    ) -> AtomicSystem:
        """
        Reads a single frame from the given string.

        Parameters
        ----------
        frame_string : str
            The string containing the frame information.
        topology : Topology, optional
            The topology of the frame. Default is None.

        Returns
        -------
        AtomicSystem
            The AtomicSystem object of the frame.

        Raises
        ------
        TrajectoryReaderError
            If the first atom in the frame is not X for QMCFC.
        """
        return self.frame_reader.read(
            frame_string, traj_format=self.traj_format, topology=topology
        )

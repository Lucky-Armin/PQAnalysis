import numpy as np
import logging
import sys

from beartype.typing import List, Dict
from unum.units import eV, angstrom

from PQAnalysis.io import (
    BaseWriter,
    FileWritingMode,
    OutputFileFormat,
    read_trajectory_generator,
    EnergyFileReader
)
from PQAnalysis.io.virial.api import read_stress_file, read_virial_file
from PQAnalysis.utils.units import kcal_per_mole
from PQAnalysis.utils.files import find_files_with_prefix
from PQAnalysis.utils.custom_logging import setup_logger
from PQAnalysis.atomicSystem import AtomicSystem
from PQAnalysis.traj import Trajectory, TrajectoryFormat
from PQAnalysis import config
from PQAnalysis import __package_name__


class NEPWriter(BaseWriter):
    """
    A class to write NEP training and testing files.
    """

    logger = logging.getLogger(__package_name__).getChild(__qualname__)

    def __init__(self,
                 filename: str | None,
                 mode: FileWritingMode | str = "w",
                 ) -> None:
        """
        Parameters
        ----------
        filename : str
            _description_
        mode : FileWritingMode | str, optional
            _description_, by default "w"
        """
        super().__init__(filename, mode)

        self.logger = setup_logger(self.logger)

    def write_from_files(self,
                         file_prefixes: List[str] | str,
                         use_forces: bool = False,
                         use_stress: bool = False,
                         use_virial: bool = False,
                         xyz_file_extension: str = None,
                         energy_file_extension: str = None,
                         info_file_extension: str = None,
                         force_file_extension: str = None,
                         stress_file_extension: str = None,
                         virial_file_extension: str = None,
                         ) -> None:
        """
        Writes the NEP trajectory file from the given files.

        Parameters
        ----------
        file_prefixes : List[str] | str
            The prefixes of the files to find. Here with prefix we mean the part of the filename not only the name before the extension, but every matching file that starts with the given prefix.
        use_forces : bool, optional
            Whether to include forces in the output file, by default False
        use_stress : bool, optional
            Whether to include the stress tensor in the output file, by default False
        use_virial : bool, optional
            Whether to include the virial in the output file, by default False
        xyz_file_extension : str, optional
            The extension of the xyz files, by default None. This means that the respective file extension will be automatically determined from all files with the given file prefixes.
        energy_file_extension : str, optional
            The extension of the energy files, by default None. This means that the respective file extension will be automatically determined from all files with the given file prefixes.
        info_file_extension : str, optional
            The extension of the info files, by default None. This means that the respective file extension will be automatically determined from all files with the given file prefixes.
        force_file_extension : str, optional
            The extension of the force files, by default None. This means that the respective file extension will be automatically determined from all files with the given file prefixes.
        stress_file_extension : str, optional
            The extension of the stress files, by default None. This means that the respective file extension will be automatically determined from all files with the given file prefixes.
        virial_file_extension : str, optional
            The extension of the virial files, by default None. This means that the respective file extension will be automatically determined from all files with the given file prefixes.
        """

        self.use_forces = use_forces
        self.use_stress = use_stress
        self.use_virial = use_virial

        self.xyz_file_extension = xyz_file_extension
        self.energy_file_extension = energy_file_extension
        self.info_file_extension = info_file_extension
        self.force_file_extension = force_file_extension
        self.stress_file_extension = stress_file_extension
        self.virial_file_extension = virial_file_extension

        files = find_files_with_prefix(file_prefixes)

        file_dict = self.determine_files(
            files,
            file_prefixes,
        )

        #fmt: off
        xyz_files = file_dict[OutputFileFormat.XYZ.value]
        en_files = file_dict[OutputFileFormat.ENERGY.value]
        info_files = file_dict[OutputFileFormat.INFO.value]
        force_files = file_dict[OutputFileFormat.FORCE.value] if use_forces else []
        stress_files = file_dict[OutputFileFormat.STRESS.value] if use_stress else []
        virial_files = file_dict[OutputFileFormat.VIRIAL.value] if use_virial else []
        #fmt: on

        self.open()

        for i in range(len(xyz_files)):

            # read stress file in format step stress_xx stress_yy stress_zz stress_xy stress_xz stress_yz as n numpy 2D 3x3 arrays
            stress = read_stress_file(stress_files[i]) if use_stress else None
            virial = read_virial_file(virial_files[i]) if use_virial else None
            energy = EnergyFileReader(en_files[i], info_files[i]).read()

            xyz_generator = read_trajectory_generator(
                xyz_files[i], traj_format=TrajectoryFormat.XYZ)
            force_generator = read_trajectory_generator(
                force_files[i], traj_format=TrajectoryFormat.FORCE) if use_forces else None

            for j, system in enumerate(xyz_generator):
                system.energy = energy.qm_energy[j]

                if use_forces:
                    force_system = next(force_generator)
                    system.forces = force_system.forces

                if use_virial:
                    system.virial = virial[j]
                if use_stress:
                    system.stress = stress[j]

                self.write_from_atomic_system(
                    system,
                    use_forces,
                    use_stress,
                    use_virial
                )

            self.logger.info(f"""
Processed {len(stress)} frames from files:
{xyz_files[i]}, {en_files[i]}, {info_files[i]}, {force_files[i] if use_forces else None}, {
                stress_files[i] if use_stress else None}, {virial_files[i] if use_virial else None}
""")

        self.close()

    def determine_files(self,
                        files: List[str],
                        file_prefixes: List[str],
                        ) -> Dict[str, List[str]]:

        file_dict = {}

        file_dict[OutputFileFormat.XYZ.value] = self._get_files(
            files,
            OutputFileFormat.XYZ,
            self.xyz_file_extension,
            file_prefixes
        )

        file_dict[OutputFileFormat.ENERGY.value] = self._get_files(
            files,
            OutputFileFormat.INSTANTANEOUS_ENERGY,
            self.energy_file_extension,
            file_prefixes
        )

        file_dict[OutputFileFormat.INFO.value] = self._get_files(
            files,
            OutputFileFormat.INFO,
            self.info_file_extension,
            file_prefixes
        )

        if self.use_forces:
            file_dict[OutputFileFormat.FORCE.value] = self._get_files(
                files,
                OutputFileFormat.FORCE,
                self.force_file_extension,
                file_prefixes
            )

        if self.use_stress:
            file_dict[OutputFileFormat.STRESS.value] = self._get_files(
                files,
                OutputFileFormat.STRESS,
                self.stress_file_extension,
                file_prefixes
            )

        if self.use_virial:
            file_dict[OutputFileFormat.VIRIAL.value] = self._get_files(
                files,
                OutputFileFormat.VIRIAL,
                self.virial_file_extension,
                file_prefixes
            )

        def raise_number_of_files_error(file_type: str, files: List[str], xyz_files: List[str]):
            self.logger.error(
                f"The number of {file_type} files does not match the number of coordinate files. The found {
                    file_type} files are: {files} and the found coordinate files are: {xyz_files}"
            )
            exit(1)

        #fmt: off
        en_files = file_dict[OutputFileFormat.ENERGY.value]
        xyz_files = file_dict[OutputFileFormat.XYZ.value]
        info_files = file_dict[OutputFileFormat.INFO.value]
        force_files = file_dict[OutputFileFormat.FORCE.value] if self.use_forces else []
        stress_files = file_dict[OutputFileFormat.STRESS.value] if self.use_stress else []
        virial_files = file_dict[OutputFileFormat.VIRIAL.value] if self.use_virial else []
        #fmt: on

        if len(en_files) != len(xyz_files):
            raise_number_of_files_error("energy", en_files, xyz_files)

        if len(info_files) != len(xyz_files):
            raise_number_of_files_error("info", info_files, xyz_files)

        if self.use_forces and len(force_files) != len(xyz_files):
            raise_number_of_files_error("force", force_files, xyz_files)

        if self.use_stress and len(stress_files) != len(xyz_files):
            raise_number_of_files_error("stress", stress_files, xyz_files)

        if self.use_virial and len(virial_files) != len(xyz_files):
            raise_number_of_files_error("virial", virial_files, xyz_files)

        self.logger.info(f"""
Reading files to write NEP trajectory file:
    - xyz_files:    {xyz_files}
    - en_files:     {en_files}
    - info_files:   {info_files}
    - force_files:  {force_files if self.use_forces else ""}
    - stress_files: {stress_files if self.use_stress else ""}
    - virial_files: {virial_files if self.use_virial else ""}
""")

        return file_dict

    def _get_files(self,
                   files: List[str],
                   OutputFileFormat: OutputFileFormat,
                   file_extension: str | None,
                   file_prefixes: List[str],
                   ) -> List[str]:

        filtered_files = OutputFileFormat.find_matching_files(
            files,
            OutputFileFormat,
            file_extension
        )

        if len(filtered_files) == 0:
            if file_extension is not None:
                raise ValueError(
                    f"You did specify a file extension for the {OutputFileFormat} files, but no files with the extension \
                    {file_extension} were found, that match the given file prefixes {file_prefixes}."
                )
            else:
                raise ValueError(
                    f"No {OutputFileFormat} files were found in {files} that match the given file prefixes {file_prefixes}. All possible file      extensions are {OutputFileFormat.get_file_extensions(
                        OutputFileFormat)}. If the specific file extension you are looking for is not in the list, please specify it using the corresponding file_extension argument. If the files should be found, please check the file paths and the file prefixes. Additionally, if you think that the file extension you chose is of general interest and should be added to the list of possible file extensions, please file an issue at {config.code_base_url}issues."
                )

        return sorted(filtered_files)

    def write_from_trajectory(self,
                              trajectory: Trajectory,
                              use_forces: bool = False,
                              use_stress: bool = False,
                              use_virial: bool = False,
                              ) -> None:

        self.open()
        for frame in trajectory:
            self.write_from_atomic_system(
                frame,
                use_forces,
                use_stress,
                use_virial
            )

        self.close()

    def write_from_atomic_system(self,
                                 system: AtomicSystem,
                                 use_forces: bool = False,
                                 use_stress: bool = False,
                                 use_virial: bool = False,
                                 ) -> None:

        if not system.has_pos:
            raise ValueError(
                "The system does not have coordinates, which are required for NEP trajectory files.")

        if not system.has_energy:
            raise ValueError(
                "The system does not have an energy, which is required for NEP trajectory files.")

        if use_forces and not system.has_forces:
            raise ValueError(
                "The system does not have forces, and they were specified to be written to the NEP trajectory file.")

        if use_stress and use_virial:
            raise ValueError(
                "Both the stress and the virial tensor were specified to be written to the NEP trajectory file. "
                "Only one of them can be written at a time.")

        if use_stress and not system.has_stress:
            raise ValueError(
                "The system does not have a stress tensor, and it was specified to be written to the NEP trajectory file.")

        if use_virial and not system.has_virial:
            raise ValueError(
                "The system does not have a virial tensor, and it was specified to be written to the NEP trajectory file.")

        self.write_header(system, use_forces, use_stress, use_virial)
        self.write_body(system, use_forces)

    def write_header(self,
                     system: AtomicSystem,
                     use_forces: bool = False,
                     use_stress: bool = False,
                     use_virial: bool = False,
                     ) -> None:

        box_matrix = np.transpose(system.cell.box_matrix)

        print(system.n_atoms, file=self.file)

        energy_unit = kcal_per_mole
        energy_conversion = energy_unit.asUnit(eV).asNumber()
        energy = system.energy * energy_conversion

        self.file.write(f"energy={energy} ")

        self.file.write("config_type=nep2xyz ")

        self.file.write("lattice=\"")
        for i in range(3):
            for j in range(3):
                self.file.write(f"{box_matrix[i][j]} ")
        self.file.write("\" ")

        if use_virial:
            virial_unit = kcal_per_mole
            virial_conversion = virial_unit.asUnit(eV).asNumber()
            virial = system.virial * virial_conversion

            self.file.write("virial=\"")
            for i in range(3):
                for j in range(3):
                    self.file.write(f"{virial[i][j]} ")
            self.file.write("\" ")

        if use_stress:
            stress_unit = kcal_per_mole / angstrom**3
            stress_conversion = stress_unit.asUnit(eV / angstrom**3).asNumber()
            stress = system.stress * stress_conversion

            self.file.write("stress=\"")
            for i in range(3):
                for j in range(3):
                    self.file.write(f"{stress[i][j]} ")
            self.file.write("\" ")

        self.file.write("properties=species:S:1:pos:R:3")
        if use_forces:
            self.file.write(":forces:R:3")
        self.file.write("\n")

    def write_body(self,
                   system: AtomicSystem,
                   use_forces: bool = False,
                   ) -> None:
        """
        Writes the body of the NEP trajectory file.

        Parameters
        ----------
        system: AtomicSystem
            The system to be written to the NEP trajectory file.
        use_forces: bool, optional
            Whether to write the forces to the NEP trajectory file, by default False
        """

        for i in range(system.n_atoms):
            atom = system.atoms[i]

            print(
                f"{atom.symbol:<4} {system.pos[i][0]:12.8f} {system.pos[i][1]:12.8f} {system.pos[i][2]:12.8f}", file=self.file, end=" "
            )

            force_unit = kcal_per_mole / angstrom
            force_conversion = force_unit.asUnit(eV / angstrom).asNumber()
            forces = system.forces * force_conversion

            if use_forces:
                print(
                    f"{forces[i][0]:15.8e} {forces[i][1]:15.8e} {forces[i][2]:15.8e}", file=self.file, end=" "
                )

            print(file=self.file)
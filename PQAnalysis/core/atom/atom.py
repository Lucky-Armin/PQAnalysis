"""
A module containing the Atom class and some associated functions.

The Atom class is used to represent an atom in a molecule. It contains the
following attributes:
    
        - name: the name of the atom (e.g. 'C')
        - element: the element of the atom (e.g. 'C')

The atomic number and mass are automatically determined from the name or symbol
of the atom. The name and symbol are automatically determined from the atomic
number. The name is the symbol in lower case.
"""

from __future__ import annotations

from beartype.typing import Any, NewType
from beartype.vale import Is
from typing import Annotated
from numbers import Real

from . import Element

#: A type hint for a list of atoms
Atoms = NewType("Atoms", Annotated[list, Is[lambda list: all(
    isinstance(atom, Atom) for atom in list)]])


class Atom():
    """
    A class used to represent an atom in a molecule.

    There are three ways to initialize an Atom object:

    1) By giving the name of the atom_type (e.g. 'C1')
       If use_guess_element is True (default), the atom_type name has to be
       a valid element symbol (e.g. 'C'). If use_guess_element is False, the
       atom_type name can be anything and an empty element is created.

    2) By giving the name of the atom_type (e.g. 'C1') and the id of the atom_type
       (e.g. 6). The id can be either an integer (atomic number) or a string (element symbol).

    3) By giving the id of the atom_type (e.g. 6). The id can be either an integer (atomic number) 
       or a string (element symbol).

    Examples
    --------
    >>> atom = Atom('C1') # use_guess_element is True by default - raises ElementNotFoundError if the element is not found

    >>> atom = Atom('C1', use_guess_element=False)
    >>> (atom.name, atom.element)
    ('C1', Element())

    >>> atom = Atom('C1', 'C')
    >>> (atom.name, atom.element)
    ('C1', Element('C'))

    >>> atom = Atom('C1', 6)
    >>> (atom.name, atom.element)
    ('C1', Element(6))

    >>> atom = Atom(6)
    >>> (atom.name, atom.element)
    ('c', Element(6))

    >>> atom = Atom('C')
    >>> (atom.name, atom.element)
    ('C', Element('C'))
    """

    def __init__(self, name: str | int, id: int | str | None = None, use_guess_element: bool = True) -> None:
        """
        Constructs all the necessary attributes for the Atom object.

        If use_guess_element is True, the symbol, atomic number and mass are
        determined from the name of the atom_type. If use_guess_element is
        False, the symbol, atomic number and mass are set to None, meaning that
        an empty element is created (Element()).

        Parameters
        ----------
        name : str | int
            The name of the atom_type (e.g. 'C1')
            If this parameter is an integer, it is interpreted as the atomic number of the element symbol and cannot 
            be used together with the id parameter.
        id : int | str, optional
            The atomic number or element symbol of the atom_type (e.g. 6 or 'C')
            If his parameter is not given, the name parameter is used to determine the element type of the atom_type.
        use_guess_element : bool, optional
            Whether to use the guess_element function to determine the element type of the atom_type 
            by its name, by default True
        """

        if id is not None and isinstance(name, int):

            raise ValueError(
                "The name of the atom_type cannot be an integer if the id is given.")

        elif id is not None and isinstance(name, str):

            self._name = name
            self._element = Element(id)

        elif isinstance(name, int):

            self._element = Element(name)
            self._name = self._element.symbol.lower()

        else:

            self._name = name
            if use_guess_element:
                self._element = Element(name)
            else:
                self._element = Element()

    def __eq__(self, other: Any) -> bool:
        """
        Checks whether the Atom is equal to another Atom.

        Parameters
        ----------
        other : Any
            The other Atom to compare to.

        Returns
        -------
        bool
            True if the Atom is equal to the other Atom, False otherwise.
        """
        if not isinstance(other, Atom):
            return False

        is_equal = True
        is_equal &= self.name.lower() == other.name.lower()
        is_equal &= self._element == other._element
        return is_equal

    def __str__(self) -> str:
        """
        Returns a string representation of the Atom.

        Returns
        -------
        str
            A string representation of the Atom.
        """
        return f"Atom({self.name}, {self.atomic_number}, {self.symbol}, {self.mass})"

    def __repr__(self) -> str:
        """
        Returns a representation of the Atom.

        Returns
        -------
        str
            A representation of the Atom.
        """
        return self.__str__()

    #######################
    #                     #
    # standard properties #
    #                     #
    #######################

    @property
    def name(self) -> str:
        """str: The name of the atom_type (e.g. 'C1')"""
        return self._name

    @property
    def symbol(self) -> str | None:
        """str: The symbol of the element (e.g. 'c')"""
        return self._element.symbol

    @property
    def atomic_number(self) -> int | None:
        """int | None: The atomic number of the element (e.g. 6)"""
        return self._element.atomic_number

    @property
    def mass(self) -> Real | None:
        """Real | None: The mass of the element (e.g. 12.011)"""
        return self._element.mass

    @property
    def element(self) -> Element:
        """Element: The element type of the atom"""
        return self._element

    @element.setter
    def element(self, element: Element) -> None:
        self._element = element

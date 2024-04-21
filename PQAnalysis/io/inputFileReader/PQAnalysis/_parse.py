"""
A module containing functions to parse the input file.
"""
from beartype.typing import List
from numbers import Real

from ..inputFileParser import InputDictionary
from ..exceptions import InputFileError
from PQAnalysis.types import PositiveReal, PositiveInt


def _parse_positive_real(dict: InputDictionary, key: str) -> PositiveReal | None:
    """
    Gets the value of a key from the input dictionary and checks if it is a positive real number.
    If the key is not in the dictionary, None is returned.

    Parameters
    ----------
    dict : InputDictionary
        the input dictionary
    key : str
        the key to get the value from

    Returns
    -------
    PositiveReal | None
        the value of the key or None if the key is not in the dictionary

    Raises
    ------
    InputFileError
        if the value is not a positive real number
    """
    value = _parse_real(dict, key)

    if value is None:
        return None

    if value < 0:
        raise InputFileError(
            f"The \"{key}\" value has to be a positive real number - It actually is {value}!")

    return value


def _parse_real(dict: InputDictionary, key: str) -> Real | None:
    """
    Gets the value of a key from the input dictionary and checks if it is a real number.
    None is returned if the key is not in the dictionary.

    Parameters
    ----------
    dict : InputDictionary
        the input dictionary
    key : str
        the key to get the value from

    Returns
    -------
    PositiveReal | None
        the value of the key or None if the key is not in the dictionary

    Raises
    ------
    InputFileError
        if the value is not a real number
    """
    try:
        data = dict[key]
    except KeyError:
        return None

    data_type = data[1]

    if data_type != "float" and data_type != "int":
        raise InputFileError(
            f"The \"{key}\" value has to be of float type - actually it is parsed as a {data_type}")

    return data[0]


def _parse_files(dict: InputDictionary, key: str) -> List[str] | None:
    """
    Gets the value of a key from the input dictionary and checks if it is a list of strings, a glob or a string.
    If the key is not in the dictionary, None is returned.

    Parameters
    ----------
    dict : InputDictionary
        the input dictionary
    key : str
        the key to get the value from

    Returns
    -------
    List[str] | None
        the value of the key or None if the key is not in the dictionary

    Raises
    ------
    InputFileError
        if the value is not a list of strings, a glob or a string
    """
    try:
        data = dict[key]
    except KeyError:
        return None

    data_type = data[1]

    if data_type == "str":
        return [data[0]]
    elif data_type == "glob" or data_type == "list(str)":
        return data[0]
    else:
        raise InputFileError(
            f"The \"{key}\" value has to be either a string, glob or a list of strings - actually it is parsed as a {data_type}")


def _parse_int(dict: InputDictionary, key: str) -> int | None:
    """
    Gets the value of a key from the input dictionary and checks if it is an integer.

    Parameters
    ----------
    dict : InputDictionary
        the input dictionary
    key : str
        the key to get the value from

    Returns
    -------
    PositiveInt | None
        the value of the key or None if the key is not in the dictionary

    Raises
    ------
    InputFileError
        if the value is not an integer
    """
    try:
        data = dict[key]
    except KeyError:
        return None

    data_type = data[1]

    if data_type != "int":
        raise InputFileError(
            f"The \"{key}\" value has to be of int type - actually it is parsed as a {data_type}")

    return data[0]


def _parse_positive_int(dict: InputDictionary, key: str) -> PositiveInt | None:
    """
    Gets the value of a key from the input dictionary and checks if it is a positive integer.

    Parameters
    ----------
    dict : InputDictionary
        the input dictionary
    key : str
        the key to get the value from

    Returns
    -------
    PositiveInt | None
        the value of the key or None if the key is not in the dictionary

    Raises
    ------
    InputFileError
        if the value is not a positive integer
    """
    value = _parse_int(dict, key)

    if value is None:
        return None

    if value < 1:
        raise InputFileError(
            f"The \"{key}\" value has to be a positive integer - It actually is {value}!")

    return value


def _parse_string(dict: InputDictionary, key: str) -> str | None:
    """
    Gets the value of a key from the input dictionary and checks if it is a string.

    Parameters
    ----------
    dict : InputDictionary
        the input dictionary
    key : str
        the key to get the value from

    Returns
    -------
    str | None
        the value of the key or None if the key is not in the dictionary

    Raises
    ------
    InputFileError
        if the value is not a string
    """
    try:
        data = dict[key]
    except KeyError:
        return None

    data_type = data[1]

    if data_type != "str":
        raise InputFileError(
            f"The \"{key}\" value has to be of string type - actually it is parsed as a {data_type}")

    return data[0]


def _parse_bool(dict: InputDictionary, key: str) -> bool | None:
    """
    Gets the value of a key from the input dictionary and checks if it is a bool.

    Parameters
    ----------
    dict : InputDictionary
        the input dictionary
    key : str
        the key to get the value from

    Returns
    -------
    bool | None
        the value of the key or None if the key is not in the dictionary

    Raises
    ------
    InputFileError
        if the value is not a bool
    """
    try:
        data = dict[key]
    except KeyError:
        return None

    data_type = data[1]

    if data_type != "bool":
        raise InputFileError(
            f"The \"{key}\" value has to be of bool type - actually it is parsed as a {data_type}")

    return data[0]
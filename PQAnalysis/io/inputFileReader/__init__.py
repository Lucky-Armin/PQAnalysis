"""
A package containing modules, classes and functions to parse and read input files of PQAnalysis itself and the md engines it supports.
"""

from .inputFileParser import InputFileParser, InputDictionary
from .PQ import PQ_InputFileReader
from .PQAnalysis import PQAnalysisInputFileReader
from .formats import InputFileFormat

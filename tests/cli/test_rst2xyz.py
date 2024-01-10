import pytest
import argparse

from unittest import mock

from PQAnalysis.cli.rst2xyz import rst2xyz, main


@pytest.mark.parametrize("example_dir", ["rst2xyz"], indirect=False)
def test_rst2xyz(test_with_data_dir, capsys):
    print()
    rst2xyz("md-01.rst")

    captured = capsys.readouterr()
    assert captured.out == """
4 15.0623 15.0964 20.0232 89.9232 90.2261 120.324

C     1.0000000000     1.1000000000     1.2000000000
H     2.0000000000     2.1000000000     2.2000000000
N     3.0000000000     3.1000000000     3.2000000000
N     4.0000000000     4.1000000000     4.2000000000
"""

    print()
    rst2xyz("md-01.rst", print_box=False)

    captured = capsys.readouterr()
    assert captured.out == """
4

C     1.0000000000     1.1000000000     1.2000000000
H     2.0000000000     2.1000000000     2.2000000000
N     3.0000000000     3.1000000000     3.2000000000
N     4.0000000000     4.1000000000     4.2000000000
"""


@pytest.mark.parametrize("example_dir", ["rst2xyz"], indirect=False)
def test_main(test_with_data_dir, capsys):
    main_rst2xyz()

    captured = capsys.readouterr()
    assert captured.out == """
4 15.0623 15.0964 20.0232 89.9232 90.2261 120.324

C     1.0000000000     1.1000000000     1.2000000000
H     2.0000000000     2.1000000000     2.2000000000
N     3.0000000000     3.1000000000     3.2000000000
N     4.0000000000     4.1000000000     4.2000000000
"""


@mock.patch('argparse.ArgumentParser.parse_args',
            return_value=argparse.Namespace(restart_file="md-01.rst", output=None, nobox=False))
def main_rst2xyz(mock_args):
    print()
    main()

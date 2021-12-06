"""
Tests for fileio.reduction module
"""

import datetime
import unittest

from orsopy.fileio import base, reduction


class TestSoftware(unittest.TestCase):
    """
    Tests for the Software class.
    """

    def test_creation(self):
        """
        Creation of object with all arguments.
        """
        value = reduction.Software("Reducer", "1.2.3", "Ubuntu-20.04")
        assert value.name == "Reducer"
        assert value.version == "1.2.3"
        assert value.platform == "Ubuntu-20.04"

    def test_to_yaml(self):
        """
        Transform to yaml.
        """
        value = reduction.Software("Reducer", "1.2.3", "Ubuntu-20.04")
        assert value.to_yaml() == "name: Reducer\nversion: 1.2.3\nplatform: Ubuntu-20.04\n"

    def test_no_name_to_yaml(self):
        """
        Transform to yaml with no name.
        """
        value = reduction.Software(None, "1.0.0", "WindowsXP")
        assert value.to_yaml() == "name: null\nversion: 1.0.0\nplatform: WindowsXP\n"


class TestReduction(unittest.TestCase):
    """
    Tests for the Reduction class.
    """

    def test_creation(self):
        """
        Creation of an reduction class with minimal options.
        """
        value = reduction.Reduction(
            reduction.Software("Reducer", "1.2.3", "Ubuntu-20.04"),
            datetime.datetime(2021, 7, 7, 9, 11, 20),
            base.Person("A Person", "University"),
            ["footprint doi", "background"],
        )
        assert value.software == reduction.Software("Reducer", "1.2.3", "Ubuntu-20.04")
        assert value.timestamp == datetime.datetime(2021, 7, 7, 9, 11, 20)
        assert value.creator == base.Person("A Person", "University")
        assert value.corrections == ["footprint doi", "background"]

    def test_to_yaml(self):
        """
        Transform minimal options to yaml.
        """
        value = reduction.Reduction(
            reduction.Software("Reducer", "1.2.3", "Ubuntu-20.04"),
            datetime.datetime(2021, 7, 7, 9, 11, 20),
            base.Person("A Person", "University"),
            ["footprint doi", "background"],
        )
        assert (
            value.to_yaml()
            == "software:\n  name: Reducer\n  version: 1.2.3\n  "
            + "platform: Ubuntu-20.04\ntimestamp: 2021-07-07T09:11:20\n"
            + "creator:\n  name: A Person\n  affiliation: University\n"
            + "corrections:\n- footprint doi\n- background\n"
        )

    def test_call_to_yaml(self):
        """
        Tranform with call to yaml.
        """
        value = reduction.Reduction(
            reduction.Software("Reducer", "1.2.3", "Ubuntu-20.04"),
            datetime.datetime(2021, 7, 7, 9, 11, 20),
            base.Person("A Person", "University"),
            ["footprint doi", "background"],
            call="sh myreducer.sh 1 0",
        )
        assert value.to_yaml() == (
            "software:\n  name: Reducer\n  version: 1.2.3\n  "
            "platform: Ubuntu-20.04\ntimestamp: 2021-07-07T09:11:20\n"
            "creator:\n  name: A Person\n  affiliation: University\n"
            "corrections:\n- footprint doi\n- background\ncall: "
            "sh myreducer.sh 1 0\n"
        )

    def test_script_to_yaml(self):
        """
        Tranform with script to yaml.
        """
        value = reduction.Reduction(
            reduction.Software("Reducer", "1.2.3", "Ubuntu-20.04"),
            datetime.datetime(2021, 7, 7, 9, 11, 20),
            base.Person("A Person", "University"),
            ["footprint doi", "background"],
            script="/home/user/user1/scripts/reducer.py",
        )
        assert (
            value.to_yaml()
            == "software:\n  name: Reducer\n  version: 1.2.3\n  "
            + "platform: Ubuntu-20.04\ntimestamp: 2021-07-07T09:11:20\n"
            + "creator:\n  name: A Person\n  affiliation: University\n"
            + "corrections:\n- footprint doi\n- background\nscript: "
            + "/home/user/user1/scripts/reducer.py\n"
        )

    def test_computer_to_yaml(self):
        """
        Tranform with computer to yaml.
        """
        value = reduction.Reduction(
            reduction.Software("Reducer", "1.2.3", "Ubuntu-20.04"),
            datetime.datetime(2021, 7, 7, 9, 11, 20),
            base.Person("A Person", "University"),
            ["footprint doi", "background"],
            computer="cluster.esss.dk",
        )
        assert (
            value.to_yaml()
            == "software:\n  name: Reducer\n  version: 1.2.3\n  "
            + "platform: Ubuntu-20.04\ntimestamp: 2021-07-07T09:11:20\n"
            + "creator:\n  name: A Person\n  affiliation: University\n"
            + "corrections:\n- footprint doi\n- background\ncomputer: "
            + "cluster.esss.dk\n"
        )

    def test_binary_to_yaml(self):
        """
        Tranform with computer to yaml.
        """
        value = reduction.Reduction(
            reduction.Software("Reducer", "1.2.3", "Ubuntu-20.04"),
            datetime.datetime(2021, 7, 7, 9, 11, 20),
            base.Person("A Person", "University"),
            ["footprint doi", "background"],
            binary="/home/users/user1/bin/file",
        )
        assert (
            value.to_yaml()
            == "software:\n  name: Reducer\n  version: 1.2.3\n  "
            + "platform: Ubuntu-20.04\ntimestamp: 2021-07-07T09:11:20\n"
            + "creator:\n  name: A Person\n  affiliation: University\n"
            + "corrections:\n- footprint doi\n- background\nbinary: "
            + "/home/users/user1/bin/file\n"
        )

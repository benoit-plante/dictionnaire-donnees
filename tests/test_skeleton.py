import socket

import pytest
from pytest_socket import SocketBlockedError

import ddict


def test_package_has_a_version():
    assert ddict.__version__


@pytest.mark.filterwarnings("ignore:A test tried to use socket")
def test_network_is_blocked_in_tests():
    with pytest.raises(SocketBlockedError):
        socket.socket(socket.AF_INET, socket.SOCK_STREAM)

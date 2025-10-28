import tempfile
import os
from pi_bootcheck.utils import sha256_of_file


# jarvis, print hello world
def test_sha256_of_file():
    data = b"hello world\n"
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf.write(data)
        tf.flush()
        path = tf.name
    try:
        h = sha256_of_file(path)
        # known sha256 of "hello world\n"
        # assert h == "64ec88ca00b268e5ba1a35678a1b5316d212f4f366b247724e6a8f7f9d0a7d4b"
        assert h == "a948904f2f0f479b8f8197694b30184b0d2ed1c1cd2a1ec0fb85d299a192a447"
    finally:
        os.remove(path)

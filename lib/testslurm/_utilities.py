import random
import string
from pathlib import Path

import numpy as np

BASE94 = string.ascii_letters + string.digits + string.punctuation

def random_unique_filename(directory, suffix = "", length = 6, alphabet = BASE94, num_attempts = 10):

    directory = Path(directory)

    for n in range(num_attempts):

        filename =  directory / "".join(random.choices(alphabet, k = length + n))

        if suffix != "":
            filename = filename.with_suffix(suffix)

        if not filename.exists():
            return filename

    raise RuntimeError("buy a lottery ticket fr")


def is_int(num):
    return isinstance(num, (int, np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64))

def check_type(obj, name, expected_type):

    if not isinstance(obj, expected_type):
        raise TypeError(f"`{name}` must be of type `{expected_type.__name__}`, not `{type(obj).__name__}`.")

def check_type_None_default(obj, name, expected_type, default):

    if obj is not None and not isinstance(obj, expected_type):
        raise TypeError(f"`{name}` must be of type `{expected_type.__name__}`, not `{type(obj).__name__}`.")

    elif obj is not None:
        return obj

    else:
        return default

def check_return_int(obj, name):

    if not is_int(obj):
        raise TypeError(f"`{name}` must be of type `int`, not `{type(obj).__name__}`.")

    else:
        return int(obj)

def check_return_int_None_default(obj, name, default):

    if obj is not None and not is_int(obj):
        raise TypeError(f"`{name}` must be of type `int`, not `{type(obj).__name__}`.")

    elif obj is not None:
        return int(obj)

    else:
        return default

def check_return_Path(obj, name):

    if not isinstance(obj, (str, Path)):
        raise TypeError(f"`{name}` must be either of type `str` or `pathlib.Path`, not `{type(obj).__name__}`.")

    else:
        return Path(obj)

def check_return_Path_None_default(obj, name, default):

    if obj is None:
        return default

    elif not isinstance(obj, (str, Path)):
        raise TypeError(f"`{name}` must be either of type `str` or `pathlib.Path`, not `{type(obj).__name__}`.")

    else:
        return Path(obj)

def resolve_path(path):
    """
    :param path: (type `pathlib.Path`)
    :raise FileNotFoundError: If the path could not be resolved.
    :return: (type `pathlib.Path`) Resolved.
    """

    try:
        resolved = path.resolve(True) # True raises FileNotFoundError

    except FileNotFoundError:
        raise_error = True

    else:
        return resolved

    if raise_error:

        resolved = path.resolve(False) # False suppressed FileNotFoundError

        for parent in reversed(resolved.parents):

            if not parent.exists():
                raise FileNotFoundError(
                    f"Resolved path : `{resolved}`\n" +
                    f"The file or directory `{str(parent)}` could not be found."
                )

        else:
            raise FileNotFoundError(f"The file or directory `{path}` could not be found.")
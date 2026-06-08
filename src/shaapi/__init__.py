"""shaapi — scaffold lean, batteries-included FastAPI backends."""
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("shaapi")
except PackageNotFoundError:  # not installed (e.g. running from a source checkout)
    __version__ = "0.0.0"

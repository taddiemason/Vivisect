"""Tab screens for the native GUI."""

from .dashboard import DashboardScreen
from .disk import DiskScreen
from .network import NetworkScreen
from .memory import MemoryScreen
from .artifacts import ArtifactsScreen
from .hid import HIDScreen
from .reports import ReportsScreen

# Display order of the tabs.
SCREEN_CLASSES = [
    DashboardScreen,
    DiskScreen,
    NetworkScreen,
    MemoryScreen,
    ArtifactsScreen,
    HIDScreen,
    ReportsScreen,
]

__all__ = [
    'DashboardScreen', 'DiskScreen', 'NetworkScreen', 'MemoryScreen',
    'ArtifactsScreen', 'HIDScreen', 'ReportsScreen', 'SCREEN_CLASSES',
]

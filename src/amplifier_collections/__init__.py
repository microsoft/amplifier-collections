"""amplifier-collections - Convention-based collection discovery and management.

Public API exports matching README.md specification.

Per KERNEL_PHILOSOPHY: This is library mechanism, apps inject policy (paths, sources).
"""

from .discovery import CollectionResources
from .discovery import discover_collection_resources
from .discovery import list_agents
from .discovery import list_profiles
from .exceptions import CollectionError
from .exceptions import CollectionInstallError
from .exceptions import CollectionMetadataError
from .exceptions import CollectionNotFoundError
from .installer import install_collection
from .installer import uninstall_collection
from .lock import CollectionLock
from .lock import CollectionLockEntry
from .protocols import InstallSourceProtocol
from .resolver import CollectionResolver
from .schema import CollectionMetadata
from .utils import extract_collection_name_from_path

__all__ = [
    # Metadata
    "CollectionMetadata",
    # Resolution
    "CollectionResolver",
    # Discovery
    "CollectionResources",
    "discover_collection_resources",
    "list_profiles",
    "list_agents",
    # Installation
    "install_collection",
    "uninstall_collection",
    "InstallSourceProtocol",
    # Lock file
    "CollectionLock",
    "CollectionLockEntry",
    # Exceptions
    "CollectionError",
    "CollectionInstallError",
    "CollectionMetadataError",
    "CollectionNotFoundError",
    # Utilities
    "extract_collection_name_from_path",
]

__version__ = "0.1.0"

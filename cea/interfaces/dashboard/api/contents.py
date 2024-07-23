import os.path
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, List

from fastapi import APIRouter, HTTPException, status

from cea.interfaces.dashboard.dependencies import CEAConfig
from cea.interfaces.dashboard.utils import secure_path, InvalidPathError

router = APIRouter()


class ContentType(Enum):
    directory = 'directory'
    file = 'file'


class ContentPathNotFound(Exception):
    pass


class ContentTypeInvalid(Exception):
    pass


@dataclass
class ContentInfo:
    name: str
    path: str
    last_modified: float
    contents: Optional[List["ContentInfo"]]
    size: Optional[int]
    type: ContentType

    @staticmethod
    def _dict_factory(data):
        return {
            field: value.value if isinstance(value, Enum) else value
            for field, value in data
        }

    def as_dict(self):
        return asdict(self, dict_factory=self._dict_factory)


def get_content_info(root_path: str, content_path: str, content_type: ContentType,
                     depth: int = 1, show_hidden: bool = False) -> ContentInfo:
    full_path = os.path.join(root_path, content_path)
    if not os.path.exists(full_path):
        raise ContentPathNotFound

    if not ((content_type == ContentType.file and os.path.isfile(full_path))
            or (content_type == ContentType.directory and os.path.isdir(full_path))):
        raise ContentTypeInvalid

    contents = None
    # continue recursively up to depth
    if depth > 0 and content_type == ContentType.directory:
        _contents = [
            (item, ContentType.file if os.path.isfile(os.path.join(full_path, item)) else ContentType.directory)
            # ignore "hidden" items that start with "."
            for item in os.listdir(full_path) if not item.startswith(".") or show_hidden
        ]
        contents = [get_content_info(root_path, os.path.join(content_path, _path).replace("\\", "/"), _type,
                                     depth - 1, show_hidden)
                    for _path, _type in _contents]

    size = None
    if content_type == ContentType.file:
        size = os.path.getsize(full_path)

    return ContentInfo(
        name=os.path.basename(content_path),
        path=content_path,
        last_modified=os.path.getmtime(full_path),
        contents=contents,
        size=size,
        type=content_type
    )


@router.get('/')
@router.get('/{content_path}')
async def get_contents(config: CEAConfig, type: ContentType, root: str,
                       content_path: str = "", show_hidden: bool = False):
    """
    Get information of the content path provided
    """
    content_type = type

    if root is None:
        root_path = config.server.project_root
    else:
        root_path = root
    try:
        # Check path first
        secure_path(os.path.join(root_path, content_path))
        content_info = get_content_info(root_path, content_path, content_type, show_hidden=show_hidden)
        return content_info.as_dict()
    except (ContentPathNotFound, InvalidPathError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Path `{content_path}` does not exist",
        )
    except ContentTypeInvalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path `{content_path}` is not of type `{content_type.value}`",
        )

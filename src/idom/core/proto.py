"""
Core Interfaces
===============
"""

from __future__ import annotations

from types import TracebackType
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
)

from typing_extensions import Protocol, TypedDict, runtime_checkable


ComponentConstructor = Callable[..., "ComponentType"]
"""Simple function returning a new component"""


@runtime_checkable
class ComponentType(Protocol):
    """The expected interface for all component-like objects"""

    key: Optional[Any]
    """An identifier which is unique amongst a component's immediate siblings"""

    def render(self) -> VdomDict:
        """Render the component's :class:`VdomDict`."""


_Self = TypeVar("_Self")
_Render = TypeVar("_Render", covariant=True)
_Event = TypeVar("_Event", contravariant=True)


@runtime_checkable
class LayoutType(Protocol[_Render, _Event]):
    """Renders and delivers, updates to views and events to handlers, respectively"""

    async def render(self) -> _Render:
        """Render an update to a view"""

    async def deliver(self, event: _Event) -> None:
        """Relay an event to its respective handler"""

    def __enter__(self: _Self) -> _Self:
        """Prepare the layout for its first render"""

    def __exit__(
        self, exc_type: Type[Exception], exc_value: Exception, traceback: TracebackType
    ) -> Optional[bool]:
        """Clean up the view after its final render"""


VdomAttributes = Mapping[str, Any]
"""Describes the attributes of a :class:`VdomDict`"""

VdomChild = Union[ComponentType, "VdomDict", str]
"""A single child element of a :class:`VdomDict`"""

VdomChildren = Sequence[VdomChild]
"""Describes a series of :class:`VdomChild` elements"""

VdomAttributesAndChildren = Union[
    Mapping[str, Any],  # this describes both VdomDict and VdomAttributes
    Iterable[VdomChild],
]
"""Useful for the ``*attributes_and_children`` parameter in :func:`idom.core.vdom.vdom`"""


class _VdomDictOptional(TypedDict, total=False):
    key: str
    children: Sequence[
        # recursive types are not allowed yet:
        # https://github.com/python/mypy/issues/731
        Union[ComponentType, Dict[str, Any], str]
    ]
    attributes: VdomAttributes
    eventHandlers: EventHandlerDict  # noqa
    importSource: ImportSourceDict  # noqa


class _VdomDictRequired(TypedDict, total=True):
    tagName: str  # noqa


class VdomDict(_VdomDictRequired, _VdomDictOptional):
    """A :ref:`VDOM` dictionary"""


class ImportSourceDict(TypedDict):
    source: str
    fallback: Any
    sourceType: str  # noqa
    unmountBeforeUpdate: bool  # noqa


class _OptionalVdomJson(TypedDict, total=False):
    key: str
    error: str
    children: List[Any]
    attributes: Dict[str, Any]
    eventHandlers: Dict[str, _JsonEventTarget]  # noqa
    importSource: _JsonImportSource  # noqa


class _RequiredVdomJson(TypedDict, total=True):
    tagName: str  # noqa


class VdomJson(_RequiredVdomJson, _OptionalVdomJson):
    """A JSON serializable form of :class:`VdomDict` matching the :data:`VDOM_JSON_SCHEMA`"""


class _JsonEventTarget(TypedDict):
    target: str
    preventDefault: bool  # noqa
    stopPropagation: bool  # noqa


class _JsonImportSource(TypedDict):
    source: str
    fallback: Any


EventHandlerMapping = Mapping[str, "EventHandlerType"]
"""A generic mapping between event names to their handlers"""

EventHandlerDict = Dict[str, "EventHandlerType"]
"""A dict mapping between event names to their handlers"""


class EventHandlerFunc(Protocol):
    """A coroutine which can handle event data"""

    async def __call__(self, data: List[Any]) -> None:
        ...


@runtime_checkable
class EventHandlerType(Protocol):
    """Defines a handler for some event"""

    prevent_default: bool
    """Whether to block the event from propagating further up the DOM"""

    stop_propagation: bool
    """Stops the default action associate with the event from taking place."""

    function: EventHandlerFunc
    """A coroutine which can respond to an event and its data"""

    target: Optional[str]
    """Typically left as ``None`` except when a static target is useful.

    When testing, it may be useful to specify a static target ID so events can be
    triggered programatically.

    .. note::

        When ``None``, it is left to a :class:`LayoutType` to auto generate a unique ID.
    """

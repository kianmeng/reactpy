import abc
from typing import TypeVar, Dict, Any, Tuple, Optional, Generic, TypeVar
from threading import Thread, Event

from idom.core.element import ElementConstructor


_App = TypeVar("_App", bound=Any)
_Config = TypeVar("_Config", bound=Any)
_Self = TypeVar("_Self", bound="AbstractRenderServer[Any, Any]")


class AbstractRenderServer(Generic[_App, _Config]):
    """Base class for all IDOM server application and extension implementations.

    It is assumed that IDOM will be used in conjuction with some async-enabled server
    library (e.g. ``sanic`` or ``tornado``) so these server implementations should work
    standalone and as an extension to an existing application.

    Standalone usage:
        :meth:`AbstractServerExtension.run` or :meth:`AbstractServerExtension.daemon`
    Register an extension:
        :meth:`AbstractServerExtension.register`
    """

    def __init__(
        self,
        constructor: ElementConstructor,
        config: Optional[_Config] = None,
    ) -> None:
        self._app: Optional[_App] = None
        self._root_element_constructor = constructor
        self._daemonized = False
        self._config = self._create_config(config)
        self._server_did_start = Event()

    @property
    def application(self) -> _App:
        if self._app is None:
            raise RuntimeError("No application registered.")
        return self._app

    def run(self, *args: Any, **kwargs: Any) -> None:
        """Run as a standalone application."""
        if self._app is None:
            app = self._default_application(self._config)
            self.register(app)
        else:
            app = self._app
        if not self._daemonized:
            return self._run_application(app, self._config, args, kwargs)
        else:
            return self._run_application_in_thread(app, self._config, args, kwargs)

    def daemon(self, *args: Any, **kwargs: Any) -> Thread:
        """Run the standalone application in a seperate thread."""
        self._daemonized = True

        thread = Thread(target=lambda: self.run(*args, **kwargs), daemon=True)
        thread.start()

        self.wait_until_server_start()

        return thread

    def register(self: _Self, app: Optional[_App]) -> _Self:
        """Register this as an extension."""
        self._setup_application(app, self._config)
        self._setup_application_did_start_event(app, self._server_did_start)
        self._app = app
        return self

    def server_started(self) -> bool:
        """Whether the underlying application has started"""
        return self._server_did_start.set()

    def wait_until_server_start(self, timeout: float = 3.0):
        """Block until the underlying application has started"""
        if not self._server_did_start.wait(timeout=timeout):
            raise RuntimeError(f"Server did not start within {timeout} seconds")

    @abc.abstractmethod
    def _create_config(self, config: Optional[_Config]) -> _Config:
        """Return the default configuration options."""

    @abc.abstractmethod
    def _default_application(self, config: _Config) -> _App:
        """If used standalone this should return an application."""
        raise NotImplementedError()

    @abc.abstractmethod
    def _setup_application(self, app: _App, config: _Config) -> None:
        """General application setup - add routes, templates, static resource, etc."""
        raise NotImplementedError()

    @abc.abstractmethod
    def _setup_application_did_start_event(self, app: _App, event: Event) -> None:
        """Register a callback to the app indicating whether the server has started"""
        raise NotImplementedError()

    @abc.abstractmethod
    def _run_application(
        self, app: _App, config: _Config, args: Tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> None:
        """Run the application in the main thread"""
        raise NotImplementedError()

    @abc.abstractmethod
    def _run_application_in_thread(
        self, app: _App, config: _Config, args: Tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> None:
        """This function has been called inside a daemon thread to run the application"""
        raise NotImplementedError()

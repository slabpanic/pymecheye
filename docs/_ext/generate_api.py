"""Generate API indexes from runtime exports and reject missing public docstrings."""

from importlib import import_module
import inspect
from pathlib import Path

MODULES = (
    "mecheye.shared",
    "mecheye.area_scan_3d_camera",
    "mecheye.area_scan_3d_camera_utils",
)


def public_objects(module):
    """Use canonical public definitions, documenting shared container adapters once."""
    classes, functions, constants = [], [], []
    for name in module.__all__:
        value = getattr(module, name)
        origin = getattr(value, "__module__", None)
        owned = origin == module.__name__ or (
            module.__name__ == "mecheye.shared" and origin == "mecheye._containers"
        )
        qualified = f"{module.__name__}.{name}"
        if inspect.isclass(value) and owned:
            classes.append(qualified)
        elif inspect.isfunction(value) and owned:
            functions.append(qualified)
        elif isinstance(value, (int, float, str)):
            constants.append(qualified)
    return classes, functions, constants


def check_docstrings(qualified, value):
    """Check every public method/property implemented by the wrapper, including bases."""
    missing = []
    if not (value.__doc__ if inspect.isclass(value) else inspect.getdoc(value)):
        missing.append(qualified)
    if inspect.isclass(value):
        for base in value.__mro__:
            if not base.__module__.startswith("mecheye."):
                continue
            for name, member in vars(base).items():
                if name.startswith("_"):
                    continue
                if isinstance(member, (classmethod, staticmethod)):
                    member = member.__func__
                if (
                    inspect.isfunction(member) or isinstance(member, property)
                ) and not inspect.getdoc(member):
                    missing.append(f"{qualified}.{name}")
    return missing


def write_if_changed(path: Path, text: str):
    """Keep source timestamps stable during incremental Sphinx builds."""
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")


def generate_api(docs: Path):
    """Validate exports and write autosummary input files; no camera is constructed."""
    output = docs / "api/_generated"
    output.mkdir(parents=True, exist_ok=True)
    missing = []
    pages = []
    expected_objects = set()
    for name in MODULES:
        module = import_module(name)
        classes, functions, constants = public_objects(module)
        expected_objects.update(qualified + ".rst" for qualified in classes + functions)
        for qualified in classes + functions:
            missing.extend(
                check_docstrings(
                    qualified, getattr(module, qualified.rsplit(".", 1)[-1])
                )
            )
        exceptions = [
            item
            for item in classes
            if issubclass(getattr(module, item.rsplit(".", 1)[-1]), BaseException)
        ]
        classes = [item for item in classes if item not in exceptions]
        lines = [name, "=" * len(name), "", f".. automodule:: {name}", ""]
        if name.endswith("_utils"):
            lines += [
                "This module also re-exports camera and shared types. Their canonical",
                "definitions are documented on the other API module pages.",
                "",
            ]
        for title, objects, template in (
            ("Classes", classes, "class.rst"),
            ("Exceptions", exceptions, "exception.rst"),
            ("Functions", functions, "function.rst"),
        ):
            if objects:
                lines += [
                    title,
                    "-" * len(title),
                    "",
                    ".. autosummary::",
                    "   :toctree: objects",
                    f"   :template: autosummary/{template}",
                    "",
                    *["   " + obj.rsplit(".", 1)[-1] for obj in objects],
                    "",
                ]
        if constants:
            lines += ["Constants", "---------", ""]
            for constant in constants:
                lines += [f".. autodata:: {constant}", ""]
        pages.append((output / (name.rsplit(".", 1)[-1] + ".rst"), "\n".join(lines)))
    if missing:
        raise RuntimeError(
            "Public API docstrings are missing:\n" + "\n".join(sorted(set(missing)))
        )
    # Remove obsolete stubs so removed exports do not leave stale API pages.
    for path in (output / "objects").glob("*.rst"):
        if path.name not in expected_objects:
            path.unlink()
    for path, text in pages:
        write_if_changed(path, text)

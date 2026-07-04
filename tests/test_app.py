from control_plane import __version__
from control_plane.app import MODULES, module_map


def test_version_is_set():
    assert __version__


def test_module_registry_is_well_formed():
    keys = [m.key for m in module_map()]
    assert keys == ["core", "gateway", "prompts", "evals", "observability", "dashboard"]
    assert len(set(keys)) == len(keys)  # unique
    assert all(m.status in {"planned", "building", "available"} for m in MODULES)
    assert all(m.name and m.summary for m in MODULES)
    # the first slice starts at the core
    assert next(m for m in MODULES if m.key == "core").status == "building"

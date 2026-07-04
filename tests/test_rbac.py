from control_plane.core.rbac import Permission, Role, has_permission


def test_owner_has_every_permission():
    assert all(has_permission(Role.OWNER.value, p) for p in Permission)


def test_viewer_is_read_only():
    assert has_permission("viewer", Permission.ORG_READ)
    assert has_permission("viewer", Permission.USER_READ)
    assert not has_permission("viewer", Permission.USER_MANAGE)
    assert not has_permission("viewer", Permission.GATEWAY_INVOKE)


def test_member_can_invoke_but_not_manage():
    assert has_permission("member", Permission.GATEWAY_INVOKE)
    assert not has_permission("member", Permission.USER_MANAGE)


def test_unknown_role_has_nothing():
    assert not has_permission("wizard", Permission.ORG_READ)

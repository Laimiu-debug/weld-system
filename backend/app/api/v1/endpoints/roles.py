"""
Role and permission API endpoints for the welding system backend.
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.role import (
    PermissionCreate, PermissionResponse, PermissionUpdate,
    RoleCreate, RoleResponse, RoleUpdate, UserRoleAssignment, UserRoleResponse
)
from app.services.role_service import role_service, permission_service

router = APIRouter()


# Permission endpoints
@router.get("/permissions/", response_model=List[PermissionResponse])
def read_permissions(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve permissions."""
    # Check permission
    if not user_service.has_permission(db, current_user.id, "role", "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    permissions = permission_service.get_multi(db, skip=skip, limit=limit)
    return permissions


@router.post("/permissions/", response_model=PermissionResponse)
def create_permission(
    *,
    db: Session = Depends(deps.get_db),
    permission_in: PermissionCreate,
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """Create new permission."""
    # Check permission
    if not user_service.has_permission(db, current_user.id, "role", "create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    permission = permission_service.get_by_name(db, name=permission_in.name)
    if permission:
        raise HTTPException(
            status_code=400,
            detail="Permission with this name already exists"
        )

    return permission_service.create(db, obj_in=permission_in)


@router.get("/permissions/{id}", response_model=PermissionResponse)
def read_permission(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """Get permission by ID."""
    # Check permission
    if not user_service.has_permission(db, current_user.id, "role", "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    permission = permission_service.get(db, id=id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    return permission


@router.put("/permissions/{id}", response_model=PermissionResponse)
def update_permission(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    permission_in: PermissionUpdate,
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """Update permission."""
    # Check permission
    if not user_service.has_permission(db, current_user.id, "role", "update"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    permission = permission_service.get(db, id=id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    return permission_service.update(db, db_obj=permission, obj_in=permission_in)


@router.delete("/permissions/{id}", response_model=PermissionResponse)
def delete_permission(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """Delete permission."""
    # Check permission
    if not user_service.has_permission(db, current_user.id, "role", "delete"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    permission = permission_service.get(db, id=id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    return permission_service.remove(db, id=id)


# Role endpoints
@router.get("/", response_model=List[RoleResponse])
def read_roles(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve roles."""
    # Check permission
    if not user_service.has_permission(db, current_user.id, "role", "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    roles = role_service.get_multi(db, skip=skip, limit=limit)
    return roles


@router.post("/", response_model=RoleResponse)
def create_role(
    *,
    db: Session = Depends(deps.get_db),
    role_in: RoleCreate,
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """Create new role."""
    # Check permission
    if not user_service.has_permission(db, current_user.id, "role", "create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    role = role_service.get_by_name(db, name=role_in.name)
    if role:
        raise HTTPException(
            status_code=400,
            detail="Role with this name already exists"
        )

    return role_service.create(db, obj_in=role_in)


@router.get("/{id}", response_model=RoleResponse)
def read_role(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """Get role by ID."""
    # Check permission
    if not user_service.has_permission(db, current_user.id, "role", "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    role = role_service.get(db, id=id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.put("/{id}", response_model=RoleResponse)
def update_role(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    role_in: RoleUpdate,
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """Update role."""
    # Check permission
    if not user_service.has_permission(db, current_user.id, "role", "update"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    role = role_service.get(db, id=id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return role_service.update(db, db_obj=role, obj_in=role_in)


@router.delete("/{id}", response_model=RoleResponse)
def delete_role(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """Delete role."""
    # Check permission
    if not user_service.has_permission(db, current_user.id, "role", "delete"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    role = role_service.get(db, id=id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return role_service.remove(db, id=id)


# User role assignment endpoints
@router.post("/users/{user_id}/roles/{role_id}", response_model=UserRoleResponse)
def assign_role_to_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    role_id: int,
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """Assign role to user."""
    # Check permission
    if not user_service.has_permission(db, current_user.id, "role", "assign"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    user = role_service.assign_role_to_user(db, user_id=user_id, role_id=role_id)
    return user


@router.delete("/users/{user_id}/roles/{role_id}", response_model=UserRoleResponse)
def remove_role_from_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    role_id: int,
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """Remove role from user."""
    # Check permission
    if not user_service.has_permission(db, current_user.id, "role", "assign"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    user = role_service.remove_role_from_user(db, user_id=user_id, role_id=role_id)
    return user


@router.put("/users/{user_id}/roles", response_model=UserRoleResponse)
def assign_multiple_roles_to_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    role_assignment: UserRoleAssignment,
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """Assign multiple roles to user."""
    # Check permission
    if not user_service.has_permission(db, current_user.id, "role", "assign"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    if user_id != role_assignment.user_id:
        raise HTTPException(
            status_code=400,
            detail="User ID mismatch"
        )

    user = role_service.assign_multiple_roles_to_user(
        db, user_id=user_id, role_ids=role_assignment.role_ids
    )
    return user


@router.get("/users/{user_id}/permissions", response_model=List[str])
def get_user_permissions(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """Get all permissions for a user."""
    # Check permission
    if not user_service.has_permission(db, current_user.id, "role", "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    permissions = role_service.get_user_permissions(db, user_id=user_id)
    return list(permissions)


# Import user_service at the end to avoid circular imports
from app.services.user_service import user_service
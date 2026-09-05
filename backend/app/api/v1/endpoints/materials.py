"""
Material Management API endpoints for the welding system backend.
"""
from typing import Any, List, Optional
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.material import MaterialCreate, MaterialUpdate, MaterialResponse, MaterialListResponse
from app.services.material_service import MaterialService
from app.core.data_access import WorkspaceContext

router = APIRouter()


@router.get("/", response_model=dict)
def get_materials_list(
    db: Session = Depends(deps.get_db),
    workspace_type: str = Query(..., description="??????personal/enterprise"),
    company_id: Optional[int] = Query(None, description="??ID?????????"),
    factory_id: Optional[int] = Query(None, description="??ID????"),
    skip: int = Query(0, ge=0, description="?????"),
    limit: int = Query(100, ge=1, le=1000, description="?????"),
    search: Optional[str] = Query(None, description="?????"),
    material_type: Optional[str] = Query(None, description="????"),
    low_stock: Optional[bool] = Query(None, description="?????"),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    ??????

    - **workspace_type**: ??????personal/enterprise?
    - **company_id**: ??ID?????????
    - **factory_id**: ??ID????
    - **skip**: ??????
    - **limit**: ??????
    - **search**: ?????
    - **material_type**: ??????
    - **low_stock**: ????????
    """
    try:
        # ????????
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        # ?????
        service = MaterialService(db)
        materials, total = service.get_material_list(
            current_user=current_user,
            workspace_context=workspace_context,
            skip=skip,
            limit=limit,
            search=search,
            material_type=material_type,
            low_stock=low_stock
        )

        # ??????
        page = (skip // limit) + 1 if limit > 0 else 1
        total_pages = ceil(total / limit) if limit > 0 else 0

        return {
            "success": True,
            "data": {
                "items": [MaterialResponse.model_validate(m) for m in materials],
                "total": total,
                "page": page,
                "page_size": limit,
                "total_pages": total_pages
            },
            "message": "????????"
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        print(f"? ????????: {error_detail}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/", response_model=dict)
def create_material(
    material_in: MaterialCreate,
    workspace_type: str = Query(..., description="??????personal/enterprise"),
    company_id: Optional[int] = Query(None, description="??ID?????????"),
    factory_id: Optional[int] = Query(None, description="??ID????"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    ?????

    - **workspace_type**: ??????personal/enterprise?
    - **company_id**: ??ID?????????
    - **factory_id**: ??ID????
    """
    try:
        # ????????
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        # ?????
        service = MaterialService(db)
        material = service.create_material(
            current_user=current_user,
            material_data=material_in.model_dump(),
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": MaterialResponse.model_validate(material),
            "message": "??????"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{material_id:int}", response_model=dict)
def get_material_detail(
    material_id: int,
    workspace_type: str = Query(..., description="??????personal/enterprise"),
    company_id: Optional[int] = Query(None, description="??ID?????????"),
    factory_id: Optional[int] = Query(None, description="??ID????"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    ??????

    - **material_id**: ??ID
    - **workspace_type**: ??????personal/enterprise?
    - **company_id**: ??ID?????????
    - **factory_id**: ??ID????
    """
    try:
        # ????????
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        # ?????
        service = MaterialService(db)
        material = service.get_material_by_id(
            material_id=material_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": MaterialResponse.model_validate(material),
            "message": "????????"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{material_id:int}", response_model=dict)
def update_material(
    material_id: int,
    material_in: MaterialUpdate,
    workspace_type: str = Query(..., description="??????personal/enterprise"),
    company_id: Optional[int] = Query(None, description="??ID?????????"),
    factory_id: Optional[int] = Query(None, description="??ID????"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    ??????

    - **material_id**: ??ID
    - **workspace_type**: ??????personal/enterprise?
    - **company_id**: ??ID?????????
    - **factory_id**: ??ID????
    """
    try:
        # ????????
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        # ?????
        service = MaterialService(db)
        material = service.update_material(
            material_id=material_id,
            current_user=current_user,
            material_data=material_in.model_dump(exclude_unset=True),
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": MaterialResponse.model_validate(material),
            "message": "????????"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{material_id:int}", response_model=dict)
def delete_material(
    material_id: int,
    workspace_type: str = Query(..., description="??????personal/enterprise"),
    company_id: Optional[int] = Query(None, description="??ID?????????"),
    factory_id: Optional[int] = Query(None, description="??ID????"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    ????

    - **material_id**: ??ID
    - **workspace_type**: ??????personal/enterprise?
    - **company_id**: ??ID?????????
    - **factory_id**: ??ID????
    """
    try:
        print(f"??? ??????:")
        print(f"   material_id: {material_id}")
        print(f"   workspace_type: {workspace_type}")
        print(f"   company_id: {company_id}")
        print(f"   factory_id: {factory_id}")
        print(f"   current_user: {current_user.id} ({current_user.username})")

        # ????????
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        # ?????
        service = MaterialService(db)
        service.delete_material(
            material_id=material_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        print(f"? ??????")
        return {
            "success": True,
            "message": "??????"
        }

    except HTTPException as e:
        print(f"? ?????? (HTTPException): {e.status_code} - {e.detail}")
        raise
    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        print(f"? ?????? (Exception): {error_detail}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{material_id}/stock-in")
def material_stock_in_by_id(
    material_id: int,
    transaction_data: dict,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID"),
    factory_id: Optional[int] = Query(None, description="工厂ID"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """按焊材ID入库。"""
    workspace_context = WorkspaceContext(
        workspace_type=workspace_type,
        user_id=current_user.id,
        company_id=company_id,
        factory_id=factory_id
    )
    service = MaterialService(db)
    result = service.stock_in(
        current_user=current_user,
        material_id=material_id,
        quantity=float(transaction_data.get("quantity") or 0),
        workspace_context=workspace_context,
        unit_price=transaction_data.get("unit_price"),
        source=transaction_data.get("source"),
        batch_number=transaction_data.get("batch_number"),
        warehouse=transaction_data.get("warehouse"),
        storage_location=transaction_data.get("storage_location"),
        notes=transaction_data.get("notes"),
    )
    return {
        "success": True,
        "data": {
            "transaction_id": result["transaction"].id,
            "transaction_number": result["transaction"].transaction_number,
            "current_stock": result["material"].current_stock,
            "unit": result["material"].unit
        },
        "message": result["message"]
    }


@router.post("/{material_id}/stock-out")
def material_stock_out_by_id(
    material_id: int,
    transaction_data: dict,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID"),
    factory_id: Optional[int] = Query(None, description="工厂ID"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """按焊材ID出库。"""
    workspace_context = WorkspaceContext(
        workspace_type=workspace_type,
        user_id=current_user.id,
        company_id=company_id,
        factory_id=factory_id
    )
    service = MaterialService(db)
    result = service.stock_out(
        current_user=current_user,
        material_id=material_id,
        quantity=float(transaction_data.get("quantity") or 0),
        workspace_context=workspace_context,
        destination=transaction_data.get("destination"),
        reference_type=transaction_data.get("reference_type"),
        reference_id=transaction_data.get("reference_id"),
        reference_number=transaction_data.get("reference_number"),
        notes=transaction_data.get("notes"),
    )
    return {
        "success": True,
        "data": {
            "transaction_id": result["transaction"].id,
            "transaction_number": result["transaction"].transaction_number,
            "current_stock": result["material"].current_stock,
            "unit": result["material"].unit
        },
        "message": result["message"]
    }


@router.get("/{material_id}/transactions")
def get_material_transactions_by_id(
    material_id: int,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID"),
    factory_id: Optional[int] = Query(None, description="工厂ID"),
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """获取指定焊材的出入库记录。"""
    workspace_context = WorkspaceContext(
        workspace_type=workspace_type,
        user_id=current_user.id,
        company_id=company_id,
        factory_id=factory_id
    )
    service = MaterialService(db)
    result = service.get_transaction_list(
        current_user=current_user,
        workspace_context=workspace_context,
        material_id=material_id,
        skip=skip,
        limit=limit,
    )
    return {
        "success": True,
        "data": result,
        "message": "获取出入库记录成功"
    }


@router.get("/low-stock/alerts")
def get_low_stock_alerts(
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID"),
    factory_id: Optional[int] = Query(None, description="工厂ID"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """获取低库存预警。"""
    workspace_context = WorkspaceContext(
        workspace_type=workspace_type,
        user_id=current_user.id,
        company_id=company_id,
        factory_id=factory_id
    )
    service = MaterialService(db)
    result = service.get_low_stock_alerts(current_user, workspace_context)
    return {
        "success": True,
        "data": {
            "items": [MaterialResponse.model_validate(item) for item in result["items"]],
            "total": result["total"],
        },
        "message": "获取低库存预警成功"
    }


@router.get("/statistics/overview")
def get_materials_statistics(
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID"),
    factory_id: Optional[int] = Query(None, description="工厂ID"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """获取焊材统计。"""
    workspace_context = WorkspaceContext(
        workspace_type=workspace_type,
        user_id=current_user.id,
        company_id=company_id,
        factory_id=factory_id
    )
    service = MaterialService(db)
    return {
        "success": True,
        "data": service.get_statistics(current_user, workspace_context),
        "message": "获取焊材统计成功"
    }


# ==================== ????? ====================

@router.post("/stock-in", response_model=dict)
def material_stock_in(
    workspace_type: str = Query(..., description="??????personal/enterprise"),
    company_id: Optional[int] = Query(None, description="??ID?????????"),
    factory_id: Optional[int] = Query(None, description="??ID????"),
    material_id: int = Query(..., description="??ID"),
    quantity: float = Query(..., gt=0, description="????"),
    unit_price: Optional[float] = Query(None, description="??"),
    source: Optional[str] = Query(None, description="??"),
    batch_number: Optional[str] = Query(None, description="???"),
    warehouse: Optional[str] = Query(None, description="??"),
    storage_location: Optional[str] = Query(None, description="????"),
    notes: Optional[str] = Query(None, description="??"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    ????

    - **material_id**: ??ID
    - **quantity**: ?????????0?
    - **unit_price**: ??????
    - **source**: ??????
    - **batch_number**: ???????
    - **warehouse**: ??????
    - **storage_location**: ????????
    - **notes**: ??????
    """
    try:
        # ????????
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        # ?????
        service = MaterialService(db)
        result = service.stock_in(
            current_user=current_user,
            material_id=material_id,
            quantity=quantity,
            workspace_context=workspace_context,
            unit_price=unit_price,
            source=source,
            batch_number=batch_number,
            warehouse=warehouse,
            storage_location=storage_location,
            notes=notes
        )

        return {
            "success": True,
            "data": {
                "transaction_id": result["transaction"].id,
                "transaction_number": result["transaction"].transaction_number,
                "current_stock": result["material"].current_stock,
                "unit": result["material"].unit
            },
            "message": result["message"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/stock-out", response_model=dict)
def material_stock_out(
    workspace_type: str = Query(..., description="??????personal/enterprise"),
    company_id: Optional[int] = Query(None, description="??ID?????????"),
    factory_id: Optional[int] = Query(None, description="??ID????"),
    material_id: int = Query(..., description="??ID"),
    quantity: float = Query(..., gt=0, description="????"),
    destination: Optional[str] = Query(None, description="??"),
    reference_type: Optional[str] = Query(None, description="??????"),
    reference_id: Optional[int] = Query(None, description="????ID"),
    reference_number: Optional[str] = Query(None, description="?????"),
    notes: Optional[str] = Query(None, description="??"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    ????

    - **material_id**: ??ID
    - **quantity**: ?????????0?
    - **destination**: ??????
    - **reference_type**: ?????????????????
    - **reference_id**: ????ID????
    - **reference_number**: ?????????
    - **notes**: ??????
    """
    try:
        # ????????
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        # ?????
        service = MaterialService(db)
        result = service.stock_out(
            current_user=current_user,
            material_id=material_id,
            quantity=quantity,
            workspace_context=workspace_context,
            destination=destination,
            reference_type=reference_type,
            reference_id=reference_id,
            reference_number=reference_number,
            notes=notes
        )

        return {
            "success": True,
            "data": {
                "transaction_id": result["transaction"].id,
                "transaction_number": result["transaction"].transaction_number,
                "current_stock": result["material"].current_stock,
                "unit": result["material"].unit
            },
            "message": result["message"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/transactions", response_model=dict)
def get_material_transactions(
    workspace_type: str = Query(..., description="??????personal/enterprise"),
    company_id: Optional[int] = Query(None, description="??ID?????????"),
    factory_id: Optional[int] = Query(None, description="??ID????"),
    material_id: Optional[int] = Query(None, description="??ID?????????"),
    transaction_type: Optional[str] = Query(None, description="????????"),
    skip: int = Query(0, ge=0, description="?????"),
    limit: int = Query(20, ge=1, le=100, description="?????"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    ?????????

    - **material_id**: ??ID????????????????
    - **transaction_type**: ????????in/out/adjust/return/transfer/consume?
    - **skip**: ?????
    - **limit**: ?????
    """
    try:
        # ????????
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        # ?????
        service = MaterialService(db)
        result = service.get_transaction_list(
            current_user=current_user,
            workspace_context=workspace_context,
            material_id=material_id,
            transaction_type=transaction_type,
            skip=skip,
            limit=limit
        )

        return {
            "success": True,
            "data": result,
            "message": "?????????"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


"""Watch endpoints — with Supabase REST fallback."""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional
from app.db import get_db_or_rest
from app.models import WatchCore, WatchSpecState, WatchComment
from app.schemas import (
    WatchListResponse,
    WatchCoreResponse,
    WatchDetailResponse,
    WatchSpecStateResponse,
    WatchSpecsResponse,
    WatchSpecSourceResponse,
    WatchCommentResponse,
    CreateCommentRequest,
)
from app.auth import get_current_user, get_optional_user
from app.models import User

router = APIRouter(prefix="/watches", tags=["watches"])


@router.get("", response_model=WatchListResponse)
async def list_watches(
    query: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=1000),
    db_or_rest: tuple = Depends(get_db_or_rest),
):
    db, supabase = db_or_rest

    if db is not None:
        q = db.query(WatchCore)
        if query:
            search_term = f"%{query}%"
            q = q.filter(or_(
                WatchCore.product_name.ilike(search_term),
                WatchCore.brand.ilike(search_term),
                WatchCore.description.ilike(search_term),
            ))
        if brand:
            q = q.filter(WatchCore.brand.ilike(f"%{brand}%"))
        total = q.count()
        total_pages = (total + limit - 1) // limit
        watches = q.order_by(WatchCore.watch_id).offset((page - 1) * limit).limit(limit).all()
        return WatchListResponse(
            watches=[WatchCoreResponse.from_orm(w) for w in watches],
            total=total, page=page, limit=limit, total_pages=total_pages,
        )

    if supabase is not None:
        try:
            q = supabase.table("watch_core").select("*", count="exact")
            if query:
                # PostgREST wildcards use * not %
                pattern = f"*{query}*"
                q = q.or_(f"product_name.ilike.{pattern},brand.ilike.{pattern}")
            if brand:
                q = q.ilike("brand", f"*{brand}*")
            offset = (page - 1) * limit
            q = q.order("watch_id").range(offset, offset + limit - 1)
            r = q.execute()
        except Exception as e:
            print(f"[WATCHES] Supabase list_watches error: {e}")
            raise HTTPException(status_code=503, detail=f"Could not load watches: {e}")
        total = r.count if r.count is not None else len(r.data or [])
        total_pages = (total + limit - 1) // limit if total > 0 else 1
        watches = [
            WatchCoreResponse(
                watch_id=w["watch_id"], source=w.get("source", ""),
                product_url=w.get("product_url", ""),
                image_url=w.get("image_url"),
                brand=w.get("brand"), product_name=w.get("product_name", ""),
                sku=w.get("sku"), price_raw=w.get("price_raw"),
                price_value=w.get("price_value"), currency=w.get("currency", ""),
                description=w.get("description"),
                created_at=w.get("created_at"), updated_at=w.get("updated_at"),
            )
            for w in (r.data or [])
        ]
        return WatchListResponse(
            watches=watches, total=total, page=page, limit=limit, total_pages=total_pages,
        )

    raise HTTPException(status_code=503, detail="Database unavailable")


@router.get("/{watch_id}", response_model=WatchDetailResponse)
async def get_watch(watch_id: int, db_or_rest: tuple = Depends(get_db_or_rest)):
    db, supabase = db_or_rest

    if db is not None:
        watch = db.query(WatchCore).filter(WatchCore.watch_id == watch_id).first()
        if not watch:
            raise HTTPException(status_code=404, detail="Watch not found")
        specs = db.query(WatchSpecState).filter(WatchSpecState.watch_id == watch_id).all()
        comments_count = db.query(func.count(WatchComment.id)).filter(WatchComment.watch_id == watch_id).scalar()
        response = WatchDetailResponse.from_orm(watch)
        response.specs = [WatchSpecStateResponse.from_orm(s) for s in specs]
        response.comments_count = comments_count or 0
        return response

    if supabase is not None:
        r = supabase.table("watch_core").select("*").eq("watch_id", watch_id).execute()
        if not r.data:
            raise HTTPException(status_code=404, detail="Watch not found")
        w = r.data[0]
        sr = supabase.table("watch_spec_state").select("*").eq("watch_id", watch_id).execute()
        specs = [
            WatchSpecStateResponse(
                id=s["id"], watch_id=s["watch_id"], spec_key=s["spec_key"],
                spec_value=s.get("spec_value"), unit=s.get("unit"),
                source_type=s.get("source_type", ""), confidence=s.get("confidence"),
                resolved_at=s.get("resolved_at"), updated_at=s.get("updated_at"),
            )
            for s in (sr.data or [])
        ]
        return WatchDetailResponse(
            watch_id=w["watch_id"], source=w.get("source", ""),
            product_url=w.get("product_url", ""),
            image_url=w.get("image_url"), brand=w.get("brand"),
            product_name=w.get("product_name", ""), sku=w.get("sku"),
            price_raw=w.get("price_raw"), price_value=w.get("price_value"),
            currency=w.get("currency", ""), description=w.get("description"),
            created_at=w.get("created_at"), updated_at=w.get("updated_at"),
            specs=specs, comments_count=0,
        )

    raise HTTPException(status_code=503, detail="Database unavailable")


@router.get("/{watch_id}/specs", response_model=WatchSpecsResponse)
async def get_watch_specs(watch_id: int, db_or_rest: tuple = Depends(get_db_or_rest)):
    db, supabase = db_or_rest

    if db is not None:
        watch = db.query(WatchCore).filter(WatchCore.watch_id == watch_id).first()
        if not watch:
            raise HTTPException(status_code=404, detail="Watch not found")
        specs = db.query(WatchSpecState).filter(WatchSpecState.watch_id == watch_id).all()
        from app.models import WatchSpecSource
        sources_dict = {}
        for spec in specs:
            spec_sources = db.query(WatchSpecSource).filter(
                WatchSpecSource.watch_id == watch_id,
                WatchSpecSource.spec_key == spec.spec_key,
            ).all()
            sources_dict[spec.spec_key] = [WatchSpecSourceResponse.from_orm(s) for s in spec_sources]
        return WatchSpecsResponse(
            specs=[WatchSpecStateResponse.from_orm(s) for s in specs],
            sources=sources_dict,
        )

    if supabase is not None:
        sr = supabase.table("watch_spec_state").select("*").eq("watch_id", watch_id).execute()
        specs = [
            WatchSpecStateResponse(
                id=s["id"], watch_id=s["watch_id"], spec_key=s["spec_key"],
                spec_value=s.get("spec_value"), unit=s.get("unit"),
                source_type=s.get("source_type", ""), confidence=s.get("confidence"),
                resolved_at=s.get("resolved_at"), updated_at=s.get("updated_at"),
            )
            for s in (sr.data or [])
        ]
        return WatchSpecsResponse(specs=specs, sources={})

    raise HTTPException(status_code=503, detail="Database unavailable")


@router.get("/{watch_id}/comments", response_model=list[WatchCommentResponse])
async def get_watch_comments(watch_id: int, db_or_rest: tuple = Depends(get_db_or_rest)):
    db, supabase = db_or_rest

    if db is not None:
        watch = db.query(WatchCore).filter(WatchCore.watch_id == watch_id).first()
        if not watch:
            raise HTTPException(status_code=404, detail="Watch not found")
        comments = db.query(WatchComment).filter(
            WatchComment.watch_id == watch_id
        ).order_by(WatchComment.created_at.desc()).all()
        return [WatchCommentResponse.from_orm(c) for c in comments]

    if supabase is not None:
        r = supabase.table("watch_comments").select("*").eq("watch_id", watch_id).order("created_at", desc=True).execute()
        return [
            WatchCommentResponse(
                id=c["id"], watch_id=c["watch_id"], user_id=c["user_id"],
                content=c["content"], rating=c.get("rating"),
                created_at=c["created_at"], updated_at=c["updated_at"],
            )
            for c in (r.data or [])
        ]

    raise HTTPException(status_code=503, detail="Database unavailable")


@router.post("/{watch_id}/comments", response_model=WatchCommentResponse)
async def create_comment(
    watch_id: int,
    request: CreateCommentRequest,
    db_or_rest: tuple = Depends(get_db_or_rest),
    current_user: User = Depends(get_current_user),
):
    db, supabase = db_or_rest

    if db is not None:
        watch = db.query(WatchCore).filter(WatchCore.watch_id == watch_id).first()
        if not watch:
            raise HTTPException(status_code=404, detail="Watch not found")
        comment = WatchComment(
            watch_id=watch_id, user_id=current_user.id,
            content=request.content, rating=request.rating,
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return WatchCommentResponse.from_orm(comment)

    if supabase is not None:
        r = supabase.table("watch_comments").insert({
            "watch_id": watch_id, "user_id": str(current_user.id),
            "content": request.content, "rating": request.rating,
        }).execute()
        if r.data:
            c = r.data[0]
            return WatchCommentResponse(
                id=c["id"], watch_id=c["watch_id"], user_id=c["user_id"],
                content=c["content"], rating=c.get("rating"),
                created_at=c["created_at"], updated_at=c["updated_at"],
            )

    raise HTTPException(status_code=503, detail="Database unavailable")

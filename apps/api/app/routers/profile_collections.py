from __future__ import annotations

import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import get_current_user
from app.models import User, UserCollection, UserCollectionItem
from app.schemas import (
    CreateUserCollectionRequest,
    ProfileMeResponse,
    UserCollectionResponse,
    UserCollectionItemResponse,
)

from app.services.watch_ingestion import start_background_processing


router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=ProfileMeResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return ProfileMeResponse.from_orm(current_user)


def _get_upload_dir() -> Path:
    # apps/api/static/uploads
    uploads_dir = Path(__file__).resolve().parents[2] / "static" / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    return uploads_dir


def _save_upload(image_file: UploadFile) -> str:
    upload_dir = _get_upload_dir()
    ext = Path(image_file.filename or "upload.jpg").suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        ext = ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = upload_dir / filename

    content = image_file.file.read()
    with open(dest, "wb") as f:
        f.write(content)

    # Browser path served by FastAPI static mount at `/static`
    return f"/static/uploads/{filename}"


@router.get("/collections", response_model=List[UserCollectionResponse])
def list_my_collections(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    collections = db.query(UserCollection).filter(UserCollection.user_id == current_user.id).order_by(UserCollection.created_at.desc()).all()
    return [UserCollectionResponse.from_orm(c) for c in collections]


@router.post("/collections", response_model=UserCollectionResponse)
def create_collection(
    payload: CreateUserCollectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = UserCollection(user_id=current_user.id, name=payload.name, description=payload.description)
    db.add(c)
    db.commit()
    db.refresh(c)
    return UserCollectionResponse.from_orm(c)


@router.get("/collections/{collection_id}", response_model=UserCollectionResponse)
def get_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.query(UserCollection).filter(UserCollection.id == collection_id, UserCollection.user_id == current_user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Collection not found")
    return UserCollectionResponse.from_orm(c)


@router.get("/collections/{collection_id}/items", response_model=List[UserCollectionItemResponse])
def list_collection_items(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    collection = (
        db.query(UserCollection)
        .filter(UserCollection.id == collection_id, UserCollection.user_id == current_user.id)
        .first()
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    items = (
        db.query(UserCollectionItem)
        .filter(UserCollectionItem.collection_id == collection_id)
        .order_by(UserCollectionItem.created_at.desc())
        .all()
    )
    return [UserCollectionItemResponse.from_orm(i) for i in items]


@router.post("/collections/{collection_id}/items", response_model=UserCollectionItemResponse)
def add_watch_to_collection(
    collection_id: int,
    source: str = Form(...),
    product_url: str = Form(...),
    product_name: str = Form(...),
    sku: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    image_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    collection = db.query(UserCollection).filter(UserCollection.id == collection_id, UserCollection.user_id == current_user.id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    image_url = _save_upload(image_file)

    item = UserCollectionItem(
        collection_id=collection_id,
        status="processing_ai",
        sku=sku,
        source=source,
        product_url=product_url,
        product_name=product_name,
        brand=brand,
        image_url=image_url,
        watch_id=None,
        suggestion_id=None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    # Start background processing immediately
    start_background_processing(item.id)

    return UserCollectionItemResponse.from_orm(item)


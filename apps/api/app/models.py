"""SQLAlchemy models for Watch Community Platform."""
from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, CheckConstraint, UniqueConstraint, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    supabase_user_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    username = Column(String(100))
    display_name = Column(String(200))
    avatar_url = Column(Text)
    is_admin = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class WatchCore(Base):
    __tablename__ = "watch_core"

    watch_id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(255), nullable=False)
    product_url = Column(Text, nullable=False)
    image_url = Column(Text)
    brand = Column(String(255))
    product_name = Column(String(500), nullable=False)
    sku = Column(String(255))
    price_raw = Column(String(100))
    price_value = Column(Numeric(12, 2))
    currency = Column(String(3), default="TRY")
    description = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("currency IN ('TRY', 'USD', 'EUR', 'GBP')", name="check_currency"),
    )


class WatchSpecState(Base):
    __tablename__ = "watch_spec_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    watch_id = Column(Integer, ForeignKey("watch_core.watch_id", ondelete="CASCADE"), nullable=False)
    spec_key = Column(String(100), nullable=False)
    spec_value = Column(Text)
    unit = Column(String(50))
    source_type = Column(String(50), nullable=False)
    confidence = Column(Numeric(3, 2))
    resolved_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("watch_id", "spec_key", name="uq_watch_spec_state"),
        CheckConstraint(
            "source_type IN ('official', 'community_verified', 'ai_estimated', 'disputed', 'unknown')",
            name="check_source_type",
        ),
    )


class WatchSpecSource(Base):
    __tablename__ = "watch_spec_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    watch_id = Column(Integer, ForeignKey("watch_core.watch_id", ondelete="CASCADE"), nullable=False)
    spec_key = Column(String(100), nullable=False)
    spec_value = Column(Text, nullable=False)
    unit = Column(String(50))
    source_type = Column(String(50), nullable=False)
    source_name = Column(String(255), nullable=False)
    source_url = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "watch_id", "spec_key", "source_type", "source_name", "spec_value",
            name="uq_watch_spec_sources",
        ),
        CheckConstraint(
            "source_type IN ('official', 'scraper', 'community', 'ai')",
            name="check_spec_source_type",
        ),
    )


class WatchComment(Base):
    __tablename__ = "watch_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    watch_id = Column(Integer, ForeignKey("watch_core.watch_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    rating = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating"),
    )

    user = relationship("User", lazy="joined")


class WatchUserContribution(Base):
    __tablename__ = "watch_user_contributions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    watch_id = Column(Integer, ForeignKey("watch_core.watch_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    spec_key = Column(String(100), nullable=False)
    proposed_value = Column(Text, nullable=False)
    unit = Column(String(50))
    note = Column(Text)
    evidence_url = Column(Text)
    status = Column(String(50), default="pending")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="check_contribution_status",
        ),
    )

    user = relationship("User", lazy="joined")


class WatchContributionVote(Base):
    __tablename__ = "watch_contribution_votes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contribution_id = Column(
        Integer, ForeignKey("watch_user_contributions.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vote_type = Column(String(20), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("contribution_id", "user_id", name="uq_contribution_vote"),
        CheckConstraint("vote_type IN ('confirm', 'reject')", name="check_vote_type"),
    )


class WatchAIEstimation(Base):
    __tablename__ = "watch_ai_estimations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    watch_id = Column(Integer, ForeignKey("watch_core.watch_id", ondelete="CASCADE"), nullable=False)
    spec_key = Column(String(100), nullable=False)
    estimated_value = Column(Text, nullable=False)
    unit = Column(String(50))
    confidence = Column(Numeric(3, 2), nullable=False)
    model_name = Column(String(255), nullable=False)
    model_version = Column(String(100))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("watch_id", "spec_key", "model_name", name="uq_ai_estimation"),
        CheckConstraint(
            "confidence >= 0.00 AND confidence <= 1.00",
            name="check_confidence",
        ),
    )


class WatchEmbedding(Base):
    __tablename__ = "watch_embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    watch_id = Column(Integer, ForeignKey("watch_core.watch_id", ondelete="CASCADE"), nullable=False)
    embedding = Column(Text)  # Stored as text, converted to/from vector in queries
    text_payload = Column(Text)
    model_name = Column(String(255), nullable=False, default="siglip")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("watch_id", "model_name", name="uq_watch_embedding"),
    )


class UserCollection(Base):
    __tablename__ = "user_collections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", lazy="joined")


class WatchSuggestion(Base):
    __tablename__ = "watch_suggestions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False)

    sku = Column(Text)
    source = Column(Text)
    product_url = Column(Text)
    product_name = Column(Text)
    brand = Column(Text)
    image_url = Column(Text)

    ai_output_json = Column(JSONB)
    admin_notes = Column(Text)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", lazy="joined")


class UserCollectionItem(Base):
    __tablename__ = "user_collection_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_id = Column(Integer, ForeignKey("user_collections.id", ondelete="CASCADE"), nullable=False)

    status = Column(String(50), nullable=False)

    sku = Column(Text)
    source = Column(Text)
    product_url = Column(Text)
    product_name = Column(Text)
    brand = Column(Text)
    image_url = Column(Text)

    watch_id = Column(Integer, ForeignKey("watch_core.watch_id", ondelete="SET NULL"), nullable=True)
    suggestion_id = Column(Integer, ForeignKey("watch_suggestions.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


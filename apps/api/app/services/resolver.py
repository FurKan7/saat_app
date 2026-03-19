"""Resolver service to determine best spec value based on priority rules."""
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from app.models import (
    WatchCore,
    WatchSpecState,
    WatchSpecSource,
    WatchUserContribution,
    WatchContributionVote,
    WatchAIEstimation,
)


def resolve_watch_specs(watch_id: int, db: Session) -> dict:
    """
    Resolve watch specs based on priority:
    1. Official (from watch_spec_sources with source_type='official')
    2. Community verified (>=3 confirms, median value stable)
    3. AI estimated (confidence >= 0.7)
    4. Unknown
    """
    watch = db.query(WatchCore).filter(WatchCore.watch_id == watch_id).first()
    if not watch:
        raise ValueError(f"Watch {watch_id} not found")

    # Get all unique spec keys from sources
    spec_keys = (
        db.query(WatchSpecSource.spec_key)
        .filter(WatchSpecSource.watch_id == watch_id)
        .distinct()
        .all()
    )
    spec_keys = [s[0] for s in spec_keys]

    resolved_count = 0

    for spec_key in spec_keys:
        resolved = resolve_single_spec(watch_id, spec_key, db)
        if resolved:
            resolved_count += 1

    return {"resolved_specs": resolved_count, "total_specs": len(spec_keys)}


def resolve_single_spec(watch_id: int, spec_key: str, db: Session) -> bool:
    """Resolve a single spec key."""
    # Priority 1: Check for official source
    official_source = (
        db.query(WatchSpecSource)
        .filter(
            WatchSpecSource.watch_id == watch_id,
            WatchSpecSource.spec_key == spec_key,
            WatchSpecSource.source_type == "official",
        )
        .first()
    )

    if official_source:
        update_spec_state(
            db, watch_id, spec_key, official_source.spec_value, official_source.unit, "official"
        )
        return True

    # Priority 2: Check for community verified (>=3 confirms)
    contributions = (
        db.query(WatchUserContribution)
        .filter(
            WatchUserContribution.watch_id == watch_id,
            WatchUserContribution.spec_key == spec_key,
            WatchUserContribution.status == "pending",
        )
        .all()
    )

    for contrib in contributions:
        confirm_count = (
            db.query(func.count(WatchContributionVote.id))
            .filter(
                WatchContributionVote.contribution_id == contrib.id,
                WatchContributionVote.vote_type == "confirm",
            )
            .scalar()
        ) or 0

        reject_count = (
            db.query(func.count(WatchContributionVote.id))
            .filter(
                WatchContributionVote.contribution_id == contrib.id,
                WatchContributionVote.vote_type == "reject",
            )
            .scalar()
        ) or 0

        # If >=3 confirms and confirms > rejects, use this value
        if confirm_count >= 3 and confirm_count > reject_count:
            update_spec_state(
                db, watch_id, spec_key, contrib.proposed_value, contrib.unit, "community_verified"
            )
            # Also create a source record
            source = WatchSpecSource(
                watch_id=watch_id,
                spec_key=spec_key,
                spec_value=contrib.proposed_value,
                unit=contrib.unit,
                source_type="community",
                source_name=f"user_{contrib.user_id}",
                source_url=contrib.evidence_url,
            )
            db.add(source)
            db.commit()
            return True

    # Priority 3: Check for AI estimation with confidence >= 0.7
    ai_estimation = (
        db.query(WatchAIEstimation)
        .filter(
            WatchAIEstimation.watch_id == watch_id,
            WatchAIEstimation.spec_key == spec_key,
            WatchAIEstimation.confidence >= Decimal("0.7"),
        )
        .order_by(WatchAIEstimation.confidence.desc())
        .first()
    )

    if ai_estimation:
        update_spec_state(
            db,
            watch_id,
            spec_key,
            ai_estimation.estimated_value,
            ai_estimation.unit,
            "ai_estimated",
            ai_estimation.confidence,
        )
        return True

    # Priority 4: Unknown
    update_spec_state(db, watch_id, spec_key, None, None, "unknown")
    return False


def update_spec_state(
    db: Session,
    watch_id: int,
    spec_key: str,
    spec_value: str | None,
    unit: str | None,
    source_type: str,
    confidence: Decimal | None = None,
):
    """Update or create watch_spec_state record."""
    existing = (
        db.query(WatchSpecState)
        .filter(WatchSpecState.watch_id == watch_id, WatchSpecState.spec_key == spec_key)
        .first()
    )

    if existing:
        existing.spec_value = spec_value
        existing.unit = unit
        existing.source_type = source_type
        existing.confidence = confidence
    else:
        new_state = WatchSpecState(
            watch_id=watch_id,
            spec_key=spec_key,
            spec_value=spec_value,
            unit=unit,
            source_type=source_type,
            confidence=confidence,
        )
        db.add(new_state)

    db.commit()


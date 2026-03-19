"""Contribution and voting endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import get_db
from app.models import (
    WatchCore,
    WatchUserContribution,
    WatchContributionVote,
    User,
)
from app.schemas import (
    WatchUserContributionResponse,
    CreateContributionRequest,
    VoteRequest,
    UserResponse,
)
from app.auth import get_current_user

router = APIRouter(prefix="/watches", tags=["contributions"])


@router.post("/{watch_id}/contributions", response_model=WatchUserContributionResponse)
async def create_contribution(
    watch_id: int,
    request: CreateContributionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a contribution for a watch spec."""
    watch = db.query(WatchCore).filter(WatchCore.watch_id == watch_id).first()
    if not watch:
        raise HTTPException(status_code=404, detail="Watch not found")

    contribution = WatchUserContribution(
        watch_id=watch_id,
        user_id=current_user.id,
        spec_key=request.spec_key,
        proposed_value=request.proposed_value,
        unit=request.unit,
        note=request.note,
        evidence_url=request.evidence_url,
    )
    db.add(contribution)
    db.commit()
    db.refresh(contribution)

    # Get vote counts
    votes = get_contribution_votes(db, contribution.id)
    
    response = WatchUserContributionResponse.from_orm(contribution)
    response.user = UserResponse.from_orm(current_user)
    response.votes = votes

    return response


@router.get("/{watch_id}/contributions", response_model=list[WatchUserContributionResponse])
async def get_watch_contributions(
    watch_id: int,
    db: Session = Depends(get_db),
):
    """Get all contributions for a watch."""
    watch = db.query(WatchCore).filter(WatchCore.watch_id == watch_id).first()
    if not watch:
        raise HTTPException(status_code=404, detail="Watch not found")

    contributions = (
        db.query(WatchUserContribution)
        .filter(WatchUserContribution.watch_id == watch_id)
        .order_by(WatchUserContribution.created_at.desc())
        .all()
    )

    result = []
    for contrib in contributions:
        votes = get_contribution_votes(db, contrib.id)
        response = WatchUserContributionResponse.from_orm(contrib)
        response.user = UserResponse.from_orm(contrib.user) if contrib.user else None
        response.votes = votes
        result.append(response)

    return result


def get_contribution_votes(db: Session, contribution_id: int) -> dict:
    """Get vote counts for a contribution."""
    confirms = (
        db.query(func.count(WatchContributionVote.id))
        .filter(
            WatchContributionVote.contribution_id == contribution_id,
            WatchContributionVote.vote_type == "confirm",
        )
        .scalar()
    ) or 0

    rejects = (
        db.query(func.count(WatchContributionVote.id))
        .filter(
            WatchContributionVote.contribution_id == contribution_id,
            WatchContributionVote.vote_type == "reject",
        )
        .scalar()
    ) or 0

    return {"confirms": confirms, "rejects": rejects, "user_vote": None}


@router.post("/contributions/{contribution_id}/vote", response_model=dict)
async def vote_on_contribution(
    contribution_id: int,
    request: VoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Vote on a contribution (confirm or reject)."""
    contribution = (
        db.query(WatchUserContribution)
        .filter(WatchUserContribution.id == contribution_id)
        .first()
    )
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribution not found")

    # Check if user already voted
    existing_vote = (
        db.query(WatchContributionVote)
        .filter(
            WatchContributionVote.contribution_id == contribution_id,
            WatchContributionVote.user_id == current_user.id,
        )
        .first()
    )

    if existing_vote:
        # Update existing vote
        existing_vote.vote_type = request.vote_type
    else:
        # Create new vote
        vote = WatchContributionVote(
            contribution_id=contribution_id,
            user_id=current_user.id,
            vote_type=request.vote_type,
        )
        db.add(vote)

    db.commit()

    votes = get_contribution_votes(db, contribution_id)
    # Get user's vote
    user_vote = (
        db.query(WatchContributionVote)
        .filter(
            WatchContributionVote.contribution_id == contribution_id,
            WatchContributionVote.user_id == current_user.id,
        )
        .first()
    )
    if user_vote:
        votes["user_vote"] = user_vote.vote_type

    return {"message": "Vote recorded", "votes": votes}


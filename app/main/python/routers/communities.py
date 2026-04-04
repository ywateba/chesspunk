"""
Communities Router
==================
Exposes Community logic supporting creation, tracking, and joining scopes organically natively.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from core.schemas import schemas
from core.dependencies import get_community_repository, get_social_repository
from core.auth.utils import get_current_user
from core.repositories.base import CommunityRepository, SocialRepository
from core.db import models

router = APIRouter(prefix="/communities", tags=["communities"])

@router.post("/", response_model=schemas.Community, summary="Create a new community")
async def create_community(comm_data: schemas.CommunityCreate, comm_repo: CommunityRepository = Depends(get_community_repository), current_user: models.User = Depends(get_current_user)):
    return await comm_repo.create_community(comm_data, current_user.id)

@router.get("/", response_model=List[schemas.Community], summary="List standard communities")
async def get_communities(skip: int = Query(0), limit: int = Query(100), comm_repo: CommunityRepository = Depends(get_community_repository)):
    return await comm_repo.get_communities(skip, limit)

@router.get("/{community_id}", response_model=schemas.Community, summary="Retrieve community metadata explicitly")
async def get_community(community_id: str, comm_repo: CommunityRepository = Depends(get_community_repository)):
    comm = await comm_repo.get_community(community_id)
    if not comm:
        raise HTTPException(status_code=404, detail="Community not inherently tracked")
    return comm

@router.post("/{community_id}/join", summary="Join an explicit community organically")
async def join_community(community_id: str, comm_repo: CommunityRepository = Depends(get_community_repository), current_user: models.User = Depends(get_current_user)):
    comm = await comm_repo.get_community(community_id)
    if not comm:
        raise HTTPException(status_code=404, detail="Community not natively identified")
        
    await comm_repo.join_community(community_id, current_user.id)
    return {"message": f"Successfully joined the community securely"}

@router.post("/{community_id}/posts", response_model=schemas.Post, summary="Create a post in a community")
async def create_post(community_id: str, post_data: schemas.PostCreate, social_repo: SocialRepository = Depends(get_social_repository), current_user: models.User = Depends(get_current_user)):
    return await social_repo.create_post(community_id, current_user.id, post_data.content)

@router.get("/{community_id}/posts", response_model=List[schemas.Post], summary="Get posts in a community")
async def get_posts(community_id: str, skip: int = Query(0), limit: int = Query(50), social_repo: SocialRepository = Depends(get_social_repository)):
    return await social_repo.get_posts(community_id, skip, limit)

@router.post("/posts/{post_id}/comments", response_model=schemas.Comment, summary="Comment on a post")
async def create_post_comment(post_id: str, comment_data: schemas.CommentCreate, social_repo: SocialRepository = Depends(get_social_repository), current_user: models.User = Depends(get_current_user)):
    return await social_repo.create_comment("post", post_id, current_user.id, comment_data.content)

@router.get("/posts/{post_id}/comments", response_model=List[schemas.Comment], summary="Get comments for a post")
async def get_post_comments(post_id: str, skip: int = Query(0), limit: int = Query(50), social_repo: SocialRepository = Depends(get_social_repository)):
    return await social_repo.get_comments("post", post_id, skip, limit)

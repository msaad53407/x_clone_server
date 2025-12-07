"""
Collaborative Filtering Recommender Service for personalized feed.
Adapted from user-provided algorithm to work with our schema.

Uses:
- Likes (weight: 1.0)
- Comments (weight: 2.0)
- Bookmarks (weight: 2.5)
- Follows (weight: 3.0 - for user recommendations)
"""

import uuid
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bookmark import Bookmark
from app.models.comment import Comment
from app.models.like import Like


class FeedRecommender:
    """
    Collaborative Filtering based recommender for personalized tweet feed.
    Uses user-user and item-item similarity based on interactions.
    """
    
    def __init__(self, interaction_weights: dict[str, float] | None = None):
        """
        Initialize recommender with custom weights for different interactions.
        
        Args:
            interaction_weights: Weights for each interaction type
        """
        self.interaction_weights = interaction_weights or {
            'like': 1.0,
            'comment': 2.0,
            'bookmark': 2.5,
        }
        
        self.user_item_matrix: csr_matrix | None = None
        self.user_similarity_matrix: Any = None
        self.item_similarity_matrix: Any = None
        self.user_id_map: dict[uuid.UUID, int] = {}
        self.item_id_map: dict[uuid.UUID, int] = {}
        self.reverse_user_map: dict[int, uuid.UUID] = {}
        self.reverse_item_map: dict[int, uuid.UUID] = {}
    
    async def load_interaction_data(self, db: AsyncSession) -> pd.DataFrame:
        """
        Load all interaction data from database.
        
        Args:
            db: Database session
            
        Returns:
            DataFrame with columns ['user_id', 'item_id', 'weight']
        """
        interactions = []
        
        # Load likes
        likes_result = await db.execute(select(Like.user_id, Like.tweet_id))
        likes = likes_result.all()
        for user_id, tweet_id in likes:
            interactions.append({
                'user_id': str(user_id),
                'item_id': str(tweet_id),
                'weight': self.interaction_weights['like'],
            })
        
        # Load comments
        comments_result = await db.execute(select(Comment.user_id, Comment.tweet_id))
        comments = comments_result.all()
        for user_id, tweet_id in comments:
            interactions.append({
                'user_id': str(user_id),
                'item_id': str(tweet_id),
                'weight': self.interaction_weights['comment'],
            })
        
        # Load bookmarks
        bookmarks_result = await db.execute(select(Bookmark.user_id, Bookmark.tweet_id))
        bookmarks = bookmarks_result.all()
        for user_id, tweet_id in bookmarks:
            interactions.append({
                'user_id': str(user_id),
                'item_id': str(tweet_id),
                'weight': self.interaction_weights['bookmark'],
            })
        
        if not interactions:
            return pd.DataFrame(columns=['user_id', 'item_id', 'weight'])
        
        df = pd.DataFrame(interactions)
        
        # Aggregate by user-item pair (sum weights for multiple interactions)
        aggregated = df.groupby(['user_id', 'item_id'])['weight'].sum().reset_index()
        
        return aggregated
    
    def build_matrices(self, interactions_df: pd.DataFrame) -> bool:
        """
        Build user-item and similarity matrices.
        
        Args:
            interactions_df: DataFrame with ['user_id', 'item_id', 'weight']
            
        Returns:
            True if matrices were built, False if not enough data
        """
        if interactions_df.empty:
            return False
        
        # Create mappings
        unique_users = interactions_df['user_id'].unique()
        unique_items = interactions_df['item_id'].unique()
        
        if len(unique_users) < 2 or len(unique_items) < 2:
            return False
        
        self.user_id_map = {uid: idx for idx, uid in enumerate(unique_users)}
        self.item_id_map = {iid: idx for idx, iid in enumerate(unique_items)}
        self.reverse_user_map = {idx: uid for uid, idx in self.user_id_map.items()}
        self.reverse_item_map = {idx: iid for iid, idx in self.item_id_map.items()}
        
        # Map to indices
        interactions_df = interactions_df.copy()
        interactions_df['user_idx'] = interactions_df['user_id'].map(self.user_id_map)
        interactions_df['item_idx'] = interactions_df['item_id'].map(self.item_id_map)
        
        # Build sparse matrix
        n_users = len(unique_users)
        n_items = len(unique_items)
        
        self.user_item_matrix = csr_matrix(
            (interactions_df['weight'].values,
             (interactions_df['user_idx'].values, interactions_df['item_idx'].values)),
            shape=(n_users, n_items)
        )
        
        # Compute similarity matrices
        self.user_similarity_matrix = cosine_similarity(self.user_item_matrix, dense_output=False)
        self.item_similarity_matrix = cosine_similarity(self.user_item_matrix.T, dense_output=False)
        
        return True
    
    def get_recommendations(
        self,
        user_id: uuid.UUID,
        n_recommendations: int = 20,
        filter_interacted: bool = True,
    ) -> list[uuid.UUID]:
        """
        Get recommended tweet IDs for a user using hybrid collaborative filtering.
        
        Args:
            user_id: User UUID
            n_recommendations: Number of recommendations
            filter_interacted: Filter out tweets user has already interacted with
            
        Returns:
            List of recommended tweet UUIDs
        """
        user_id_str = str(user_id)
        
        if user_id_str not in self.user_id_map:
            return []
        
        if self.user_item_matrix is None:
            return []
        
        user_idx = self.user_id_map[user_id_str]
        
        # User-based recommendations
        user_scores = self._get_user_based_scores(user_idx)
        
        # Item-based recommendations
        item_scores = self._get_item_based_scores(user_idx)
        
        # Combine scores (hybrid approach)
        combined_scores = (user_scores * 0.5) + (item_scores * 0.5)
        
        # Filter interacted items
        if filter_interacted:
            user_interactions = self.user_item_matrix[user_idx].toarray().flatten()
            combined_scores[user_interactions > 0] = -np.inf
        
        # Get top N
        top_indices = np.argsort(combined_scores)[-n_recommendations:][::-1]
        
        recommendations = []
        for idx in top_indices:
            if combined_scores[idx] > 0:
                tweet_id_str = self.reverse_item_map.get(idx)
                if tweet_id_str:
                    try:
                        recommendations.append(uuid.UUID(tweet_id_str))
                    except ValueError:
                        continue
        
        return recommendations
    
    def _get_user_based_scores(self, user_idx: int) -> np.ndarray:
        """Calculate scores using user-based collaborative filtering."""
        user_similarities = self.user_similarity_matrix[user_idx].toarray().flatten()
        user_similarities[user_idx] = 0
        
        k_similar = min(50, len(user_similarities))
        similar_indices = np.argsort(user_similarities)[-k_similar:]
        
        similar_matrix = self.user_item_matrix[similar_indices]
        weights = user_similarities[similar_indices].reshape(-1, 1)
        
        scores = (similar_matrix.multiply(weights)).sum(axis=0)
        return np.asarray(scores).flatten()
    
    def _get_item_based_scores(self, user_idx: int) -> np.ndarray:
        """Calculate scores using item-based collaborative filtering."""
        user_interactions = self.user_item_matrix[user_idx].toarray().flatten()
        interacted_items = np.where(user_interactions > 0)[0]
        
        if len(interacted_items) == 0:
            return np.zeros(self.user_item_matrix.shape[1])
        
        scores = np.zeros(self.user_item_matrix.shape[1])
        
        for item_idx in interacted_items:
            item_sims = self.item_similarity_matrix[item_idx].toarray().flatten()
            item_sims[item_idx] = 0
            weighted_sims = item_sims * user_interactions[item_idx]
            scores += weighted_sims
        
        return scores


# Singleton instance for caching recommendations
_recommender_instance: FeedRecommender | None = None


def get_recommender() -> FeedRecommender:
    """Get or create the recommender singleton."""
    global _recommender_instance
    if _recommender_instance is None:
        _recommender_instance = FeedRecommender()
    return _recommender_instance


async def refresh_recommender(db: AsyncSession) -> bool:
    """
    Refresh the recommender with latest data.
    Should be called periodically (e.g., every 5-15 minutes).
    
    Returns:
        True if recommender was successfully refreshed
    """
    recommender = get_recommender()
    interactions = await recommender.load_interaction_data(db)
    return recommender.build_matrices(interactions)

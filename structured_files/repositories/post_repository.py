# ======================================
# repositories/post_repository.py
# ======================================
from datetime import datetime
import uuid
from typing import List, Optional
from supabase import Client
import re

STORAGE_BUCKET = "users"


class PostRepository:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    # ======================================================
    # CREATE POST + IMAGES
    # ======================================================
    async def create_post(self, user_id: str, post_title: str, content: str, files: Optional[List] = None):
        post_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        # insert post
        self.supabase.table("posts").insert({
            "post_id": post_id,
            "post_title": post_title,
            "content": content,
            "user_id": user_id,
            "created_at": timestamp,
            "modified_at": timestamp,
            "created_by": user_id,
            "modified_by": user_id
        }).execute()

        image_urls = []
        position_index = 0

        if files:
            for img in files:
                ext = img.filename.split(".")[-1]
                image_id = str(uuid.uuid4())
                filename = f"{post_id}_{image_id}.{ext}"
                file_path = f"{user_id}/post_img/{filename}"

                file_bytes = await img.read()

                # Upload to storage
                self.supabase.storage.from_(STORAGE_BUCKET).upload(
                    file_path,
                    file_bytes,
                    {"content-type": img.content_type}
                )

                public_url = self.supabase.storage.from_(STORAGE_BUCKET).get_public_url(file_path)
                image_urls.append(public_url)

                # Insert into DB
                self.supabase.table("post_images").insert({
                    "image_id": image_id,
                    "post_id": post_id,
                    "image_url": public_url,
                    "position": position_index
                }).execute()

                position_index += 1

        return post_id, image_urls

    # ======================================================
    # UPDATE POST
    # ======================================================
    def update_post(self, post_id: str, user_id: str, post_title: str, content: str):
        exists = self.supabase.table("posts") \
            .select("post_id") \
            .eq("post_id", post_id) \
            .eq("user_id", user_id) \
            .execute()

        if not exists.data:
            return False

        self.supabase.table("posts").update({
            "post_title": post_title,
            "content": content,
            "modified_at": datetime.utcnow().isoformat(),
            "modified_by": user_id
        }).eq("post_id", post_id).execute()
        return True

    # ======================================================
    # DELETE POST
    # ======================================================
    def delete_post(self, post_id: str, user_id: str):

        post = self.supabase.table("posts") \
            .select("*") \
            .eq("post_id", post_id) \
            .eq("user_id", user_id) \
            .execute()

        if not post.data:
            return False

        # Get images
        img_rows = self.supabase.table("post_images").select("*").eq("post_id", post_id).execute()

        delete_filepaths = []

        for img in img_rows.data:
            image_url = img["image_url"]

            cleaned = image_url.split('?')[0]
            file_path = cleaned.split(f"{STORAGE_BUCKET}/")[-1]
            delete_filepaths.append(file_path)

        if delete_filepaths:
            self.supabase.storage.from_(STORAGE_BUCKET).remove(delete_filepaths)

        # delete all post related
        self.supabase.table("post_images").delete().eq("post_id", post_id).execute()
        self.supabase.table("comments").delete().eq("post_id", post_id).execute()
        self.supabase.table("likes").delete().eq("post_id", post_id).execute()
        self.supabase.table("posts").delete().eq("post_id", post_id).execute()

        return True

    # ======================================================
    # GET SINGLE POST
    # ======================================================
    def get_post(self, post_id: str, user_id: str):

        post = self.supabase.table("posts") \
            .select("*") \
            .eq("post_id", post_id) \
            .execute()

        if not post.data:
            return None

        post_data = post.data[0]

        # images
        img_rows = self.supabase.table("post_images") \
            .select("image_url, position") \
            .eq("post_id", post_id) \
            .order("position", desc=False) \
            .execute()

        images = []
        if img_rows.data:
            for img in img_rows.data:
                images.append({
                    "image_url": img["image_url"],
                    "position": img["position"]
                })

        # likes count
        likes = self.supabase.table("likes") \
            .select("like_id") \
            .eq("post_id", post_id) \
            .execute()

        # comments count
        comments = self.supabase.table("comments") \
            .select("comment_id") \
            .eq("post_id", post_id) \
            .execute()

        # user liked?
        user_like = self.supabase.table("likes") \
            .select("like_id") \
            .eq("post_id", post_id) \
            .eq("user_id", user_id) \
            .execute()

        return {
            "post": post_data,
            "images": images,
            "counts": {
                "likes": len(likes.data), 
                "comments": len(comments.data)
            },
            "user_actions": {
                "liked_by_user": True if user_like.data else False
            }
        }

from ..config.supabase_config import supabase


class PostImagesRepository:

    # insert a single image
    @staticmethod
    def insert_image(image_id: str, post_id: str, url: str, position: int):
        return supabase.table("post_images").insert({
            "image_id": image_id,
            "post_id": post_id,
            "image_url": url,
            "position": position
        }).execute()

    # insert multiple images at once
    @staticmethod
    def insert_images(images: list):
        # images = [{image_id, post_id, image_url, position}, ...]
        return supabase.table("post_images").insert(images).execute()

    # get images for post (ordered)
    @staticmethod
    def get_images(post_id: str):
        return supabase.table("post_images")\
            .select("image_url, position")\
            .eq("post_id", post_id)\
            .order("position", desc=False)\
            .execute()

    # delete all images for post
    @staticmethod
    def delete_images_for_post(post_id: str):
        return supabase.table("post_images")\
            .delete()\
            .eq("post_id", post_id)\
            .execute()

    # delete one image by image_id
    @staticmethod
    def delete_image(image_id: str):
        return supabase.table("post_images")\
            .delete()\
            .eq("image_id", image_id)\
            .execute()

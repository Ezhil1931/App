from ..config.supabase_config import supabase
from datetime import datetime

class UserTokensRepository:

    @staticmethod
    async def add_token(user_id: str, device_name: str, device_token: str, fcm_token: str):
        """
        Insert new device + token for user.
        For example: iPhone / Chrome / Windows PC / Redmi Phone
        """

        data = {
            "user_id": user_id,
            "device_name": device_name,
            "device_token": device_token,
            "fcm_token": fcm_token,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": user_id
        }

        response = supabase.table("user_tokens").insert(data).execute()
        return response.data

    @staticmethod
    async def get_tokens_by_user(user_id: str):
        """
        Get all device records (multiple)
        Useful to send push notifications to ALL devices
        """

        response = supabase.table("user_tokens").select("*").eq("user_id", user_id).execute()
        return response.data

    @staticmethod
    async def get_token_by_device(device_token: str):
        """
        Get a specific device profile from device token
        """

        response = supabase.table("user_tokens").select("*").eq("device_token", device_token).execute()
        return response.data

    @staticmethod
    async def update_fcm_token(device_token: str, new_fcm_token: str, user_id: str):
        """
        Update FCM token for a specific device
        """

        response = supabase.table("user_tokens").update({
            "fcm_token": new_fcm_token,
            "modified_at": datetime.utcnow().isoformat(),
            "modified_by": user_id
        }).eq("device_token", device_token).execute()

        return response.data

    @staticmethod
    async def delete_token(device_token: str):
        """
        Delete single device token (user logout from one device)
        """

        response = supabase.table("user_tokens").delete().eq("device_token", device_token).execute()
        return response.data

    @staticmethod
    async def delete_all_tokens_for_user(user_id: str):
        """
        Remove all active sessions for that user
        Used when user resets password / suspicious login / full logout
        """

        response = supabase.table("user_tokens").delete().eq("user_id", user_id).execute()
        return response.data

    @staticmethod
    async def token_exists(device_token: str):
        """
        Check if given device token already exists
        """

        response = supabase.table("user_tokens").select("device_token").eq("device_token", device_token).execute()
        return len(response.data) > 0

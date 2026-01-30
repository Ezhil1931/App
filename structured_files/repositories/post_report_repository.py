from ..config.supabase_config import supabase
from datetime import datetime

class PostReportRepository:

    @staticmethod
    async def create_post_report(post_id: str, user_id: str, report_reason: str):
        """Create a new report for a post — default status is PENDING"""

        data = {
            "post_id": post_id,
            "user_id": user_id,
            "report_reason": report_reason,
            "status": "PENDING",
            "created_at": datetime.utcnow().isoformat()
        }

        response = supabase.table("post_report").insert(data).execute()
        return response.data

    @staticmethod
    async def get_reports_by_post_id(post_id: str):
        """Get all reports for a specific post"""
        response = supabase.table("post_report").select("*").eq("post_id", post_id).execute()
        return response.data

    @staticmethod
    async def get_reports_by_user(user_id: str):
        """Get all reports created by a specific user"""
        response = supabase.table("post_report").select("*").eq("user_id", user_id).execute()
        return response.data

    @staticmethod
    async def get_all_reports(status: str | None = None):
        """
        Get all reports.
        If status filter exists, filter by status.
        """

        query = supabase.table("post_report").select("*")

        if status:
            query = query.eq("status", status)

        response = query.execute()
        return response.data

    @staticmethod
    async def update_report_status(post_report_id: str, new_status: str, admin_user_id: str):
        """
        Update report status  
        new_status must be ENUM: ["PENDING", "REVIEWED", "ACTION_TAKEN"]
        """

        if new_status not in ["PENDING", "REVIEWED", "ACTION_TAKEN"]:
            raise ValueError("Invalid value for status")

        response = supabase.table("post_report").update({
            "status": new_status,
            "modified_at": datetime.utcnow().isoformat(),
            "modified_by": admin_user_id
        }).eq("post_report_id", post_report_id).execute()

        return response.data

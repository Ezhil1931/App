from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form,status
from pydantic import BaseModel
from ..config.supabase_config import supabase
from ..middleware.jwt_auth import auth_guard
import uuid

router =APIRouter()

class PostReportModel(BaseModel):
    post_id: str
    report_post_report_id: str


@router.post("/report", status_code=status.HTTP_201_CREATED)
async def report_post(
    payload: PostReportModel,
    user=Depends(auth_guard)
):
    try:
        user_id = user["user_id"]
   
        
        post_id = payload.post_id
        report_reason = payload.report_reason

        # Check if post exists
        post = supabase.table("posts").select("*").eq("post_id", post_id).execute()
        if not post.data:
            raise HTTPException(status_code=404, detail="Post not found")

        # Check if user already reported this post
        existing = supabase.table("post_reports") \
            .select("*") \
            .eq("post_id", post_id) \
            .eq("user_id", user_id) \
            .execute()

        if existing.data:
            raise HTTPException(status_code=400, detail="You already reported this post")

        post_post_report_id = str(uuid.uuid4())

        # Insert the new report
        supabase.table("post_reports").insert({
            "post_post_report_id": post_post_report_id,
            "post_id": post_id,
            "user_id": user_id,
            "report_reason": report_reason,
            
            
        }).execute()

        return {
            "status": "success",
            "status_code": status.HTTP_201_CREATED,
            "message": "Post reported for review",
            "post_id": post_id,
            "post_post_report_id": post_post_report_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"POST_REPORT_ERROR: {str(e)}")

        
#get the single post report data -----------------------------------------
class SinglePostReportRequest(BaseModel):
    post_id: str

@router.post("/report/get", status_code=status.HTTP_200_OK)
async def get_single_post_report(data: SinglePostReportRequest, user=Depends(auth_guard)):
    try:
        user_id = user["user_id"]
    
        post_id = data.post_id

        # 1️⃣ validate post exists
        post = supabase.table("posts").select("*").eq("post_id", post_id).execute()
        if not post.data:
            raise HTTPException(status_code=404, detail="Post not found")

        # 2️⃣ get post images with position
        images = supabase.table("post_images") \
            .select("image_url, position") \
            .eq("post_id", post_id) \
            .order("position", desc=False) \
            .execute()

        # 3️⃣ like count
        likes = supabase.table("likes").select("like_id").eq("post_id", post_id).execute()
        like_count = len(likes.data)

        # 4️⃣ comment count
        comments = supabase.table("comments").select("comment_id").eq("post_id", post_id).execute()
        comment_count = len(comments.data)

        # 5️⃣ get all reports for this post
        reports = supabase.table("post_reports") \
            .select("post_report_id, user_id, report_reason, status, created_at") \
            .eq("post_id", post_id) \
            .order("created_at", desc=True) \
            .execute()

        report_count = len(reports.data)

        # 6️⃣ whether current user has reported
        user_report = supabase.table("post_reports") \
            .select("post_report_id") \
            .eq("post_id", post_id) \
            .eq("user_id", user_id) \
            .execute()

        reported_by_me = True if user_report.data else False

        return {
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "post": post.data[0],
            "images": images.data,
            "like_count": like_count,
            "comment_count": comment_count,
            "report_count": report_count,
            "reported_by_me": reported_by_me,
            "reports": reports.data  # all reports for this post
           
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"POST_REPORT_SINGLE_FETCH_ERROR: {str(e)}")



#get all report post data ---------------------------
class ReportedPostsRequest(BaseModel):
    skip: int = 0
    limit: int = 20


@router.post("/reported", status_code=status.HTTP_200_OK)
async def get_reported_posts(data: ReportedPostsRequest, user=Depends(auth_guard)):
    try:
        admin_id = user["user_id"]  # assuming admin/mod level
     

        skip = data.skip
        limit = data.limit

        # get reports with post info
        reports = supabase.table("post_reports") \
            .select("post_report_id, post_id, user_id, report_reason, status, created_at") \
            .order("created_at", desc=True) \
            .range(skip, skip + limit - 1) \
            .execute()

        return {
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "count": len(reports.data),
            "skip": skip,
            "limit": limit,
            "reports": reports.data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"POST_REPORT_FETCH_ERROR: {str(e)}")






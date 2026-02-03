from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel



from structured_files.controllers import login_router,sign_up,user_update,get_user,post_img,post_report,like_router,comment_router,follow_router,vector_search,cat_post_router,change_email_pass,change_password,forgot_pass,feed_post,refresh_token,cat_random



from structured_files.utils import check_user_name,otp_request
from structured_files.middleware import otp_verify
from structured_files.middleware.trigger_js import trigger_express_api

from structured_files.config.supabase_config import supabase

app=FastAPI()

@app.get("/")
def serverRunning():
    resposne=supabase.table("server_test").select("*").execute()

  
    return {
        "message": "App Backend is running",
        "server_test_data": resposne.data
    }



# =========================
# Authentication
# =========================
app.include_router(sign_up.router, prefix="/auth", tags=["Sign Up"])
app.include_router(login_router.router, prefix="/auth", tags=["Login"])
app.include_router(refresh_token.router, prefix="/auth", tags=["Refresh Token"])
app.include_router(change_email_pass.router, prefix="/auth", tags=["Change Email"])
app.include_router(change_password.router, prefix="/auth", tags=["Change Password"])

# =========================
# OTP
# =========================
app.include_router(otp_request.router, prefix="/auth", tags=["OTP Request"])
app.include_router(otp_verify.router, prefix="/auth", tags=["OTP Verify"])

# =========================
# Password Recovery
# =========================
app.include_router(forgot_pass.router, prefix="/auth", tags=["Forgot Password"])

# =========================
# User
# =========================
app.include_router(get_user.router, prefix="/get", tags=["Get User"])
app.include_router(user_update.router, prefix="/user", tags=["Update User"])
app.include_router(check_user_name.router, prefix="/check", tags=["Check Username"])

# =========================
# Social
# =========================

app.include_router(follow_router.router, prefix="/follow", tags=["Follow"])
app.include_router(like_router.router, prefix="/like", tags=["Like"])
app.include_router(comment_router.router, prefix="/comment", tags=["Comment"])

# =========================
# Posts
# =========================
app.include_router(post_img.router, prefix="/post", tags=["Post"])
app.include_router(post_report.router, prefix="/post", tags=["Report Post"])

# =========================
# Categories
# =========================
app.include_router(cat_post_router.router, prefix="/get", tags=["Category Posts-ezhil007"])
app.include_router(cat_random.router, prefix="/get", tags=["Random Category Posts-dhana"])

# =========================
# Search
# =========================
app.include_router(vector_search.router, prefix="/search", tags=["Search"])

# =========================
# Trending
# =========================
app.include_router(feed_post.router, prefix="/trending_post", tags=["User folllowing Posts / Trending post"])


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
     allow_headers=[
        "auth_token",
        "refresh_token",
        "Authorization",
        "Content-Type",
    ]
)





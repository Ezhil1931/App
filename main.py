from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel



from structured_files.controllers import login_router,sign_up,user_update,get_user,post_img,post_report,like_router,comment_router,follow_router,vector_search,cat_post_router,change_email_pass,change_password,forgot_pass,trending_post,refresh_token,cat_random



from structured_files.utils import check_user_name,otp_request
from structured_files.middleware import otp_verify
from structured_files.middleware.trigger_js import trigger_express_api
 

app=FastAPI()

@app.get("/")
def serverRunning():
    return {"message": "V Predict Backend is running"}

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
app.include_router(otp_request.router, prefix="/request", tags=["OTP Request"])
app.include_router(otp_verify.router, prefix="/verify", tags=["OTP Verify"])

# =========================
# Password Recovery
# =========================
app.include_router(forgot_pass.router, prefix="/forgot", tags=["Forgot Password"])

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
app.include_router(cat_post_router.router, prefix="/get", tags=["Category Posts"])
app.include_router(cat_random.router, prefix="/random", tags=["Random Category Posts"])

# =========================
# Search
# =========================
app.include_router(vector_search.router, prefix="/search", tags=["Search"])

# =========================
# Trending
# =========================
app.include_router(trending_post.router, prefix="/trending_post", tags=["Trending Posts"])


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
     allow_headers=[
        "auth_token",
        "Authorization",
        "Content-Type",
    ]
)





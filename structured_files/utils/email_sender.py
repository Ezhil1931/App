import httpx

EXPRESS_API_URL = "https://mail-service-sepia.vercel.app/api/send-otp"

async def send_otp_email( name,email:str,otp: int):
   
    payload = {
        "name":name,
        "email": email,
        "otpCode": otp
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(EXPRESS_API_URL, json=payload)
        response.raise_for_status()

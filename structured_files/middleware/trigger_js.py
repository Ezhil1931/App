from fastapi import APIRouter, HTTPException
import httpx



async def trigger_express_api(EXPRESS_API_URL):
   
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(EXPRESS_API_URL)  
            response.raise_for_status() 

        return {
            "message": "Express.js API triggered successfully",
           
        }

    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Could not connect to Express.js: {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Express.js responded with error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -*- coding: utf-8 -*-
import os
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware # <--- 新增导入
from pydantic import BaseModel
from supabase import create_client, Client
from datetime import datetime

# --- 配置 ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
app = FastAPI()

# --- 新增：CORS 中间件配置 ---
# 这是解决问题的关键。它告诉我们的 API，允许来自任何来源的请求。
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # 允许所有方法 (GET, POST, etc.)
    allow_headers=["*"], # 允许所有请求头
)
# --- CORS 配置结束 ---


class PaymentRequest(BaseModel):
    cardId: str
    amount: float
    merchantId: str

@app.post("/handlePayment")
def handle_payment(request: PaymentRequest):
    """处理支付请求的 API 端点"""
    try:
        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="支付金额必须大于0")

        rpc_params = {
            "card_id_input": request.cardId,
            "amount_to_deduct": request.amount,
            "merchant_id_input": request.merchantId
        }
        
        response = supabase.rpc("process_payment", rpc_params).execute()
        
        if response.data:
            result = json.loads(response.data)
            
            if result.get("status") == "success":
                return result 
            else:
                raise HTTPException(status_code=400, detail=result.get("message"))
        else:
            raise HTTPException(status_code=500, detail="数据库操作失败，未返回任何数据")

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Payment API is running"}
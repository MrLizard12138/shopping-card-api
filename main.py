# -*- coding: utf-8 -*-
import os
import json
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from datetime import datetime

# --- 配置 ---
# 这些值将从 Render 的环境变量中读取
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# 初始化 Supabase 客户端
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 初始化 FastAPI 应用
app = FastAPI()

# 定义请求体的数据模型
class PaymentRequest(BaseModel):
    cardId: str
    amount: float
    merchantId: str

# --- API 端点 ---
@app.post("/handlePayment")
def handle_payment(request: PaymentRequest):
    """处理支付请求的 API 端点"""
    try:
        # 1. 参数验证
        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="支付金额必须大于0")

        # 2. 准备调用数据库函数的参数
        rpc_params = {
            "card_id_input": request.cardId,
            "amount_to_deduct": request.amount,
            "merchant_id_input": request.merchantId
        }
        
        # 3. 调用数据库函数
        response = supabase.rpc("process_payment", rpc_params).execute()
        
        # 4. 处理数据库函数的返回结果 (关键改动)
        if response.data:
            # 手动解析数据库返回的纯文本JSON
            result = json.loads(response.data)
            
            if result.get("status") == "success":
                # 直接返回解析后的成功结果
                return result 
            else:
                # 如果是业务逻辑错误（如余额不足），则向前端报告错误
                raise HTTPException(status_code=400, detail=result.get("message"))
        else:
            # 这种情况不应该发生，但作为保险
            raise HTTPException(status_code=500, detail="数据库操作失败，未返回任何数据")

    except HTTPException as http_exc:
        # 重新抛出已知的 HTTP 异常，以便 FastAPI 正确处理
        raise http_exc
    except Exception as e:
        # 捕获所有其他未知错误
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

# 健康检查端点 (可选，但推荐)
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Payment API is running"}
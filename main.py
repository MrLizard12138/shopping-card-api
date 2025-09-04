# -*- coding: utf-8 -*-
import os
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

        # 2. 调用数据库函数来安全地处理支付
        #    这是我们之前在 Supabase SQL Editor 中创建的那个强大的函数！
        rpc_params = {
            "card_id_input": request.cardId,
            "amount_to_deduct": request.amount,
            "merchant_id_input": request.merchantId
        }
        
        response = supabase.rpc("process_payment", rpc_params).execute()
        
        # 3. 处理数据库函数的返回结果
        if response.data:
            result = response.data
            if result.get("status") == "success":
                return {
                    "status": "success",
                    "message": result.get("message"),
                    "newBalance": result.get("newBalance")
                }
            else:
                # 如果是业务逻辑错误（如余额不足），返回 400 错误
                raise HTTPException(status_code=400, detail=result.get("message"))
        else:
            # 如果 rpc 调用本身失败了
            raise HTTPException(status_code=500, detail="数据库操作失败")

    except HTTPException as http_exc:
        # 重新抛出已知的 HTTP 异常
        raise http_exc
    except Exception as e:
        # 捕获所有其他未知错误
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

# 健康检查端点 (可选，但推荐)
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Payment API is running"}

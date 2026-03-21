from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import sys
import os

# Adjust path to import main's load_data / save_data
# Alternatively, I can move data logic here, but let's keep it simple
router = APIRouter()

@router.get("/")
def get_portfolio():
    from database import load_data
    return load_data()

@router.post("/")
def update_portfolio(data: Dict[str, Any]):
    from database import save_data, load_data
    
    current_data = load_data()
    
    # Deep update dict
    def deep_update(d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                d[k] = deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d
        
    updated = deep_update(current_data, data)
    save_data(updated)
    return {"status": "success", "data": updated}

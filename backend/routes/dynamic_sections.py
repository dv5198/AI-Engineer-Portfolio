from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from database import load_data, save_data
import uuid
from datetime import datetime

router = APIRouter()

# --- Models ---
class ResearchItem(BaseModel):
    id: Optional[str] = None
    topic: str
    description: str
    visible: bool = True
    order: int

class TestimonialItem(BaseModel):
    id: Optional[str] = None
    quote: str
    name: str
    role: str
    company: str
    relation: str
    visible: bool = True
    order: int

class BlogPost(BaseModel):
    id: Optional[str] = None
    title: str
    slug: Optional[str] = None
    content: str
    category: str
    visible: bool = True
    order: int
    date: str = datetime.now().strftime("%Y-%m-%d")

class LanguageItem(BaseModel):
    id: Optional[str] = None
    name: str
    level: str
    percentage: int
    visible: bool = True
    order: int

class ReorderRequest(BaseModel):
    ids: List[str]

# --- Helpers ---
def log_activity(action: str, section: str, changes: dict = None):
    data = load_data()
    log_entry = {
        "id": f"log_{uuid.uuid4().hex[:8]}",
        "action": action,
        "section": section,
        "timestamp": datetime.now().isoformat(),
        "changes": changes
    }
    data["activityLog"].insert(0, log_entry)
    data["activityLog"] = data["activityLog"][:100] # Keep last 100
    save_data(data)

# --- Generic CRUD Factory (Simplified for brevity but functional) ---
def register_crud(collection_name: str, model_class, section_display: str):
    @router.post(f"/{collection_name}")
    async def create_item(item: model_class):
        data = load_data()
        item.id = f"{collection_name[:2]}_{uuid.uuid4().hex[:8]}"
        if hasattr(item, 'slug') and hasattr(item, 'title'):
            item.slug = item.title.lower().replace(" ", "-")
        
        data[collection_name].append(item.dict())
        save_data(data)
        log_activity(f"Added new item to {section_display}", section_display)
        return item

    @router.put(f"/{collection_name}/{{item_id}}")
    async def update_item(item_id: str, item: model_class):
        data = load_data()
        for idx, existing in enumerate(data[collection_name]):
            if existing["id"] == item_id:
                item.id = item_id # Keep same ID
                data[collection_name][idx] = item.dict()
                save_data(data)
                log_activity(f"Updated item in {section_display}", section_display)
                return item
        raise HTTPException(status_code=404, detail="Item not found")

    @router.delete(f"/{collection_name}/{{item_id}}")
    async def delete_item(item_id: str):
        data = load_data()
        initial_len = len(data[collection_name])
        data[collection_name] = [x for x in data[collection_name] if x["id"] != item_id]
        if len(data[collection_name]) == initial_len:
            raise HTTPException(status_code=404, detail="Item not found")
        save_data(data)
        log_activity(f"Deleted item from {section_display}", section_display)
        return {"message": "Deleted"}

    @router.patch(f"/{collection_name}/{{item_id}}/visibility")
    async def toggle_visibility(item_id: str):
        data = load_data()
        for x in data[collection_name]:
            if x["id"] == item_id:
                x["visible"] = not x.get("visible", True)
                save_data(data)
                return {"visible": x["visible"]}
        raise HTTPException(status_code=404, detail="Item not found")

    @router.patch(f"/{collection_name}/reorder")
    async def reorder_items(req: ReorderRequest):
        data = load_data()
        id_map = {x["id"]: x for x in data[collection_name]}
        new_list = []
        for new_id in req.ids:
            if new_id in id_map:
                new_list.append(id_map[new_id])
        
        # Update order field
        for i, item in enumerate(new_list):
            item["order"] = i + 1
            
        data[collection_name] = new_list
        save_data(data)
        return {"message": "Reordered"}

# Register all
register_crud("researchInterests", ResearchItem, "Research")
register_crud("testimonials", TestimonialItem, "Testimonials")
register_crud("blogPosts", BlogPost, "Blog")
register_crud("languages", LanguageItem, "Languages")

@router.get("/blog/{slug}")
async def get_blog_post(slug: str):
    data = load_data()
    for post in data["blogPosts"]:
        if post["slug"] == slug:
            return post
    raise HTTPException(status_code=404, detail="Post not found")

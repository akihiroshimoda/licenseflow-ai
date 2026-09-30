from pydantic import BaseModel, Field

class Product(BaseModel):
    product_id: str
    name: str
    category: str
    base_price: float = Field(gt=0)
    
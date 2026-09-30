from pydantic import BaseModel

class Customer(BaseModel):
    customer_id: str
    name: str
    region: str
    account_tier: str
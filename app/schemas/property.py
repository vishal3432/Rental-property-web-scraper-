from pydantic import BaseModel


class PropertyOut(BaseModel):
    id: int
    address: str
    price_text: str
    price_value: float
    link: str

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    count: int
    items: list[PropertyOut]


class RecommendationResponse(BaseModel):
    source_property_id: int
    recommendations: list[PropertyOut]

from pydantic import BaseModel, Field


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class TagResponse(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}


class TagWithCount(BaseModel):
    id: int
    name: str
    slug: str
    article_count: int

    model_config = {"from_attributes": True}

from pydantic import BaseModel


class ImageMetadata(BaseModel):
    title: str
    url: str
    price: str
    author: str


class ScraperResults(BaseModel):
    results: dict[str, list[ImageMetadata]]

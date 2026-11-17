from typing import List, TypedDict
from pydantic import BaseModel

class Step(BaseModel):
    file_path: str
    instruction: str

class Plan(BaseModel):
    steps: List[Step]

class Review(BaseModel):
    file_path: str
    passed: bool
    feedback: str

class ReviewList(BaseModel):
    reviews: List[Review]

class State(TypedDict):
    task: str
    steps: List[dict]
    files: List[str]
    failed: List[dict]
    retries: int
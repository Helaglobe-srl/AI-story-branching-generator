from typing import List
from pydantic import BaseModel, Field

class Choice(BaseModel):
    text: str = Field(..., description="The text describing this choice option")
    outcome: str = Field(..., description="The outcome of making this choice")
    impact: str = Field(..., description="The impact this choice has on the character's condition")

class Node(BaseModel):
    situation: str = Field(..., description="The situation where the character must make a choice")
    reasoning: str = Field(..., description="From which source of information the node was generated")
    choices: List[Choice] = Field(
        ..., 
        description="List of possible choices the character can make in this situation",
    )

class StoryBranch(BaseModel):
    disease: str = Field(..., description="The disease the character is suffering from")
    nodes: List[Node] = Field(
        ..., 
        description="List of decision nodes in the story"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "disease": "Asthma",
                "nodes": [
                    {
                        "situation": "Alex wakes up late with shortness of breath. The inhaler is visible on the nightstand, and the window is closed.",
                        "choices": [
                            {
                                "text": "Take the inhaler and open the window for fresh air",
                                "outcome": "Breathing stabilizes, energy increases, well-being improves",
                                "impact": "Positive impact on asthma management, better day ahead"
                            },
                            {
                                "text": "Ignore the inhaler and rush out quickly",
                                "outcome": "Breathing becomes labored, well-being decreases",
                                "impact": "Negative impact on asthma management, difficult day ahead"
                            }
                        ]
                    }
                ]
            }
        } 
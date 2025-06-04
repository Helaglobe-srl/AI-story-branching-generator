from typing import List, Optional
from pydantic import BaseModel, Field

class Choice(BaseModel):
    text: str = Field(..., description="the text describing this choice option")
    outcome: str = Field(..., description="the outcome of making this choice")
    impact: str = Field(..., description="the impact this choice has on the character's condition")

class Character(BaseModel):
    type: str = Field(..., description="the type of character (e.g., 'paziente', 'dottore')")

class ChatMessage(BaseModel):
    who: int = Field(..., description="identifier of the character speaking (1 for character1, 2 for character2)")
    text: str = Field(..., description="the message text")

class Node(BaseModel):
    situation: str = Field(..., description="the situation where the character must make a choice")
    reasoning: str = Field(..., description="from which source of information the node was generated")
    background: Optional[str] = Field(None, description="the setting or location where the situation takes place")
    character1: Optional[Character] = Field(None, description="the first character in the situation")
    character2: Optional[Character] = Field(None, description="the second character in the situation")
    chat: Optional[List[ChatMessage]] = Field(None, description="the conversation between characters")
    choices: List[Choice] = Field(
        ..., 
        description="list of possible choices the character can make in this situation",
    )

class StoryBranch(BaseModel):
    disease: str = Field(..., description="the disease the character is suffering from")
    nodes: List[Node] = Field(
        ..., 
        description="list of decision nodes in the story"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "disease": "ipertensione",
                "nodes": [
                    {
                        "situation": "marco si sveglia con un leggero mal di testa. deve prendere le medicine per l'ipertensione ma ha un importante incontro di lavoro tra un'ora e sa che le medicine potrebbero causargli sonnolenza.",
                        "reasoning": "l'aderenza alla terapia è importante, ma anche gli impegni quotidiani e gli effetti collaterali possono influenzare le decisioni.",
                        "background": "camera da letto",
                        "character1": {
                            "type": "paziente"
                        },
                        "character2": {
                            "type": "medico"
                        },
                        "chat": [
                            {"who": 1, "text": "dottore, le medicine mi fanno sentire stanco durante il giorno. oggi ho un incontro importante."},
                            {"who": 2, "text": "capisco la sua preoccupazione, ma è importante mantenere regolare l'assunzione dei farmaci."}
                        ],
                        "choices": [
                            {
                                "text": "prendere la medicina come prescritto, nonostante il rischio di sonnolenza durante l'incontro",
                                "outcome": "la pressione rimane sotto controllo, ma marco avverte una leggera sonnolenza durante la presentazione",
                                "impact": "beneficio per la salute a lungo termine, ma potenziale impatto negativo sulla performance lavorativa immediata"
                            },
                            {
                                "text": "rimandare l'assunzione del farmaco a dopo l'incontro di lavoro per rimanere più lucido",
                                "outcome": "marco riesce a mantenere la concentrazione durante l'incontro, ma la sua pressione risulta più elevata del solito",
                                "impact": "vantaggio immediato nella performance lavorativa, ma potenziale rischio per la salute se questo comportamento diventa abituale"
                            }
                        ]
                    }
                ]
            }
        } 
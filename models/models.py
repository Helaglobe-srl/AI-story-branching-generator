from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# Valid background options
BackgroundType = Literal[
    "bagno", "camera", "citta", "cucina", 
    "ufficio", "parco", "palestra", "sala"
]

# Valid character types
CharacterType = Literal[
    "amico", "amica", "collega", "nipote", 
    "familiare", "conoscente", "paziente"
]

class Choice(BaseModel):
    text: str = Field(..., description="the text describing this choice option")
    outcome: str = Field(..., description="the outcome of making this choice")
    impact: str = Field(..., description="the impact this choice has on the character's condition")
    score: int = Field(0, description="the score for this choice: +1 for correct, -1 for incorrect")

class Character(BaseModel):
    type: CharacterType = Field(..., description="the type of character (e.g., 'paziente', 'dottore')")

class ChatMessage(BaseModel):
    who: int = Field(..., description="identifier of the character speaking (1 for character1, 2 for character2)")
    text: str = Field(..., description="the message text")

class Node(BaseModel):
    situation: str = Field(..., description="the situation where the character must make a choice")
    reasoning: str = Field(..., description="from which source of information the node was generated")
    background: Optional[BackgroundType] = Field(None, description="the setting or location where the situation takes place")
    character1: Optional[Character] = Field(None, description="the first character in the situation")
    character2: Optional[Character] = Field(None, description="the second character in the situation")
    chat: Optional[List[ChatMessage]] = Field(None, description="the conversation between characters")
    choices: List[Choice] = Field(
        ..., 
        description="list of possible choices the character can make in this situation"
    )

class StoryBranch(BaseModel):
    disease: str = Field(..., description="the disease the character is suffering from")
    nodes: List[Node] = Field(
        ..., 
        description="list of decision nodes in the story"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "disease": "ipertensione",
                    "nodes": [
                        {
                            "situation": "marco si sveglia con un leggero mal di testa. deve prendere le medicine per l'ipertensione ma ha un importante incontro di lavoro tra un'ora e sa che le medicine potrebbero causargli sonnolenza.",
                            "reasoning": "l'aderenza alla terapia è importante, ma anche gli impegni quotidiani e gli effetti collaterali possono influenzare le decisioni.",
                            "background": "camera",
                            "character1": {
                                "type": "paziente"
                            },
                            "character2": {
                                "type": "familiare"
                            },
                            "chat": [
                                { "who": 1, "text": "oggi ho un incontro importante e se prendo la medicina potrei sentirmi stanco." },
                                { "who": 2, "text": "eh sì, lo so che a volte ti rallenta un po'. non puoi prenderla dopo l'incontro?" },
                                { "who": 1, "text": "non so, ho sempre paura che saltare l'orario preciso faccia male." },
                                { "who": 2, "text": "ma è solo per oggi, no? magari cerca di prenderla appena finisci." },
                                { "who": 1, "text": "sì, ma mi dà ansia anche così. magari la prendo adesso e vada come vada." },
                                { "who": 2, "text": "fai come ti senti più tranquillo. magari mangia qualcosa prima, ti aiuta un po' con la stanchezza." },
                                { "who": 1, "text": "ok, ci penso un attimo. grazie." }
                            ],
                            "choices": [
                                {
                                    "text": "prendere la medicina come prescritto, nonostante il rischio di sonnolenza durante l'incontro",
                                    "outcome": "la pressione rimane sotto controllo, ma marco avverte una leggera sonnolenza durante la presentazione",
                                    "impact": "beneficio per la salute a lungo termine, ma potenziale impatto negativo sulla performance lavorativa immediata",
                                    "score": 1
                                },
                                {
                                    "text": "rimandare l'assunzione del farmaco a dopo l'incontro di lavoro per rimanere più lucido",
                                    "outcome": "marco riesce a mantenere la concentrazione durante l'incontro, ma la sua pressione risulta più elevata del solito",
                                    "impact": "vantaggio immediato nella performance lavorativa, ma potenziale rischio per la salute se questo comportamento diventa abituale",
                                    "score": -1
                                }
                            ]
                        }
                    ]
                },
                {
                    "disease": "diabete",
                    "nodes": [
                        {
                            "situation": "lucia si trova al ristorante con amici. è diabetica e sta seguendo una dieta rigorosa, ma gli amici hanno ordinato un dolce da condividere e la incoraggiano a prenderne un pezzo.",
                            "reasoning": "la pressione sociale può influire sulle scelte alimentari, specialmente in situazioni sociali.",
                            "background": "sala",
                            "character1": {
                                "type": "paziente"
                            },
                            "character2": None,
                            "chat": [
                                {
                                    "who": 1,
                                    "text": "tutti stanno mangiando quel dolce e mi guardano. se rifiuto sembrerà che non voglio fare parte del gruppo, ma non voglio far salire la glicemia..."
                                }
                            ],
                            "choices": [
                                {
                                    "text": "rifiutare gentilmente il dolce spiegando la propria condizione",
                                    "outcome": "lucia mantiene il controllo della glicemia, ma si sente leggermente a disagio per un momento",
                                    "impact": "positivo per la salute, leggero disagio sociale momentaneo",
                                    "score": 1
                                },
                                {
                                    "text": "mangiare una porzione normale del dolce per non attirare l'attenzione sulla sua condizione",
                                    "outcome": "lucia si sente parte del gruppo, ma più tardi deve gestire livelli di glicemia significativamente elevati",
                                    "impact": "forte impatto negativo sulla salute, temporaneo beneficio sociale",
                                    "score": -1
                                }
                            ]
                        }
                    ]
                }
            ]
        }
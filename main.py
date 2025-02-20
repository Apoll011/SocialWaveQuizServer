from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Literal, Dict, Optional, Set, Tuple
import uvicorn
from enum import Enum
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Direction(str, Enum):
    ACROSS = "across"
    DOWN = "down"

class Completion(BaseModel):
    direction: Direction
    number: int
    answer: str

class Submission(BaseModel):
    username: str
    completion: Completion

class WordSubmission(BaseModel):
    username: str
    word: str
    points: int

class PlayerScore(BaseModel):
    username: str
    score: int
    completed_words: Optional[List[Dict[str, str]]] = None

WORD_POINTS = {
    1: 100,
    2: 95,
    3: 90,
    4: 85,
    5: 80,
    6: 75,
    7: 70,
    8: 65,
    9: 60,
    10: 55,
    11: 50,
    12: 45,
    13: 40,
    14: 35,
    15: 30,
    16: 25
}

player_scores: Dict[str, int] = {}
# Armazena as palavras completas para cada usuário como conjunto de tuplas (número, direção)
completed_words: Dict[str, Set[str]] = {}
# Armazena as palavras reais que o usuário completou
word_records: Dict[str, List[Dict]] = {}

@app.post("/submit")
async def submit_completion(submission: Submission):
    username = submission.username
    completion = submission.completion

    if not 1 <= completion.number <= 16:
        raise HTTPException(status_code=400, detail="Número de palavra inválido")

    user_key = (completion.number, completion.direction.value)

    # Inicializa as estruturas de dados do usuário se necessário
    if username not in completed_words:
        completed_words[username] = set()
    if username not in word_records:
        word_records[username] = []

    # Verifica se o usuário já completou essa palavra
    if user_key in completed_words[username]:
        return {"status": "already_completed", "message": "Palavra já completada por este usuário"}

    # Atribui pontos e registra a conclusão
    points = WORD_POINTS[completion.number]
    player_scores[username] = player_scores.get(username, 0) + points
    completed_words[username].add(user_key)

    # Registra a palavra completa
    word_records[username].append(
        {
            "word": completion.answer,
            "number": completion.number,
            "direction": completion.direction.value,
            "points": points
        }
    )

    return {
        "status": "success",
        "points_earned": points,
        "total_score": player_scores[username]
    }

@app.post("/add-word")
async def add_word(submission: WordSubmission):
    username = submission.username
    word = submission.word
    points = submission.points

    if points <= 0:
        raise HTTPException(status_code=400, detail="Pontos devem ser positivos")

    if username not in completed_words:
        completed_words[username] = set()
    if username not in word_records:
        word_records[username] = []

    user_key = word

    if user_key in completed_words[username]:
        return {
            "status": "already_completed",
            "message": "Palavra já completada por este usuário",
            "current_score": player_scores.get(username, 0)
        }

    # Atribui pontos e registra a conclusão
    player_scores[username] = player_scores.get(username, 0) + points
    completed_words[username].add(user_key)

    # Registra a palavra completa
    word_records[username].append(
        {
            "word": word,
            "points": points
        }
    )

    return {
        "status": "success",
        "points_earned": points,
        "total_score": player_scores[username]
    }

@app.get("/leaderboard", response_model=List[PlayerScore])
async def get_leaderboard():
    sorted_players = sorted(
        [{"username": k, "score": v} for k, v in player_scores.items()],
        key=lambda x: x["score"],
        reverse=True
    )
    return sorted_players[:10]

@app.get("/player/{username}", response_model=PlayerScore)
async def get_player_score(username: str):
    if username not in player_scores:
        return {"username": username, "score": 0, "completed_words": []}

    return {
        "username": username,
        "score": player_scores[username],
        "completed_words": word_records.get(username, [])
    }

@app.get("/player/{username}/words")
async def get_player_words(username: str):
    return {
        "username": username,
        "completed_words": word_records.get(username, [])
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
from copy import deepcopy
from enum import Enum
from random import randint
import socket


class Card(Enum):
    KING = "KING"
    QUEEN = "QUEEN"
    JOKER = "JOKER"
    ACE = "ACE"


NUMBER_CARD = 6
ALL_CARDS = (
    [deepcopy(Card.KING) for _ in range(NUMBER_CARD)]
    + [deepcopy(Card.QUEEN) for _ in range(NUMBER_CARD)]
    + [deepcopy(Card.JOKER) for _ in range(NUMBER_CARD)]
    + [deepcopy(Card.ACE) for _ in range(NUMBER_CARD)]
)

BUFFER_SIZE = 4096
PORT = 8180
NUMBER_PLAYER = 4


class Player:
    def __init__(self, name: str, conn: socket.socket = None, addr=None):
        self.name = name
        self.conn = conn
        self.addr = addr
        self.shot = 0
        self.bullets = [0, 0, 0, 0, 0, 0]
        self.bullets[randint(0, 5)] = 1
        self.cards = []
        self.is_alive = True

    def round(self, cards: list[Card]):
        self.cards = cards

    def choice(self, indexes: list[int]):
        selected = []
        for index in sorted(indexes, reverse=True):
            selected.append(self.cards.pop(int(index)).value)
        return selected

    def set_round(self, cards: list[Card]):
        self.cards = cards

    def roulette(self):
        boom = bool(self.bullets[self.shot])
        self.shot += 1
        self.is_alive = not boom
        return boom

    def get_round_str(self):
        return " ".join([card.name[0] for card in self.cards])

    def __str__(self) -> str:
        return self.name

    def __eq__(self, value):
        return self.name == value.name

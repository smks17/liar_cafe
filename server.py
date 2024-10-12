from copy import deepcopy
import json
from random import choice, shuffle
import socket
from time import sleep

from game import ALL_CARDS, BUFFER_SIZE, NUMBER_PLAYER, PORT, Card, Player


class Game:
    def __init__(self):
        self.players: list[Player] = []
        self.round_card: Card = None
        self.turn: int = 0
        self.last_cards = []

    def create_host(self):
        self.host = socket.socket()
        self.host.bind(("0.0.0.0", PORT))
        self.host.listen(3)
        print("host created")

        print("Waiting for others...")
        for _ in range(NUMBER_PLAYER):
            conn, addr = self.host.accept()
            print("Connected from", addr)
            name = json.loads(conn.recv(BUFFER_SIZE).decode())["data"][0]
            print("JOIN:", name)
            self.players.append(Player(name, conn, addr))
            server_player = list(map(str, self.players))
            conn.sendall(
                json.dumps({"type": "players", "data": server_player}).encode()
            )
            for player in self.players:
                if player.name != name:
                    player.conn.sendall(
                        json.dumps({"type": "new_player", "data": [name]}).encode()
                    )
        sleep(1)

    @staticmethod
    def send_to(player: Player, data: dict):
        player.conn.sendall(json.dumps(data).encode())

    def send_all(self, data: dict):
        for player in self.players:
            Game.send_to(player, data)

    @staticmethod
    def receive_from(player: Player) -> dict:
        return json.loads(player.conn.recv(BUFFER_SIZE).decode())

    @property
    def alive_players(self) -> list[Player]:
        return [player for player in self.players if player.is_alive]

    def handle_round_card(self):
        self.round_card = choice(deepcopy(ALL_CARDS))
        self.send_all({"type": "round_card", "data": [self.round_card.name]})

    def handle_the_player_cards(self):
        new_round = deepcopy(ALL_CARDS)
        shuffle(new_round)
        for i, player in enumerate(self.alive_players):
            player_cards = new_round[i * 6 : (i + 1) * 6]
            player.set_round(player_cards)
            Game.send_to(
                player,
                {
                    "type": "handle_cards",
                    "for_player": player.name,
                    "data": [card.value for card in player_cards],
                },
            )

    @property
    def before_turn(self):
        return (self.turn - 1) % len(self.alive_players)

    def next_turn(self):
        self.turn += 1
        self.turn %= len(self.alive_players)
        self.send_all({"type": "next_turn", "data": None})
        for player in self.players:
            data = Game.receive_from(player)
            assert data["type"] == "next_turn"

    def get_player_choice(self):
        turn_player = self.alive_players[self.turn]
        data = Game.receive_from(turn_player)
        indexes_card = data["data"]
        data["data"] = [len(indexes_card)]
        for player in self.players:
            if player != turn_player:
                Game.send_to(player, data)
        sleep(1)
        if data["type"] == "choice_card":
            self.last_cards = turn_player.choice(indexes_card)
            return False
        elif data["type"] == "roulette":
            data = {
                "type": "result_liar",
                "data": self.last_cards,
            }
            self.send_all(data)
            sleep(1)
            if all(card == self.round_card.value for card in self.last_cards):
                target_player = self.alive_players[self.turn]
            else:
                target_player = self.alive_players[self.before_turn]

            status = target_player.roulette()
            self.send_all(
                {
                    "type": "result_roulette",
                    "for_player": target_player.name,
                    "data": [status],
                }
            )
            sleep(1)

            return True

    def sim(self):
        end_game = False
        while not end_game:
            self.turn %= len(self.alive_players)
            end_round = False
            print("new round")
            print(f"alive: {[player.name for player in self.alive_players]}")
            self.handle_round_card()
            print(f"round card: {self.round_card}")
            sleep(1)
            self.handle_the_player_cards()
            while not end_round:
                print(f"Turn player {self.alive_players[self.turn]}")
                end_round = self.get_player_choice()
                if end_round:
                    break
                self.next_turn()
            if len(self.alive_players) < 2:
                self.send_all(
                    {"type": "winner", "data": [self.alive_players[0].name]}
                )
                print(f"Winner is {self.alive_players[0].name}")
                end_game = True
                break
            sleep(4)


if __name__ == "__main__":
    game = Game()
    try:
        game.create_host()
        game.sim()
    finally:
        game.host.close()

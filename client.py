import json
import socket
import sys
from time import sleep
from game import BUFFER_SIZE, NUMBER_PLAYER, PORT, Card, Player


class Game:
    def __init__(self):
        self.players = []
        self.server_conn = None
        self.round_card: Card = None
        self.turn: int = 0
        self.me = None

    def connect_to(self, ip: str, my_name: str):
        print(f"Connecting to {ip}")
        self.server_conn = socket.socket()
        self.server_conn.connect((ip, PORT))
        self.server_conn.send(
            json.dumps({"type": "new_player", "data": [my_name]}).encode()
        )
        print("Connected to host")
        data = self.server_conn.recv(BUFFER_SIZE)
        players_name = json.loads(data.decode())["data"]
        self.players = []
        for player_name in players_name:
            self.players.append(Player(player_name))
        self.me = self.players[-1]
        print(f"Players: {','.join(players_name)}")
        for _ in range(NUMBER_PLAYER - len(self.players)):
            data = self.server_conn.recv(BUFFER_SIZE)
            new_player = json.loads(data.decode())["data"][0]
            self.players.append(Player(new_player))
            print(f"Player {new_player} join")

    @property
    def alive_players(self):
        return [player for player in self.players if player.is_alive]

    def send(self, data: dict):
        self.server_conn.sendall(json.dumps(data).encode())

    def receive(self) -> dict:
        return json.loads(self.server_conn.recv(BUFFER_SIZE).decode())

    def get_round_card(self):
        data = self.receive()
        self.round_card = Card(data["data"][0])

    def get_my_cards(self):
        data = self.receive()
        self.me.set_round([Card(card) for card in data["data"]])

    def next_turn(self):
        self.turn += 1
        self.turn %= len(self.alive_players)
        self.send({"type": "next_turn", "data": None})

    def player_choices(self, choices: list[int]):
        if choices[0] == "L":
            self.send({"type": "roulette", "data": ["L"]})
            sleep(1)
            data = self.receive()
            print(f"Cards reveal: {data['data']}")
            print("roulette ...")
            sleep(2)
            data = self.receive()
            for player in self.alive_players:
                if player.name == data["for_player"]:
                    player.shot += 1
            if data["data"][0]:
                for player in self.alive_players:
                    if player.name == data["for_player"]:
                        player.is_alive = False
                        break
                print(f"BOOOOM! Player {data['for_player']} is dead")
            else:
                print(f"HAHAHA! Player {data['for_player']} is still alive")
        else:
            _ = self.me.choice(choices)
            self.send(
                {"type": "choice_card", "data": choices}
            )

    def get_player_choices(self):
        turn_player = self.alive_players[self.turn]
        data = self.receive()
        if data["type"] == "choice_card":
            print(
                f"Player {turn_player.name} has {data['data'][0]} {self.round_card.name} cards"
            )
            return False
        else:
            print(
                f"Player {turn_player.name} believe {self.alive_players[self.before_turn]} is lier"
            )
            sleep(1)
            data = self.receive()
            print(f"Cards reveal: {data['data']}")
            print("roulette ...")
            sleep(2)
            data = self.receive()
            for player in self.alive_players:
                if player.name == data["for_player"]:
                    player.shot += 1
            if data["data"][0]:
                for player in self.alive_players:
                    if player.name == data["for_player"]:
                        player.is_alive = False
                        break
                print(f"BOOOOM! Player {data['for_player']} is dead")
            else:
                print(f"HAHAHA! Player {data['for_player']} is still alive")
            return True

    @property
    def before_turn(self):
        return (self.turn - 1) % len(self.alive_players)

    def handle_game(self):
        end_game = False
        while not end_game:
            self.turn %= len(self.alive_players)
            end_turn = False
            print("New Round")
            self.get_round_card()
            sleep(1)
            if self.me.is_alive:
                self.get_my_cards()
            while not end_turn:
                # import os
                # os.system('cls' if os.name == 'nt' else 'clear')

                for player in self.players:
                    print(
                        f"{player.name}: {player.shot}/6 {'alive' if player.is_alive else 'dead'}"
                    )

                print(f"selected card for this round is {self.round_card.name}")
                sleep(1)

                if self.me.is_alive:
                    print(
                        f"            {' '.join(list(map(str, range(len(self.me.cards)))))}"
                    )
                    print(f"Your round: {self.me.get_round_str()}")
                else:
                    print("You are dead!")

                sleep(1)

                if self.me.is_alive and self.alive_players[self.turn] == self.me:
                    my_choices = input("Your choice: ").split(" ")
                    while len(my_choices) > len(self.me.cards):
                        print("You do not have sufficient cards. Try again")
                        my_choices = input("Your choice: ").split(" ")
                    if my_choices[0] == "L":
                        self.player_choices(my_choices)
                        break
                    else:
                        self.player_choices(my_choices)
                else:
                    if self.get_player_choices():
                        end_turn = True
                        break

                sleep(1)

                data = self.receive()

                if data["type"] == "winner":
                    print(f"Winner is {self.alive_players[0].name}")
                    end_game = True
                    break

                self.next_turn()

                print("------------------------")
            sleep(2)
            if len(self.alive_players) < 2:
                print(f"Winner is {self.alive_players[0].name}")
                end_game = True
                break
            print("------------------------")




if __name__ == "__main__":
    game = Game()
    my_name = sys.argv[1]
    server_ip = sys.argv[2]
    game.connect_to(server_ip, my_name)
    print("--------------------")
    game.handle_game()

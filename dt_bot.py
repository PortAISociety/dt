import model
import os
from collections import defaultdict
import hlt
from hlt import constants
import logging


class Bot:
    def __init__(self, weights):
        game = hlt.Game()
        game.ready("DecisionTreeBot")

        m = model.HaliteModel(weights=weights)
        self.m = m
        self.game = game

    def run(self):
        go_home = defaultdict(lambda: False)
        while True:
            self.game.update_frame()
            me = self.game.me #got metadata
            game_map = self.game.game_map #
            other_players = [p for pid, p in self.game.players.items() if pid != self.game.my_id]

            command_queue = []

            for ship in me.get_ships():
                if ship.position == me.shipyard.position:
                    go_home[ship.id] = False
                elif go_home[ship.id] or ship.halite_amount == constants.MAX_HALITE:
                    go_home[ship.id] = True
                    movement = game_map.get_safe_move(game_map[ship.position],game_map[me.shipyard.position])
                    if movement is not None:
                        game_map[ship.position.directional_offset(movement)].mark_unsafe(ship)
                        command_queue.append(ship.move(movement))
                    else:
                        ship.stay_still()
                    continue

                ml_move = self.m.predict_move(ship, game_map, me, other_players, self.game.turn_number)
                logging.info("move: ")
                logging.info(ml_move)
                logging.info("move: ")
                logging.error(ml_move)
                if ml_move is not None:
                    movement = game_map.get_safe_move(game_map[ship.position],
                                                game_map[ship.position.directional_offset(ml_move)])
                    if movement is not None:
                        game_map[ship.position.directional_offset(movement)].mark_unsafe(ship)
                        command_queue.append(ship.move(movement))
                        continue
                ship.stay_still()

            if me.halite_amount >= constants.SHIP_COST and \
                    not game_map[me.shipyard].is_occupied and len(me.get_ships()) <=4:
                        command_queue.append(self.game.me.shipyard.spawn())

            self.game.end_turn(command_queue)

bot = Bot("out/dt.svc")
bot.run()

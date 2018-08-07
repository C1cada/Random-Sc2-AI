from sc2.unit import Unit
from sc2.units import Units
from sc2.data import race_gas, race_worker, race_townhalls, ActionResult, Attribute, Race

import sc2 # pip install sc2
from sc2 import Race, Difficulty, run_game, maps
from sc2.constants import * # for autocomplete
from sc2.ids.unit_typeid import *
from sc2.ids.ability_id import *
from sc2.position import Point2, Point3
from sc2.helpers import ControlGroup

from sc2.player import Bot, Computer, Human
import math
import random

class Trinity(sc2.BotAI):
  def __init__(self):
  
  async def on_step(self, iteration):
        if iteration == 0:
            for worker in self.workers:
                await self.do(worker.attack(self.enemy_start_locations[0]))
                
run_game(maps.get("MechDepotLE"), [
     #Human(Race.Zerg),
     Bot(Race.Random, Trinity()),
     #Bot(Race.Protoss, CannonLoverBot())
     Computer(Race.Zerg, Difficulty.VeryHard)
     ], realtime=True)

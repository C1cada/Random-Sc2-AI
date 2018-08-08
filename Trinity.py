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
    self.myRace = "None"
    
  async def on_step(self, iteration):
    if iteration == 0:
      await self.onStart()
            
  async def onStart(self):
    await self.chat_send("(glhf)")
    if self.townhalls == self.units(COMMANDCENTER):
      self.myRace = "Terran"
    elif self.townhalls == self.units(HATCHERY):
      self.myRace = "Zerg"
    elif self.townhalls == self.units(NEXUS):
      self.myRace = "Protoss"
                 
run_game(maps.get("MechDepotLE"), [
     #Human(Race.Zerg),
     Bot(Race.Random, Trinity()),
     #Bot(Race.Protoss, CannonLoverBot())
     Computer(Race.Zerg, Difficulty.VeryHard)
     ], realtime=True)

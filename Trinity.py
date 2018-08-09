from sc2.unit import Unit
from sc2.units import Units
from sc2.data import race_gas, race_worker, race_townhalls, ActionResult, Attribute, Race

import sc2  # pip install sc2
from sc2 import Race, Difficulty, run_game, maps
from sc2.constants import *  # for autocompletepomg spurce code
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
        self.stopWorker = False

    async def on_step(self, iteration):
        if iteration == 0:
            await self.onStart()
        
        ###EVERY RACE INTSRUCTIONS###
        # self.remember_enemy_units()
        # self.remember_friendly_units()
        await self.distribute_workers()
        
        ###TERRAN INTSRUCTIONS###
        if self.myRace == "Terran":
            await self.buildSCV()
            await self.buildSupplyDepot()
            
        ###ZERG INTSRUCTIONS###
        elif self.myRace == "Zerg":
           print(self.myRace)
        
        ###PROTOSS INTSRUCTIONS###
        elif self.myRace == "Protoss":
            await self.buildPylons()
            await self.buildProbes()
            
    ###FUNCTIONS FOR EVERY RACE###
    async def onStart(self):
        await self.chat_send("(glhf)")
        #Figures out what race the bot is
        if self.townhalls == self.units(COMMANDCENTER):
            self.myRace = "Terran"
        elif self.townhalls == self.units(HATCHERY):
            self.myRace = "Zerg"
        elif self.townhalls == self.units(NEXUS):
            self.myRace = "Protoss"

    ###PROTOSS FUNCTIONS###
    async def buildProbes(self):
        if (self.units(NEXUS).amount * 22) > self.units(PROBE).amount: 
            if self.units(PROBE).amount < 70 and self.can_afford(PROBE):
                for nexus in self.units(NEXUS).noqueue:
                    await self.do(nexus.train(PROBE))

    async def buildPylons(self):
        if self.units(NEXUS).exists:
            nexus = self.units(NEXUS).random
            if self.supply_left <= 8 and self.already_pending(PYLON) < 2 and self.supply_cap < 200:
                if self.can_afford(PYLON):
                    await self.build(PYLON, near=nexus.position.towards(self.game_info.map_center, 8))
    ###TERRAN FUNCTIONS###
     async def buildSCVs(self):
        if (self.townhalls.amount * 22) > self.units(SCV).amount:
            if self.units(SCV).amount < 60 and self.can_afford(SCV):
                for cc in self.townhalls.noqueue:
                    await self.do(cc.train(SCV))

    async def buildSupplyDepots(self):
        if self.units(COMMANDCENTER).exists:
            cc = self.townhalls.random
            if self.supply_left <= 8 and self.already_pending(SUPPLYDEPOT) < 2 and self.supply_cap < 200:
                if self.can_afford(SUPPLYDEPOT):
                    await self.build(SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 8))

    ###ZERG FUNCTIONS###
    
    ###USE FUNCTIONS###
run_game(maps.get("(2)CatalystLE"), [
    # Human(Race.Zerg),
    Bot(Race.Protoss, Trinity()),
    # Bot(Race.Protoss, CannonLoverBot())
    Computer(Race.Zerg, Difficulty.VeryHard)
], realtime=True)

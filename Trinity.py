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
        self.stopArmy = False
        self.stopBuild = False

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
            if self.units(PROBE).amount < 70:
                for nexus in self.units(NEXUS).noqueue:
                    if self.can_afford(PROBE) and not self.stopWorker:
                        await self.do(nexus.train(PROBE))

    async def buildPylons(self):
        if self.units(NEXUS).exists:
            nexus = self.units(NEXUS).random
            if self.supply_left <= 8 and self.already_pending(PYLON) < 2 and self.supply_cap < 200:
                if self.can_afford(PYLON):
                    await self.build(PYLON, near=nexus.position.towards(self.game_info.map_center, 8))
                    
     async def buildGateway(self):
        if self.units(PYLON).exists and self.can_afford(GATEWAY):
            if self.units(GATEWAY).amount < 2* self.townhalls.amount and self.units(GATEWAY).amount < 6:
                pylon = self.units(PYLON).random
                await self.build(GATEWAY, near=pylon.position.towards(self.game_info.map_center))
    async def buildCyber(self):
        if self.units(PYLON).exists and self.units(GATEWAY).exists and self.can_afford(CYBERNETICSCORE):
            if not self.units(CYBERNETICSCORE).exists and not self.already_pending(CYBERNETICSCORE):
                pylon = self.units(PYLON).random
                await self.build(CYBERNETICSCORE, near=pylon)

    async def buildAssimilator(self):
        if self.townhalls.exists:
            hq = self.townhalls.random
            vaspenes = self.state.vespene_geyser.closer_than(15.0, hq)
            if self.townhalls.amount < 6:
                if not self.already_pending(ASSIMILATOR) and (self.units(ASSIMILATOR).amount / (self.townhalls.amount * 1.5)) < 1:
                    for vaspene in vaspenes:
                        if not self.can_afford(ASSIMILATOR):
                            break
                        worker = self.select_build_worker(vaspene.position)
                        if worker is None:
                            break
                        if not self.units(ASSIMILATOR).closer_than(1.0, vaspene).exists:
                            await self.do(worker.build(ASSIMILATOR, vaspene))
            elif self.townhalls.amount > 5:
                if not self.already_pending(ASSIMILATOR):
                    for vaspene in vaspenes:
                        if not self.can_afford(ASSIMILATOR):
                            break
                        worker = self.select_build_worker(vaspene.position)
                        if worker is None:
                            break
                        if not self.units(ASSIMILATOR).closer_than(1.0, vaspene).exists:
                            await self.do(worker.build(ASSIMILATOR, vaspene))

    async def trainZealotsAndStalkers(self):
        if self.units(GATEWAY).exists :
            for gt in self.units(GATEWAY).noqueue:
                if self.units(CYBERNETICSCORE).exists:
                    if self.units(STALKER).amount *2 <  self.units(ZEALOT).amount and self.can_afford(STALKER):
                        await self.do(gt.train(STALKER))
                    elif self.can_afford(ZEALOT):
                        await self.do(gt.train(ZEALOT))
                elif self.can_afford(ZEALOT):
                    await self.do(gt.train(ZEALOT))
    ###TERRAN FUNCTIONS###
    async def buildSCVs(self):
        if (self.townhalls.amount * 22) > self.units(SCV).amount:
            if self.units(SCV).amount < 60:
                for cc in self.townhalls.noqueue:
                    if self.can_afford(SCV) and not self.stopWorker:
                        await self.do(cc.train(SCV))

    async def buildSupplyDepots(self):
        if self.units(COMMANDCENTER).exists:
            cc = self.townhalls.random
            if self.supply_left <= 8 and self.already_pending(SUPPLYDEPOT) < 2 and self.supply_cap < 200:
                if self.can_afford(SUPPLYDEPOT):
                    await self.build(SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 8))
    
     async def buildBarracks(self):
        if self.units(SUPPLYDEPOT).exists and self.can_afford(BARRACKS) and self.townhalls.exists:
            if self.units(BARRACKS).amount < 2 * self.townhalls.amount and self.units(BARRACKS).amount < 6:
                cc = self.townhalls.random
                await self.build(BARRACKS, near=cc.position.towards(self.game_info.map_center, 8))

    async def trainMarine(self):
        if self.units(BARRACKS).exists and self.can_afford(MARINE):
            for br in self.units(BARRACKS).noqueue:
                await self.do(br.train(MARINE))

    ###ZERG FUNCTIONS###
    
     async def buildDrones(self):
        if self.units(LARVA).exists:
            for larva in self.units(LARVA):
                if self.already_pending(DRONE) <= 4 and self.units(DRONE).amount < 80:
                    if self.units(DRONE).amount < 22 * self.townhalls.amount and not self.stopWorker:
                        if self.can_afford(DRONE):
                            await self.do(larva.train(DRONE))
                        
     async def buildOverlords(self):
        if self.units(LARVA).exists:
            for larva in self.units(LARVA):
                if self.supply_cap < 200:
                    if self.supply_left < 7 and self.already_pending(OVERLORD) < 2:
                        if self.can_afford(OVERLORD):
                            await self.do(larva.train(OVERLORD))

        if (self.units(LAIR) | self.units(HIVE)).exists and (self.units(OVERSEER) | self.units(OVERLORDCOCOON)).amount < 2:
            if self.units(OVERLORD).exists and self.can_afford(OVERSEER):
                ov = self.units(OVERLORD).random
                await self.do(ov(MORPH_OVERSEER))

    ###USE FUNCTIONS###
run_game(maps.get("CatalystLE"), [
    # Human(Race.Zerg),
    Bot(Race.Protoss, Trinity()),
    # Bot(Race.Protoss, CannonLoverBot())
    Computer(Race.Zerg, Difficulty.VeryHard)
], realtime=True)

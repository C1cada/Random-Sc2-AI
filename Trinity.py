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
            
    async def attackRally(self):
        for unit in self.armyUnits.idle:
            attack_location = self.get_rally_location()
            await self.do(unit.attack(attack_location))

    async def getGases(self):
        if self.minerals > 0 and self.vespene > 0:
            if (self.minerals / self.vespene) >= 3 and self.gases <= 1:
                self.gases += 0.25
            elif (self.vespene / self.minerals) >= 3 and self.gases >= 1:
                self.gases += -0.25

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
                if self.already_pending(DRONE) <= 2 and self.units(DRONE).amount < 75:
                    if self.units(DRONE).amount < 22 * self.townhalls.amount and not self.stopWorker:
                        if self.can_afford(DRONE):
                            await self.do(larva.train(DRONE))

    async def buildOverlords(self):
        if self.units(LARVA).exists:
            for larva in self.units(LARVA):
                if self.supply_cap < 200:
                    if self.supply_left < 7 and self.already_pending(OVERLORD) < 2:
                        if not self.stopArmy:
                            if self.can_afford(OVERLORD):
                                await self.do(larva.train(OVERLORD))

        if (self.units(LAIR) | self.units(HIVE)).exists and (
                self.units(OVERSEER) | self.units(OVERLORDCOCOON)).amount < 2:
            if self.units(OVERLORD).exists and self.can_afford(OVERSEER):
                ov = self.units(OVERLORD).random
                await self.do(ov(MORPH_OVERSEER))

    async def zergExpand(self):
        expand_every = 2.5 * 60
        prefered_base_count = 2 + int(math.floor(self.get_game_time() / expand_every))
        current_base_count = self.townhalls.amount

        if self.minerals > 900:
            prefered_base_count += 1

        if current_base_count < (len(self.expansion_locations.keys()) - (len(self.expansion_locations.keys()) / 2)):
            if current_base_count < prefered_base_count:
                self.stopWorker = True
                self.stopArmy = True
                self.stopBuild = True
                if self.can_afford(HATCHERY):
                    await self.expandNow(HATCHERY)

        if current_base_count >= prefered_base_count or self.already_pending(HATCHERY):
            self.stopWorker = False
            self.stopArmy = False
            self.stopBuild = False

    async def buildPool(self):
        if self.townhalls.exists:
            if not self.stopBuild:
                if not (self.units(SPAWNINGPOOL).exists or self.already_pending(SPAWNINGPOOL)):
                    hq = self.townhalls.random
                    if self.can_afford(SPAWNINGPOOL):
                        await self.build(SPAWNINGPOOL, near=hq.position.towards(self.game_info.map_center, 8))

    async def buildWarren(self):
        if self.townhalls.exists:
            if not self.stopBuild:
                if self.units(SPAWNINGPOOL).exists and not self.already_pending(ROACHWARREN) and not self.units(ROACHWARREN).exists:
                    hq = self.townhalls.random
                    if self.can_afford(ROACHWARREN):
                        await self.build(ROACHWARREN, near=hq.position.towards(self.game_info.map_center, 8))

    async def hasLair(self):
        if(self.units(LAIR).amount > 0):
            return True
        morphingYet = False
        for h in self.units(HATCHERY):
            if CANCEL_MORPHLAIR in await self.get_available_abilities(h):
                morphingYet = True
                break
        if morphingYet:
            return True
        return False

    async def getLair(self):
        if not self.stopBuild:
            if self.units(HATCHERY).idle.exists:
                hq = self.units(HATCHERY).idle.random
                if self.units(SPAWNINGPOOL).ready.exists and not await self.hasLair():
                    if not self.units(HIVE).exists or self.units(LAIR).exists:
                        if self.can_afford(LAIR):
                            await self.do(hq.build(LAIR))

    async def buildDen(self):
        if not self.stopBuild:
            if self.units(LAIR).exists or self.units(HIVE).exists:
                hq = (self.units(LAIR) | self.units(HIVE)).random
                if not self.already_pending(HYDRALISKDEN) and not self.units(HYDRALISKDEN).exists:
                    if self.can_afford(HYDRALISKDEN):
                        await self.build(HYDRALISKDEN, near=hq.position.towards(self.game_info.map_center, 8))

    async def buildExtractor(self):
        if self.townhalls.exists:
            hq = self.townhalls.random
            if not self.stopBuild:
                vaspenes = self.state.vespene_geyser.closer_than(15.0, hq)
                if self.townhalls.amount < 6:
                    if not self.already_pending(EXTRACTOR) and (
                            self.units(EXTRACTOR).amount / (self.townhalls.amount * self.gases)) < 1:
                        for vaspene in vaspenes:
                            if not self.can_afford(EXTRACTOR):
                                break
                            worker = self.select_build_worker(vaspene.position)
                            if worker is None:
                                break
                            if not self.units(EXTRACTOR).closer_than(1.0, vaspene).exists:
                                await self.do(worker.build(EXTRACTOR, vaspene))
                elif self.townhalls.amount > 5:
                    if not self.already_pending(EXTRACTOR):
                        for vaspene in vaspenes:
                            if not self.can_afford(EXTRACTOR):
                                break
                            worker = self.select_build_worker(vaspene.position)
                            if worker is None:
                                break
                            if not self.units(EXTRACTOR).closer_than(1.0, vaspene).exists:
                                await self.do(worker.build(EXTRACTOR, vaspene))

    async def zergArmy(self):
        if not self.stopArmy:
            if self.units(LARVA).exists:
                for larva in self.units(LARVA):
                    if self.units(SPAWNINGPOOL).exists:
                        if self.units(ROACHWARREN).exists and not self.units(HYDRALISKDEN).exists:
                            await self.trainZerg(ROACH)
                        elif self.units(HYDRALISKDEN).exists and not self.units(ROACHWARREN).exists:
                            await self.trainZerg(HYDRALISK)
                        elif self.units(ROACHWARREN).exists and self.units(HYDRALISKDEN).exists:
                            if self.units(ROACH).amount < self.units(HYDRALISK).amount:
                                await self.trainZerg(ROACH)
                            else:
                                await self.trainZerg(HYDRALISK)
                        else:
                            await self.trainZerg(ZERGLING)

    async def trainZerg(self, unit):
        if not self.stopArmy:
            larva = self.units(LARVA).random
            if self.can_afford(unit):
                await self.do(larva.train(unit))

    async def buildQueens(self):
        if self.townhalls.exists:
            for hq in self.townhalls.noqueue.ready:
                if self.units(SPAWNINGPOOL).ready.exists:
                    if self.units(QUEEN).amount < (self.townhalls.amount * 1.2):
                        if self.can_afford(QUEEN) and self.units(QUEEN).amount < 10:
                            await self.do(hq.train(QUEEN))

    ###USE FUNCTIONS###
    def get_rally_location(self):
        if self.townhalls.exists:
            hq = self.townhalls.closest_to(self.game_info.map_center).position
            rally_location = hq.position.towards(self.game_info.map_center, 8)
            return rally_location

    def get_game_time(self):
        return self.state.game_loop*0.725*(1/16)

    async def expandNow(self, townhall, building=None, max_distance=10, location=None):
        """Takes new expansion."""

        if not building:
            building = self.townhalls.first.type_id

        assert isinstance(building, UnitTypeId)

        if not location:
            location = await self.get_next_expansion()

        if self.can_afford(townhall):
            await self.build(building, near=location, max_distance=max_distance, random_alternative=False,
                             placement_step=1)
            
    async def has_ability(self, ability, unit):
        abilities = await self.get_available_abilities(unit)
        if ability in abilities:
            return True
        else:
            return False

    def get_base_build_location(self, base, min_distance=10, max_distance=15):
        return base.position.towards(self.get_game_center_random(), random.randrange(min_distance, max_distance))

    def get_game_center_random(self, offset_x=50, offset_y=50):
        x = self.game_info.map_center.x
        y = self.game_info.map_center.y

        rand = random.random()
        if rand < 0.2:
            x += offset_x
        elif rand < 0.4:
            x -= offset_x
        elif rand < 0.6:
            y += offset_y
        elif rand < 0.8:
            y -= offset_y

        return sc2.position.Point2((x, y))

run_game(maps.get("CatalystLE"), [
    # Human(Race.Zerg),
    Bot(Race.Protoss, Trinity()),
    # Bot(Race.Protoss, CannonLoverBot())
    Computer(Race.Zerg, Difficulty.VeryHard)
], realtime=True)

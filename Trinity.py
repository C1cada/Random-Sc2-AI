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
        self.injectInterval = 50
        self.creepTargetDistance = 15  # was 10
        self.creepTargetCountsAsReachedDistance = 10  # was 25
        self.creepSpreadInterval = 10
        self.stopMakingNewTumorsWhenAtCoverage = 0.5  # stops queens from putting down new tumors and save up transfuse energy

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
            await self.doQueenInjects(iteration)
            self.assignQueen()
            await self.doCreepSpread()
        
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
                            
    def assignQueen(self):
        maxAmountInjectQueens = self.townhalls.amount
        # # list of all alive queens and bases, will be used for injecting
        if not hasattr(self, "queensAssignedHatcheries"):
            self.queensAssignedHatcheries = {}

        if maxAmountInjectQueens == 0:
            self.queensAssignedHatcheries = {}

        queensNoInjectPartner = self.units(QUEEN).filter(lambda q: q.tag not in self.queensAssignedHatcheries.keys())
        basesNoInjectPartner = self.townhalls.filter(lambda h: h.tag not in self.queensAssignedHatcheries.values() and h.build_progress > 0.8)

        for queen in queensNoInjectPartner:
            if basesNoInjectPartner.amount == 0:
                break
            closestBase = basesNoInjectPartner.closest_to(queen)
            self.queensAssignedHatcheries[queen.tag] = closestBase.tag
            basesNoInjectPartner = basesNoInjectPartner - [closestBase]
            break # else one hatch gets assigned twice

    async def doQueenInjects(self, iteration):
        # list of all alive queens and bases, will be used for injecting
        aliveQueenTags = [queen.tag for queen in self.units(QUEEN)] # list of numbers (tags / unit IDs)
        aliveBasesTags = [base.tag for base in self.townhalls]

        # make queens inject if they have 25 or more energy
        toRemoveTags = []

        if hasattr(self, "queensAssignedHatcheries"):
            for queenTag, hatchTag in self.queensAssignedHatcheries.items():
                # queen is no longer alive
                if queenTag not in aliveQueenTags:
                    toRemoveTags.append(queenTag)
                    continue
                # hatchery / lair / hive is no longer alive
                if hatchTag not in aliveBasesTags:
                    toRemoveTags.append(queenTag)
                    continue
                # queen and base are alive, try to inject if queen has 25+ energy
                queen = self.units(QUEEN).find_by_tag(queenTag)
                hatch = self.townhalls.find_by_tag(hatchTag)
                if hatch.is_ready:
                    if queen.energy >= 25 and queen.is_idle and not hatch.has_buff(QUEENSPAWNLARVATIMER):
                        await self.do(queen(EFFECT_INJECTLARVA, hatch))
                else:
                    if iteration % self.injectInterval == 0 and queen.is_idle and queen.position.distance_to(hatch.position) > 10 and not self.defending_queens:
                        await self.do(queen(AbilityId.MOVE, hatch.position.to2))

            # clear queen tags (in case queen died or hatch got destroyed) from the dictionary outside the iteration loop
            for tag in toRemoveTags:
                self.queensAssignedHatcheries.pop(tag)

    async def updateCreepCoverage(self, stepSize=None):
        if stepSize is None:
            stepSize = self.creepTargetDistance
        ability = self._game_data.abilities[ZERGBUILD_CREEPTUMOR.value]

        positions = [Point2((x, y)) \
                     for x in range(self._game_info.playable_area[0] + stepSize,
                                    self._game_info.playable_area[0] + self._game_info.playable_area[2] - stepSize,
                                    stepSize) \
                     for y in range(self._game_info.playable_area[1] + stepSize,
                                    self._game_info.playable_area[1] + self._game_info.playable_area[3] - stepSize,
                                    stepSize)]

        validPlacements = await self._client.query_building_placement(ability, positions)
        successResults = [
            ActionResult.Success,  # tumor can be placed there, so there must be creep
            ActionResult.CantBuildLocationInvalid,  # location is used up by another building or doodad,
            ActionResult.CantBuildTooFarFromCreepSource,  # - just outside of range of creep
            # ActionResult.CantSeeBuildLocation - no vision here
        ]
        # self.positionsWithCreep = [p for index, p in enumerate(positions) if validPlacements[index] in successResults]
        self.positionsWithCreep = [p for valid, p in zip(validPlacements, positions) if valid in successResults]
        self.positionsWithoutCreep = [p for index, p in enumerate(positions) if
                                      validPlacements[index] not in successResults]
        self.positionsWithoutCreep = [p for valid, p in zip(validPlacements, positions) if valid not in successResults]
        return self.positionsWithCreep, self.positionsWithoutCreep

    async def doCreepSpread(self):
        # only use queens that are not assigned to do larva injects
        allTumors = self.units(CREEPTUMOR) | self.units(CREEPTUMORBURROWED) | self.units(CREEPTUMORQUEEN)

        if not hasattr(self, "usedCreepTumors"):
            self.usedCreepTumors = set()

        # gather all queens that are not assigned for injecting and have 25+ energy
        if hasattr(self, "queensAssignedHatcheries"):
            unassignedQueens = self.units(QUEEN).filter(
                lambda q: (q.tag not in self.queensAssignedHatcheries and q.energy >= 50) and (
                            q.is_idle or len(q.orders) == 1 and q.orders[0].ability.id in [AbilityId.MOVE]))
        else:
            unassignedQueens = self.units(QUEEN).filter(lambda q: q.energy >= 50 and (
                        q.is_idle and q.orders[0].ability.id in [AbilityId.MOVE]))

        # update creep coverage data and points where creep still needs to go
        if not hasattr(self, "positionsWithCreep") or self.iteration % self.creepSpreadInterval * 10 == 0:
            posWithCreep, posWithoutCreep = await self.updateCreepCoverage()
            totalPositions = len(posWithCreep) + len(posWithoutCreep)
            self.creepCoverage = len(posWithCreep) / totalPositions
            # print(self.getTimeInSeconds(), "creep coverage:", creepCoverage)

        # filter out points that have already tumors / bases near them
        if hasattr(self, "positionsWithoutCreep"):
            self.positionsWithoutCreep = [x for x in self.positionsWithoutCreep if
                                          (allTumors | self.townhalls).closer_than(
                                              self.creepTargetCountsAsReachedDistance, x).amount < 1 or (
                                                      allTumors | self.townhalls).closer_than(
                                              self.creepTargetCountsAsReachedDistance + 10,
                                              x).amount < 5]  # have to set this to some values or creep tumors will clump up in corners trying to get to a point they cant reach

        # make all available queens spread creep until creep coverage is reached 50%
        if hasattr(self, "creepCoverage") and (
                self.creepCoverage < self.stopMakingNewTumorsWhenAtCoverage or allTumors.amount - len(
                self.usedCreepTumors) < 25):
            for queen in unassignedQueens:
                # locations = await self.findCreepPlantLocation(self.positionsWithoutCreep, castingUnit=queen, minRange=3, maxRange=30, stepSize=2, locationAmount=16)
                if self.townhalls.ready.exists:
                    locations = await self.findCreepPlantLocation(self.positionsWithoutCreep, castingUnit=queen,
                                                                  minRange=3, maxRange=30, stepSize=2,
                                                                  locationAmount=16)
                    # locations = await self.findCreepPlantLocation(self.positionsWithoutCreep, castingUnit=self.townhalls.ready.random, minRange=3, maxRange=30, stepSize=2, locationAmount=16)
                    if locations is not None:
                        for loc in locations:
                            err = await self.do(queen(BUILD_CREEPTUMOR_QUEEN, loc))
                            if not err:
                                break

        unusedTumors = allTumors.filter(lambda x: x.tag not in self.usedCreepTumors)
        tumorsMadeTumorPositions = set()
        for tumor in unusedTumors:
            tumorsCloseToTumor = [x for x in tumorsMadeTumorPositions if tumor.distance_to(Point2(x)) < 8]
            if len(tumorsCloseToTumor) > 0:
                continue
            abilities = await self.get_available_abilities(tumor)
            if AbilityId.BUILD_CREEPTUMOR_TUMOR in abilities:
                locations = await self.findCreepPlantLocation(self.positionsWithoutCreep, castingUnit=tumor,
                                                              minRange=10,
                                                              maxRange=10)  # min range could be 9 and maxrange could be 11, but set both to 10 and performance is a little better
                if locations is not None:
                    if hasattr(self, "creepCoverage") and (self.creepCoverage < 0.8):
                        for loc in locations:
                            err = await self.do(tumor(BUILD_CREEPTUMOR_TUMOR, loc))
                            if not err:
                                tumorsMadeTumorPositions.add((tumor.position.x, tumor.position.y))
                                self.usedCreepTumors.add(tumor.tag)
                                break

    async def findCreepPlantLocation(self, targetPositions, castingUnit, minRange=None, maxRange=None, stepSize=1,
                                     onlyAttemptPositionsAroundUnit=False, locationAmount=32,
                                     dontPlaceTumorsOnExpansions=True):
        """function that figures out which positions are valid for a queen or tumor to put a new tumor

        Arguments:
            targetPositions {set of Point2} -- For me this parameter is a set of Point2 objects where creep should go towards
            castingUnit {Unit} -- The casting unit (queen or tumor)

        Keyword Arguments:
            minRange {int} -- Minimum range from the casting unit's location (default: {None})
            maxRange {int} -- Maximum range from the casting unit's location (default: {None})
            onlyAttemptPositionsAroundUnit {bool} -- if True, it will only attempt positions around the unit (ideal for tumor), if False, it will attempt a lot of positions closest from hatcheries (ideal for queens) (default: {False})
            locationAmount {int} -- a factor for the amount of positions that will be attempted (default: {50})
            dontPlaceTumorsOnExpansions {bool} -- if True it will sort out locations that would block expanding there (default: {True})

        Returns:
            list of Point2 -- a list of valid positions to put a tumor on
        """

        assert isinstance(castingUnit, Unit)
        positions = []
        ability = self._game_data.abilities[ZERGBUILD_CREEPTUMOR.value]
        if minRange is None: minRange = 0
        if maxRange is None: maxRange = 500

        # get positions around the casting unit
        positions = self.getPositionsAroundUnit(castingUnit, minRange=minRange, maxRange=maxRange, stepSize=stepSize,
                                                locationAmount=locationAmount)

        # stop when map is full with creep
        if len(self.positionsWithoutCreep) == 0:
            return None

        # filter positions that would block expansions
        if dontPlaceTumorsOnExpansions and hasattr(self, "exactExpansionLocations"):
            positions = [x for x in positions if
                         self.getHighestDistance(x.closest(self.exactExpansionLocations), x) > 3]
            # TODO: need to check if this doesnt have to be 6 actually
            # this number cant also be too big or else creep tumors wont be placed near mineral fields where they can actually be placed

        # check if any of the positions are valid
        validPlacements = await self._client.query_building_placement(ability, positions)

        # filter valid results
        validPlacements = [p for index, p in enumerate(positions) if validPlacements[index] == ActionResult.Success]

        allTumors = self.units(CREEPTUMOR) | self.units(CREEPTUMORBURROWED) | self.units(CREEPTUMORQUEEN)
        # usedTumors = allTumors.filter(lambda x:x.tag in self.usedCreepTumors)
        unusedTumors = allTumors.filter(lambda x: x.tag not in self.usedCreepTumors)
        if castingUnit is not None and castingUnit in allTumors:
            unusedTumors = unusedTumors.filter(lambda x: x.tag != castingUnit.tag)

        # filter placements that are close to other unused tumors
        if len(unusedTumors) > 0:
            validPlacements = [x for x in validPlacements if x.distance_to(unusedTumors.closest_to(x)) >= 10]

        validPlacements.sort(key=lambda x: x.distance_to(x.closest(self.positionsWithoutCreep)), reverse=False)

        if len(validPlacements) > 0:
            return validPlacements
        return None


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
    
    def getPositionsAroundUnit(self, unit, minRange=0, maxRange=500, stepSize=1, locationAmount=32):
        # e.g. locationAmount=4 would only consider 4 points: north, west, east, south
        assert isinstance(unit, (Unit, Point2, Point3))
        if isinstance(unit, Unit):
            loc = unit.position.to2
        else:
            loc = unit
        positions = [Point2(( \
            loc.x + distance * math.cos(math.pi * 2 * alpha / locationAmount), \
            loc.y + distance * math.sin(math.pi * 2 * alpha / locationAmount))) \
            for alpha in range(locationAmount) # alpha is the angle here, locationAmount is the variable on how accurate the attempts look like a circle (= how many points on a circle)
            for distance in range(minRange, maxRange+1)] # distance depending on minrange and maxrange
        return positions


run_game(maps.get("CatalystLE"), [
    # Human(Race.Zerg),
    Bot(Race.Protoss, Trinity()),
    # Bot(Race.Protoss, CannonLoverBot())
    Computer(Race.Zerg, Difficulty.VeryHard)
], realtime=True)

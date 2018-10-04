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
        self.armyUnits = None
        self.gases = 1
        self.barracksAddedon = []
        self.facAddedon = []
        self.StarAddedon = []
        self.attackSupply = 190
        self.attacking = False
        self.defendRangeToTownhalls = 15
        self.defending = False
        self.expandTime = 0
        self.order_queue = []
        self.added = False
        self.injectInterval = 50
        self.creepTargetDistance = 15  # was 10
        self.creepTargetCountsAsReachedDistance = 10  # was 25
        self.creepSpreadInterval = 10
        self.stopMakingNewTumorsWhenAtCoverage = 0.5  # stops queens from putting down new tumors and save up transfuse energy
        self.runbyGroup1 = []
        self.runbyGroup2 = []
        self.runbyGroup3 = []
        self.runbyGroup = []
        self.units_to_ignore = [DRONE, SCV, PROBE, EGG, LARVA, OVERLORD, OVERSEER, OBSERVER, BROODLING, INTERCEPTOR,
                                MEDIVAC, CREEPTUMOR, CREEPTUMORBURROWED, CREEPTUMORQUEEN, CREEPTUMORMISSILE]
        self.scouter = None
        self.scout_tag = None
        self.nearby = False
        self.dropMedivac = None
        self.dropMarines = []
        self.rush = False
        self.hqs = [HATCHERY, LAIR, HIVE, COMMANDCENTER, ORBITALCOMMAND, PLANETARYFORTRESS, NEXUS]

    async def on_step(self, iteration):
        if iteration == 1:
            await self.onStart()
        self.iteration = iteration
        self.armyUnits = self.units(ROACH).ready | self.units(ZERGLING).filter(
            lambda z: z.tag not in self.runbyGroup).ready | self.units(HYDRALISK).ready | self.units(
            MARINE).ready | self.units(MARAUDER).ready | self.units(SIEGETANK).ready | self.units(
            ZEALOT).ready | self.units(IMMORTAL).ready | self.units(STALKER).ready | self.units(CORRUPTOR).ready | self.units(BROODLORD).ready | self.units(CARRIER)

        ###EVERY RACE INTSRUCTIONS###
        # self.remember_enemy_units()
        # self.remember_friendly_units()
        await self.attackRally()
        await self.distributeWorkers()
        await self.getGases()
        await self.attack()
        await self.defend()
        await self.expandingTime()
        await self.scout()
        await self.nearbyUnits()
        await self.checkRush()
        await self.armyScout()
        # print(self.barracksAddedon)
        # print(self.expandTime)
        # print(self.stopBuild)
       # print(self.stopWorker)

        ###TERRAN INTSRUCTIONS###
        if self.myRace == "Terran":
            await self.buildSCVs()
            await self.buildSupplyDepots()
            await self.buildRefinery()
            await self.buildBarracks()
            await self.checkAddon()
            await self.buildAdddon()
            await self.landBarracks()
            await self.terranExpand()
            await self.buildBio()
            await self.depoMicro()
            await self.buildFactory()
            await self.transformOrbital()
            await self.callMules()
            await self.checkFacAddon()
            await self.buildFacAdddon()
            await self.landFac()
            await self.buildTanks()
            await self.buildStarport()
            await self.checkStarAddon()
            await self.buildStarAdddon()
            await self.landStar()
            await self.buildStarUnits()
            await self.moveMedic()
            await self.tankMicro()
            await self.stim()
            await self.bioMicro()
            await self.buildBay()
            await self.bayUpgrades()
            await self.buildArmory()
            await self.moveRaven()
            await self.rushTerran()
            await self.turret()
            # await self.chooseMedivac()
            # await self.assignMarines()
            # await self.loadMedivac()
            # await self.moveDrop()


        ###ZERG INTSRUCTIONS###
        elif self.myRace == "Zerg":
            await self.zergExpand()
            await self.upgradeHive()
            await self.buildOverlords()
            await self.buildPool()
            await self.buildWarren()
            await self.getLair()
            await self.buildExtractor()
            await self.buildDrones()
            await self.zergArmy()
            await self.buildDrones()
            await self.buildDen()
            await self.buildQueens()
            await self.doQueenInjects(iteration)
            self.assignQueen()
            await self.doCreepSpread()
            await self.buildInfestation()
            await self.buildSpire()
            await self.greaterSpire()
            await self.broodlords()
            await self.trainLateZerg()
            await self.runby()
            await self.runbyGroupAdding()
            await self.spine()
            await self.roachSpeed()
            await self.lingSpeed()
            await self.hydraRange()
            await self.hydraSpeed()
            await self.burrow()
            await self.burrowMicro()
            await self.moveOverseer()
            await self.upgradesZerg()
            await self.buildEvochamber()
            await self.rushZerg()


        ###PROTOSS INTSRUCTIONS###
        elif self.myRace == "Protoss":
            await self.buildPylons()
            await self.buildProbes()
            await self.handleChronoboost()
            await self.buildGateway()
            await self.buildCyber()
            await self.buildAssimilator()
            await self.protossExpand()
            await self.getWarpgate()
            await self.trainGateway()
            await self.warpGateway()
            await self.buildRobo()
            await self.buildImmo()
            await self.prismMicro()
            await self.charge()
            await self.blink()
            await self.buildTwilight()
            await self.morePrismMicro()
            await self.buildForge()
            await self.upgrades()
            await self.blinkAway()
            await self.stargate()
            await self.fleetBeacon()
            await self.buildCarrier()
            await self.moveObserver()
            await self.rushProtoss()
            await self.cannon()

        await self.execute_order_queue()

    ###FUNCTIONS FOR EVERY RACE###
    async def onStart(self):
        # Figures out what race the bot is
        if self.townhalls == self.units(COMMANDCENTER):
            self.myRace = "Terran"
        elif self.townhalls == self.units(HATCHERY):
            self.myRace = "Zerg"
        elif self.townhalls == self.units(NEXUS):
            self.myRace = "Protoss"
        await self.chat_send("(glhf)")
        await self.chat_send("im " + self.myRace)

    async def attackRally(self):
        if not self.attacking and not self.defending:
            for unit in self.armyUnits.idle:
                attack_location = self.get_rally_location()
                await self.do(unit.attack(attack_location))

    async def getGases(self):
        if self.minerals > 0 and self.vespene > 0:
            if (self.minerals / self.vespene) >= 3 and self.gases <= 2:
                self.gases += 0.25
            elif (self.vespene / self.minerals) >= 3 and self.gases >= 0.5:
                self.gases += -0.25

    async def attack(self):
        if not self.defending:
            if self.supply_used < self.attackSupply - 20:
                self.attacking = False
            if self.supply_used > self.attackSupply or self.attacking:
                self.attacking = True
                for unit in self.armyUnits.idle:
                    await self.do(unit.attack(self.find_target(self.state).position))

        if self.units(HIVE).exists:
            if not self.defending:
                if self.supply_used < self.attackSupply - 20:
                    self.attacking = False
                if (self.supply_used > self.attackSupply and self.units(BROODLORD).amount > 5) or self.attacking:
                    self.attacking = True
                    for unit in self.armyUnits.idle:
                        await self.do(unit.attack(self.find_target(self.state).position))

    async def defend(self):
        enemiesCloseToTh = None
        for th in self.townhalls:
            enemiesCloseToTh = self.known_enemy_units.closer_than(30, th.position)
        if enemiesCloseToTh and not self.attacking:
            self.defending = True
            for unit in self.armyUnits.idle:
                await self.do(unit.attack(enemiesCloseToTh.random.position))
        elif not enemiesCloseToTh:
            self.defending = False

    async def expandingTime(self):
        if self.expandTime == 0:
            if self.myRace == "Terran":
                self.expandTime = 3
            elif self.myRace == "Protoss":
                self.expandTime = 3
            elif self.myRace == "Zerg":
                self.expandTime = 2.5

        if self.get_game_time() > 450 and not self.added:
            self.expandTime += 1
            self.added = True

    async def scout(self):
        if self.workers.exists:
            if self.units.find_by_tag(self.scouter) == None:
                worker = self.workers.random
                self.scouter = worker.tag
                scout = self.workers.find_by_tag(self.scouter)
                if self.get_game_time() < 120:
                    random_exp_location = random.choice(self.enemy_start_locations)
                else:
                    random_exp_location = random.choice(list(self.expansion_locations.keys()))
                await self.do(scout.move(random_exp_location))

            scout = self.workers.find_by_tag(self.scouter)
            if self.get_game_time() < 180:
                random_exp_location = random.choice(self.enemy_start_locations)
            else:
                random_exp_location = random.choice(list(self.expansion_locations.keys()))

            if scout.is_idle:

                await self.do(scout.move(random_exp_location))

            # Basic avoidance: If enemy is too close, go to map center
            nearby_enemy_units = self.known_enemy_units.not_structure.filter(lambda unit: unit.type_id not in self.units_to_ignore).closer_than(5, scout)
            if nearby_enemy_units.exists:

                new_random_exp_location = random.choice(list(self.expansion_locations.keys()))

                random_exp_location = new_random_exp_location
                await self.do(scout.move(random_exp_location))

            # We're close enough, so change target
            if scout.distance_to(random_exp_location) < 1:
                random_exp_location = random.choice(list(self.expansion_locations.keys()))
                await self.do(scout.move(random_exp_location))

    # async def check_enemy_supply(self):
    #     army_units = self.units(ROACH).ready | self.units(HYDRALISK).ready | self.units(OVERSEER).ready | self.units(MUTALISK).ready | self.units(ZERGLING).ready | self.units(BANELING).ready | self.units(BROODLORD).ready | self.units(CORRUPTOR).ready
    #     self.enemy_supply = 0
    #     EnemyUnits = self.remembered_enemy_units.not_structure.filter(lambda x:x.type_id not in self.not_attack_units)
    #     #print(enemyUnitData)
    #     #print(vars(enemyUnitData))
    #     self.enemy_supply = sum([unit._type_data._proto.food_required for unit in EnemyUnits])
    #     self.my_supply = sum([unit._type_data._proto.food_required for unit in army_units])
    #     if self.enemy_supply > (self.my_supply * 1.5) and not self.expanding and not self.emergency and not self.get_game_time() > 180:
    #         self.panic = True
    #         self.stop_worker = True
    #         #print("Panic")
    #     elif self.enemy_supply <= self.my_supply and self.panic:
    #         self.panic = False
    #         self.stop_worker = False

    async def nearbyUnits(self):
        if self.get_game_time() > 300:
            enemiesCloseToTh = None
            for th in self.townhalls.ready:
                enemiesCloseToTh = self.known_enemy_units.closer_than(15, th.position)
            if not enemiesCloseToTh and self.nearby:
                self.stopWorker = False
                self.nearby = False
                self.stopBuild = False
                self.stopArmy = False
                self.attackSupply = 190
            if enemiesCloseToTh:
                if enemiesCloseToTh.amount > 1:
                    # print("yay")
                    self.stopWorker = True
                    self.nearby = True
                    self.stopBuild = True
                    self.stopArmy = False
                    self.attackSupply = 190


    async def checkRush(self):
        if self.get_game_time() < 300:
            for th in self.townhalls:
                if self.known_enemy_structures(PYLON).closer_than(45, th.position).exists or sum([unit._type_data._proto.food_required for unit in self.known_enemy_units.not_structure.filter(lambda unit: unit.type_id not in self.units_to_ignore)]) >= 0.04 * self.get_game_time() or self.known_enemy_structures(BARRACKS).closer_than(45, th.position).exists or self.known_enemy_structures(HATCHERY).closer_than(45, th.position).exists:
                    #print("rush")
                    self.rush = True

    async def armyScout(self):
        # if self.get_game_time() % 120 == 0:
        if self.state.game_loop % 2688 % 600 == 0:
            #print("Scouting")
            if self.myRace == "Terran":
                if self.units(MARINE).exists:
                    marine = self.units(MARINE).random
                    target = self.known_enemy_structures.filter(lambda unit: unit.type_id in self.hqs).closest_to(self.game_info.map_center).position
                    await self.do(marine.attack(target))

            elif self.myRace == "Zerg":
                if self.units(ROACH).exists or self.units(ZERGLING).exists:
                    roach = self.units(ROACH) | self.units(ZERGLING).exists
                    target = self.known_enemy_structures.filter(lambda unit: unit.type_id in self.hqs).closest_to(
                    self.game_info.map_center).position
                    await self.do(roach.random.attack(target))

            elif self.myRace == "Protoss":
                if self.units(ZEALOT).exists:
                    zealot = self.units(ZEALOT).random
                    target = self.known_enemy_structures.filter(lambda unit: unit.type_id in self.hqs).closest_to(
                    self.game_info.map_center).position
                    await self.do(zealot.attack(target))

    async def workerDefence(self):
        if self.get_game_time() < 300:
            enemiesCloseToTh = None
            for th in self.townhalls.ready:
                enemiesCloseToTh = self.known_enemy_units.closer_than(15, th.position)
            if enemiesCloseToTh:
                if self.workers.amount > enemiesCloseToTh.amount * 2:
                    for worker in self.workers.closer_than(15, enemiesCloseToTh.random.position):
                        target = enemiesCloseToTh.random
                        await self.do(worker.attack(target.position))



    ###PROTOSS FUNCTIONS###
    async def buildProbes(self):
        if (self.townhalls.amount * 22) > self.units(PROBE).amount:
            if self.units(PROBE).amount < 60:
                for cc in self.townhalls.noqueue:
                    if self.can_afford(PROBE) and not self.stopWorker:
                        await self.do(cc.train(PROBE))

    async def buildPylons(self):
        if self.units(NEXUS).exists:
            nexus = self.units(NEXUS).random
            if self.supply_left <= 10 and self.already_pending(PYLON) < 2 and self.supply_cap < 200:
                if self.can_afford(PYLON):
                    await self.build(PYLON, near=self.get_base_build_location(nexus, min_distance=5))

    async def buildGateway(self):
        if not self.stopBuild:
            if self.units(PYLON).exists and self.can_afford(GATEWAY):
                if self.units(GATEWAY).amount + self.units(WARPGATE).amount < 1.5 * self.townhalls.amount and self.units(
                        GATEWAY).amount + self.units(WARPGATE).amount < 6:
                    pylon = self.units(PYLON).random
                    await self.build(GATEWAY, near=pylon.position.towards(self.game_info.map_center))

    async def buildCyber(self):
        if not self.stopBuild:
            if self.units(PYLON).exists and self.units(GATEWAY).exists and self.can_afford(CYBERNETICSCORE):
                if not self.units(CYBERNETICSCORE).exists and not self.already_pending(CYBERNETICSCORE):
                    pylon = self.units(PYLON).random
                    await self.build(CYBERNETICSCORE, near=pylon)

    async def buildAssimilator(self):
        if self.townhalls.exists:
            hq = self.townhalls.random
            if not self.stopBuild:
                vaspenes = self.state.vespene_geyser.closer_than(15.0, hq)
                if not self.already_pending(ASSIMILATOR) and (
                        self.units(ASSIMILATOR).amount / (self.townhalls.amount * self.gases)) < 1:
                    for vaspene in vaspenes:
                        if not self.can_afford(ASSIMILATOR):
                            break
                        worker = self.select_build_worker(vaspene.position)
                        if worker is None:
                            break
                        if not self.units(ASSIMILATOR).closer_than(1.0, vaspene).exists:
                            await self.do(worker.build(ASSIMILATOR, vaspene))

    async def handleChronoboost(self):
        if self.units(NEXUS).exists:
            for nexus in self.units(NEXUS):
                if await self.has_ability(EFFECT_CHRONOBOOSTENERGYCOST, nexus) and nexus.energy >= 50:
                    # Always CB Warpgate research first
                    if self.units(CYBERNETICSCORE).ready.exists:
                        cybernetics = self.units(CYBERNETICSCORE).first
                        if not cybernetics.noqueue and not cybernetics.has_buff(CHRONOBOOSTENERGYCOST):
                            await self.do(nexus(EFFECT_CHRONOBOOSTENERGYCOST, cybernetics))
                            return  # Don't CB anything else this step

                    # Blink is also important
                    if self.units(TWILIGHTCOUNCIL).ready.exists:
                        twilight = self.units(TWILIGHTCOUNCIL).first
                        if not twilight.noqueue and not twilight.has_buff(CHRONOBOOSTENERGYCOST):
                            await self.do(nexus(EFFECT_CHRONOBOOSTENERGYCOST, twilight))
                            return  # Don't CB anything else this step

                    # Next, focus on Forge
                    if self.units(FORGE).ready.exists:
                        forge = self.units(FORGE).first
                        if not forge.noqueue and not forge.has_buff(CHRONOBOOSTENERGYCOST):
                            await self.do(nexus(EFFECT_CHRONOBOOSTENERGYCOST, forge))
                            return  # Don't CB anything else this step

                    # Next, prioritize CB on gates
                    for gateway in (self.units(GATEWAY).ready | self.units(WARPGATE).ready):
                        if not gateway.has_buff(CHRONOBOOSTENERGYCOST):
                            await self.do(nexus(EFFECT_CHRONOBOOSTENERGYCOST, gateway))
                            return  # Don't CB anything else this step

                    # Otherwise CB nexus
                    if not nexus.has_buff(CHRONOBOOSTENERGYCOST):
                        await self.do(nexus(EFFECT_CHRONOBOOSTENERGYCOST, nexus))

    async def protossExpand(self):
        expand_every = self.expandTime * 60
        prefered_base_count = 1 + int(math.floor(self.get_game_time() / expand_every))
        current_base_count = self.townhalls.amount

        if self.nearby:
            prefered_base_count = 0

        if self.minerals > 900:
            prefered_base_count += 1

        if current_base_count < (len(self.expansion_locations.keys()) - (len(self.expansion_locations.keys()) / 2)):
            if current_base_count < prefered_base_count:
                self.stopWorker = True
                self.stopArmy = True
                self.stopBuild = True
                if self.can_afford(NEXUS) and not self.already_pending(NEXUS):
                    await self.expandNow(NEXUS)

        if current_base_count >= prefered_base_count or self.already_pending(NEXUS) and not self.nearby:
            self.stopWorker = False
            self.stopArmy = False
            self.stopBuild = False

    async def trainGateway(self):
        if not self.stopArmy:
            if not self.units(FLEETBEACON).exists:
                for gt in self.units(GATEWAY).ready:
                    if gt.noqueue:
                        if await self.has_ability(MORPH_WARPGATE, gt):
                            # if self.can_afford(MORPH_WARPGATE):
                            await self.do(gt(MORPH_WARPGATE))
                            return
                        elif self.known_enemy_units.filter(lambda unit: unit.type_id in [REAPER]):
                            if self.units(CYBERNETICSCORE).exists:
                                if self.can_afford(STALKER):
                                    await self.do(gt.train(STALKER))
                        elif self.can_afford(STALKER) and self.can_afford(ZEALOT):
                            if self.units(CYBERNETICSCORE).exists:
                                if self.units(STALKER).amount * 2 < self.units(ZEALOT).amount:
                                    if self.can_afford(STALKER):
                                        await self.do(gt.train(STALKER))
                                elif self.can_afford(ZEALOT):
                                    await self.do(gt.train(ZEALOT))
                            elif self.can_afford(ZEALOT):
                                await self.do(gt.train(ZEALOT))

    async def warpGateway(self):
        if not self.stopArmy:
            if not self.units(FLEETBEACON).exists:
                for warpgate in self.units(WARPGATE).ready:
                    # We check for WARPGATETRAIN_ZEALOT to see if warpgate is ready to warp in
                    if await self.has_ability(WARPGATETRAIN_ZEALOT, warpgate):
                        if self.units(PYLON).exists:
                            if self.units(WARPPRISMPHASING).exists:
                                pylon = self.units(WARPPRISMPHASING).random
                            else:
                                pylon = self.units(PYLON).ready.random

                            if self.known_enemy_units.filter(lambda unit: unit.type_id in [REAPER]):
                                if self.units(CYBERNETICSCORE).exists:
                                    if self.can_afford(STALKER):
                                        await self.warp_in(STALKER, pylon, warpgate)
                            elif self.units(CYBERNETICSCORE).exists:
                                if self.units(STALKER).amount * 2 < self.units(ZEALOT).amount:
                                    if self.can_afford(STALKER):
                                        await self.warp_in(STALKER, pylon, warpgate)
                                elif self.can_afford(ZEALOT):
                                    await self.warp_in(ZEALOT, pylon, warpgate)
                            elif self.can_afford(ZEALOT):
                                await self.warp_in(ZEALOT, pylon, warpgate)

    async def getWarpgate(self):
        if self.units(CYBERNETICSCORE).ready.exists:
            cybernetics = self.units(CYBERNETICSCORE).first
            if cybernetics.noqueue and await self.has_ability(RESEARCH_WARPGATE, cybernetics):
                if self.can_afford(RESEARCH_WARPGATE):
                    await self.do(cybernetics(RESEARCH_WARPGATE))

    async def warp_in(self, unit, location, warpgate):
        if isinstance(location, sc2.unit.Unit):
            location = location.position.to2
        elif location is not None:
            location = location.to2

        x = random.randrange(-8, 8)
        y = random.randrange(-8, 8)

        placement = sc2.position.Point2((location.x + x, location.y + y))

        action = warpgate.warp_in(unit, placement)
        error = await self._client.actions(action, game_data=self._game_data)

        if not error:
            cost = self._game_data.calculate_ability_cost(action.ability)
            self.minerals -= cost.minerals
            self.vespene -= cost.vespene
            return None
        else:
            return error

    async def buildRobo(self):
        if not self.stopBuild:
            if self.units(CYBERNETICSCORE).ready.exists and self.units(
                    ROBOTICSFACILITY).amount < 0.5 * self.townhalls.amount and self.units(ROBOTICSFACILITY).amount < 2:
                pylon = self.units(PYLON).ready.random
                if self.can_afford(ROBOTICSFACILITY) and not self.already_pending(ROBOTICSFACILITY):
                    await self.build(ROBOTICSFACILITY, near=pylon)

    async def buildTwilight(self):
        if not self.stopBuild:
            if self.units(CYBERNETICSCORE):
                if not self.units(TWILIGHTCOUNCIL).exists:
                    if self.can_afford(TWILIGHTCOUNCIL) and not self.already_pending(TWILIGHTCOUNCIL):
                        pylon = self.units(PYLON).ready.random
                        await self.build(TWILIGHTCOUNCIL, near=pylon)

    async def charge(self):
        if self.units(TWILIGHTCOUNCIL).exists:
            tc = self.units(TWILIGHTCOUNCIL).first
            if tc.noqueue:
                if await self.has_ability(RESEARCH_CHARGE, tc):
                    if self.can_afford(RESEARCH_CHARGE):
                        await self.do(tc(RESEARCH_CHARGE))

    async def blink(self):
        if self.units(TWILIGHTCOUNCIL).exists:
            tc = self.units(TWILIGHTCOUNCIL).first
            if tc.noqueue:
                if await self.has_ability(RESEARCH_BLINK, tc):
                    if self.can_afford(RESEARCH_BLINK):
                        await self.do(tc(RESEARCH_BLINK))

    async def buildImmo(self):
        if not self.units(FLEETBEACON).exists:
            if self.units(ROBOTICSFACILITY).exists:
                if not self.stopArmy:
                    if not self.nearby:
                        for rf in self.units(ROBOTICSFACILITY).ready.noqueue:
                            if not self.units(OBSERVER).exists:
                                await self.do(rf.train(OBSERVER))
                            if self.units(WARPPRISM).amount < 2:
                                await self.do(rf.train(WARPPRISM))
                            if self.can_afford(IMMORTAL):
                                await self.do(rf.train(IMMORTAL))
                    else:
                        for rf in self.units(ROBOTICSFACILITY).ready.noqueue:
                            if self.can_afford(IMMORTAL):
                                await self.do(rf.train(IMMORTAL))


    async def prismMicro(self):
        target = None
        if self.armyUnits.exists:
            lowest_health = self.armyUnits.random
            for prism in self.units(WARPPRISM).ready.idle:
                await self.do(prism.attack(lowest_health.position))

        if self.units(WARPPRISM).exists:
            for immo in self.units(IMMORTAL).ready:
                if immo.shield < 15 and immo.health < immo.health_max / 2:
                    target = immo
                    break
            for prism in self.units(WARPPRISM).idle:
                for passenger in prism.passengers:
                    if passenger.shield > 30:
                        if await self.has_ability(UNLOADALLAT_WARPPRISM, prism):
                            await self.do(prism(UNLOADALLAT_WARPPRISM, prism.position))
                if target:
                    if await self.has_ability(LOAD_WARPPRISM, prism):
                        await self.do(prism(LOAD_WARPPRISM, target))

    async def morePrismMicro(self):
        target = None
        for prism in self.units(WARPPRISM).ready:
            nearby_enemy_units = self.known_enemy_units.closer_than(10, prism)
            if nearby_enemy_units.amount > 5:
                await self.do(prism(MORPH_WARPPRISMPHASINGMODE))

        for prism in self.units(WARPPRISMPHASING).ready:
            nearby_enemy_units = self.known_enemy_units.closer_than(10, prism)
            if nearby_enemy_units.amount < 2:
                await self.do(prism(MORPH_WARPPRISMTRANSPORTMODE))

        for immo in self.units(IMMORTAL).ready:
            if immo.shield < 15 and immo.health < immo.health_max / 2:
                target = immo
                break

        for prism in self.units(WARPPRISMPHASING):
            for passenger in prism.passengers:
                if passenger.shield > 30:
                    if await self.has_ability(UNLOADALLAT_WARPPRISM, prism):
                        await self.do(prism(UNLOADALLAT_WARPPRISM, prism.position))

            if target:
                if await self.has_ability(LOAD_WARPPRISM, prism):
                    await self.do(prism(LOAD_WARPPRISM, target))

    async def buildForge(self):
        if not self.stopBuild:
            if self.units(PYLON).exists:
                if self.units(FORGE).amount < 1:
                    if self.can_afford(FORGE) and not self.already_pending(FORGE):
                        pylon = self.units(PYLON).ready.random
                        await self.build(FORGE, near=pylon)

    async def upgrades(self):
        if not self.stopBuild:
            if self.units(FORGE).exists:
                for forge in self.units(FORGE).ready:
                    if forge.noqueue:
                        for upgrade_level in range(1, 4):
                            upgrade_armor_id = getattr(sc2.constants,
                                                       "FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL" + str(upgrade_level))
                            upgrade_missle_id = getattr(sc2.constants,
                                                        "FORGERESEARCH_PROTOSSGROUNDARMORLEVEL" + str(upgrade_level))
                            upgrade_melee_id = getattr(sc2.constants,
                                                       "FORGERESEARCH_PROTOSSSHIELDSLEVEL" + str(upgrade_level))
                            if await self.has_ability(upgrade_missle_id, forge):
                                if self.can_afford(upgrade_missle_id):
                                    await self.do(forge(upgrade_missle_id))
                            elif await self.has_ability(upgrade_armor_id, forge):
                                if self.can_afford(upgrade_armor_id):
                                    await self.do(forge(upgrade_armor_id))
                            elif await self.has_ability(upgrade_melee_id, forge):
                                if self.can_afford(upgrade_melee_id):
                                    await self.do(forge(upgrade_melee_id))

    async def blinkAway(self):
        home_location = self.start_location
        for st in self.units(STALKER).ready:
            if st.shield < 5 and st.health < st.health_max / 2:
                if await self.has_ability(EFFECT_BLINK_STALKER, st):
                    escape_location = st.position.towards(home_location, 4)
                    await self.do(st(EFFECT_BLINK_STALKER, escape_location))


    async def stargate(self):
        if not self.stopBuild:
            if self.get_game_time() > 800:
                if self.units(STARGATE).amount < 6 and self.units(STARGATE).amount <= self.townhalls.amount:
                    if self.can_afford(STARGATE):
                        pylon = self.units(PYLON).ready.random
                        await self.build(STARGATE, near=pylon)

    async def fleetBeacon(self):
        if not self.stopBuild:
            if self.units(STARGATE).exists:
                if self.can_afford(FLEETBEACON) and not self.already_pending(FLEETBEACON):
                    if not self.units(FLEETBEACON).exists:
                        pylon = self.units(PYLON).ready.random
                        await self.build(FLEETBEACON, near=pylon)

    async def buildCarrier(self):
        if self.units(FLEETBEACON).exists and self.units(STARGATE).exists:
            if not self.stopArmy:
                for rf in self.units(STARGATE).ready.noqueue:
                    await self.do(rf.train(CARRIER))

    async def moveObserver(self):
        if self.armyUnits.exists:
            lowest_health = self.armyUnits.random
            for medic in self.units(OBSERVER).ready.idle:
                await self.do(medic.attack(lowest_health.position))

    async def rushProtoss(self):
        if self.get_game_time() < 300:
            if self.rush:
                self.stopWorker = True
                self.stopBuild = True
                self.nearby = True
                self.stopArmy = False
                self.attackSupply = 70
                if self.units(FORGE).exists:
                    if self.units(PHOTONCANNON).amount < 5:
                        await self.buildCannon()
                for h in self.units(NEXUS):
                    if PROTOSSBUILD_CANCEL in await self.get_available_abilities(h):
                        await self.do(h(PROTOSSBUILD_CANCEL))

    async def buildCannon(self):
        if self.units(PYLON).exists:
            if self.can_afford(PHOTONCANNON):
                pylon = self.units(PYLON).ready.random
                await self.build(PHOTONCANNON, near=pylon)

    async def cannon(self):
        if not self.stopBuild:
            for hq in self.townhalls.ready:
                if self.units(FORGE).exists:
                    if self.units(PHOTONCANNON).closer_than(10, hq).amount < 1:
                        if self.can_afford(PHOTONCANNON) and not self.already_pending(PHOTONCANNON):
                            await self.build(PHOTONCANNON, near=hq)


        ###TERRAN FUNCTIONS###

    async def buildSCVs(self):
        if (self.townhalls.amount * 22) > self.units(SCV).amount:
            if self.units(SCV).amount < 60:
                for cc in self.townhalls.noqueue:
                    if self.can_afford(SCV) and not self.stopWorker:
                        await self.do(cc.train(SCV))

    async def buildSupplyDepots(self):
        if self.townhalls.exists:
            cc = self.townhalls.random
            if self.supply_left <= 10 and self.already_pending(SUPPLYDEPOT) < 3 and self.supply_cap < 200:
                if self.can_afford(SUPPLYDEPOT):
                    await self.build(SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 8))

    async def buildBarracks(self):
        if not self.stopBuild:
            if self.units(SUPPLYDEPOT).exists or self.units(SUPPLYDEPOTLOWERED).exists:
                if self.townhalls.exists:
                    if (self.units(BARRACKS).amount + self.units(BARRACKSFLYING).amount) < 2 * self.townhalls.amount:
                        if (self.units(BARRACKS).amount + self.units(BARRACKSFLYING).amount) < 8:
                            if self.can_afford(BARRACKS):
                                cc = self.townhalls.random
                                await self.build(BARRACKS, near=cc.position.towards(self.game_info.map_center, 8))

    async def buildRefinery(self):
        if self.townhalls.exists:
            hq = self.townhalls.random
            if not self.stopBuild:
                vaspenes = self.state.vespene_geyser.closer_than(15.0, hq)
                if self.townhalls.amount < 6:
                    if not self.already_pending(REFINERY) and (
                            self.units(REFINERY).amount / (self.townhalls.amount * self.gases)) < 1:
                        for vaspene in vaspenes:
                            if not self.can_afford(REFINERY):
                                break
                            worker = self.select_build_worker(vaspene.position)
                            if worker is None:
                                break
                            if not self.units(REFINERY).closer_than(1.0, vaspene).exists:
                                await self.do(worker.build(REFINERY, vaspene))

    async def buildAdddon(self):
        if not self.stopBuild:
            for b in self.units(BARRACKS).ready:
                if b.add_on_tag == 0 and self.units(BARRACKSREACTOR).amount < self.units(BARRACKSTECHLAB).amount:
                    if BUILD_REACTOR_BARRACKS in await self.get_available_abilities(b):
                        if self.can_afford(BUILD_REACTOR):
                            await self.do(b.build(BARRACKSREACTOR))
                            self.barracksAddedon.append(b)
                elif b.add_on_tag == 0:
                    if BUILD_TECHLAB_BARRACKS in await self.get_available_abilities(b):
                        if self.can_afford(BUILD_TECHLAB):
                            await self.do(b.build(BARRACKSTECHLAB))
                            self.barracksAddedon.append(b)

    async def checkAddon(self):
        if self.barracksAddedon:
            for b in self.barracksAddedon:
                if self.iteration % 50 == 0:
                    my_reactors = self.units(BARRACKSREACTOR).tags
                    my_techlabs = self.units(BARRACKSTECHLAB).tags
                    #print(my_techlabs)
                    if await self.buildingAddon():
                        self.barracksAddedon.remove(b)
                    if b.add_on_tag == my_techlabs or b.add_on_tag == my_reactors:
                        self.barracksAddedon.remove(b)
                    elif b.add_on_tag != my_reactors and b.add_on_tag != my_techlabs and await self.has_ability(BUILD_TECHLAB_BARRACKS, b):
                        #print(b.add_on_tag)
                        await self.do(b(LIFT_BARRACKS))

    async def landBarracks(self):
        if self.townhalls.exists:
            cc = self.townhalls.random
            if self.units(BARRACKSFLYING).exists:
                for fb in self.units(BARRACKSFLYING).idle:
                    await self.do(fb(LAND_BARRACKS, self.get_base_build_location(cc)))
                    if fb in self.barracksAddedon:
                        self.barracksAddedon.remove(fb)

    async def buildingAddon(self):
        buildingYet = False
        for b in self.units(BARRACKS):
            if CANCEL_BARRACKSADDON in await self.get_available_abilities(b):
                buildingYet = True
                break
        if buildingYet:
            return True
        return False

    async def terranExpand(self):
        expand_every = self.expandTime * 60
        prefered_base_count = 1 + int(math.floor(self.get_game_time() / expand_every))
        current_base_count = self.townhalls.amount

        if self.nearby:
            prefered_base_count = 0

        if self.minerals > 900:
            prefered_base_count += 1

        if current_base_count < (len(self.expansion_locations.keys()) - (len(self.expansion_locations.keys()) / 2)):
            if current_base_count < prefered_base_count:
                self.stopWorker = True
                self.stopArmy = True
                self.stopBuild = True
                if self.can_afford(COMMANDCENTER) and not self.already_pending(COMMANDCENTER):
                    await self.expandNow(COMMANDCENTER)

        if current_base_count >= prefered_base_count or self.already_pending(COMMANDCENTER) and not self.nearby:
            self.stopWorker = False
            self.stopArmy = False
            self.stopBuild = False

    async def buildBio(self):
        rally_location = self.get_rally_location()
        if self.units(BARRACKS).exists:
            for b in self.units(BARRACKS):
                my_reactors = self.units(BARRACKSREACTOR).tags
                my_techlabs = self.units(BARRACKSTECHLAB).tags
                if b.add_on_tag != my_reactors and b.add_on_tag != my_techlabs:
                    if not self.stopArmy:
                        if b.add_on_tag in my_techlabs:
                            if self.can_afford(MARAUDER) and len(b.orders) < 1:
                                await self.do(b.train(MARAUDER))
                        if b.add_on_tag in my_reactors:
                            if self.minerals > 50 and len(b.orders) < 2:
                                await self.do(b.train(MARINE))


    async def depoMicro(self):
        for depo in self.units(SUPPLYDEPOT).ready:
            await self.do(depo(MORPH_SUPPLYDEPOT_LOWER))

    async def buildFactory(self):
        if not self.stopBuild:
            if self.units(BARRACKS).exists and self.townhalls.exists:
                if (self.units(FACTORY).amount + self.units(FACTORYFLYING).amount) < self.townhalls.amount / 2 and (
                        self.units(FACTORY).amount + self.units(FACTORYFLYING).amount) < 2:
                    if self.can_afford(FACTORY):
                        cc = self.townhalls.random
                        await self.build(FACTORY, near=cc.position.towards(self.game_info.map_center, 8))

    async def callMules(self):
        if self.units(ORBITALCOMMAND).exists:
            for oc in self.units(ORBITALCOMMAND).ready:
                if await self.has_ability(CALLDOWNMULE_CALLDOWNMULE, oc) and oc.energy >= 50:
                    await self.do(oc(CALLDOWNMULE_CALLDOWNMULE, self.state.mineral_field.closest_to(oc)))

    async def transformOrbital(self):
        if not self.stopBuild:
            for cc in self.units(COMMANDCENTER).ready:
                abilities = await self.get_available_abilities(cc)
                if AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND in abilities and self.minerals > 150:
                    await self.do(cc(UPGRADETOORBITAL_ORBITALCOMMAND))

    async def buildFacAdddon(self):
        if not self.stopBuild:
            for b in self.units(FACTORY).ready:
                if b.add_on_tag == 0:
                    if BUILD_TECHLAB_FACTORY in await self.get_available_abilities(b):
                        if self.can_afford(BUILD_TECHLAB):
                            await self.do(b.build(FACTORYTECHLAB))
                            self.facAddedon.append(b)

    async def checkFacAddon(self):
        if self.facAddedon:
            for b in self.facAddedon:
                if self.iteration % 50 == 0:
                    my_techlabs = self.units(FACTORYTECHLAB).tags
                    if await self.buildingFacAddon():
                        self.facAddedon.remove(b)
                    if b.add_on_tag != my_techlabs and await self.has_ability(BUILD_TECHLAB_FACTORY, b):
                        await self.do(b(LIFT_FACTORY))

    async def landFac(self):
        if self.townhalls.exists:
            cc = self.townhalls.random
            if self.units(FACTORYFLYING).exists:
                for fb in self.units(FACTORYFLYING).idle:
                    await self.do(fb(LAND_FACTORY, self.get_base_build_location(cc)))
                    if fb in self.facAddedon:
                        self.facAddedon.remove(fb)

    async def buildingFacAddon(self):
        buildingYet = False
        for b in self.units(FACTORY):
            if CANCEL_FACTORYADDON in await self.get_available_abilities(b):
                buildingYet = True
                break
        if buildingYet:
            return True
        return False

    async def buildTanks(self):
        if not self.stopArmy:
            if self.units(FACTORY).exists:
                for f in self.units(FACTORY).noqueue:
                    if self.can_afford(SIEGETANK):
                        await self.do(f.train(SIEGETANK))

    async def buildStarport(self):
        if not self.stopBuild:
            if self.townhalls.amount > 1:
                if self.units(FACTORY).exists and self.townhalls.exists:
                    if (self.units(STARPORT).amount + self.units(
                            STARPORTFLYING).amount) < self.townhalls.amount / 2 and (
                            self.units(STARPORT).amount + self.units(STARPORTFLYING).amount) < 2:
                        if self.can_afford(STARPORT):
                            cc = self.townhalls.random
                            await self.build(STARPORT, near=cc.position.towards(self.game_info.map_center, 8))

    async def buildStarAdddon(self):
        if not self.stopBuild:
            for b in self.units(STARPORT).ready:
                if b.add_on_tag == 0:
                    if BUILD_TECHLAB_STARPORT in await self.get_available_abilities(b):
                        if self.can_afford(BUILD_TECHLAB):
                            await self.do(b.build(STARPORTTECHLAB))
                            self.StarAddedon.append(b)

    async def checkStarAddon(self):
        if self.StarAddedon:
            for b in self.StarAddedon:
                if self.iteration % 50 == 0:
                    my_techlabs = self.units(STARPORTTECHLAB).tags
                    if await self.buildingStarAddon():
                        self.StarAddedon.remove(b)
                    if b.add_on_tag != my_techlabs and await self.has_ability(BUILD_TECHLAB_STARPORT, b):
                        await self.do(b(LIFT_STARPORT))

    async def landStar(self):
        if self.townhalls.exists:
            cc = self.townhalls.random
            if self.units(STARPORTFLYING).exists:
                for fb in self.units(STARPORTFLYING).idle:
                    await self.do(fb(LAND_STARPORT, self.get_base_build_location(cc)))
                    if fb in self.StarAddedon:
                        self.StarAddedon.remove(fb)

    async def buildingStarAddon(self):
        buildingYet = False
        for b in self.units(STARPORT):
            if CANCEL_STARPORTADDON in await self.get_available_abilities(b):
                buildingYet = True
                break
        if buildingYet:
            return True
        return False

    async def buildStarUnits(self):
        if self.units(STARPORT).exists:
            if not self.stopArmy:
                for rf in self.units(STARPORT).ready.noqueue:
                    if not rf.add_on_tag == 0:
                        if not self.units(RAVEN).exists:
                            await self.do(rf.train(RAVEN))
                        elif self.units(MEDIVAC).amount < 8:
                            await self.do(rf.train(MEDIVAC))

    async def moveMedic(self):
        if self.armyUnits.exists:
            lowest_health = self.armyUnits.random
            for unit in self.armyUnits:
                if unit.health < lowest_health.health:
                    lowest_health = unit
            for medic in self.units(MEDIVAC).ready.idle:
                await self.do(medic.attack(lowest_health.position))

    async def tankMicro(self):
        for tank in self.units(SIEGETANK).ready:
            nearby_enemy_units = self.known_enemy_units.closer_than(15, tank)
            if nearby_enemy_units.amount > 5:
                await self.do(tank(SIEGEMODE_SIEGEMODE))
        for tank in self.units(SIEGETANKSIEGED).ready:
            nearby_enemy_units = self.known_enemy_units.closer_than(15, tank)
            if nearby_enemy_units.amount < 2:
                await self.do(tank(UNSIEGE_UNSIEGE))

    async def stim(self):
        if self.units(BARRACKSTECHLAB).exists:
            tl = self.units(BARRACKSTECHLAB).first
            if tl.noqueue:
                if await self.has_ability(BARRACKSTECHLABRESEARCH_STIMPACK, tl):
                    if self.can_afford(BARRACKSTECHLABRESEARCH_STIMPACK):
                        await self.do(tl(BARRACKSTECHLABRESEARCH_STIMPACK))

    async def bioMicro(self):
        for marine in self.units(MARINE).ready:
            nearby_enemy_units = self.known_enemy_units.closer_than(15, marine)
            if nearby_enemy_units.amount > 2:
                if marine.health == marine.health_max:
                    await self.do(marine(EFFECT_STIM_MARINE))
        for marauder in self.units(MARAUDER).ready:
            nearby_enemy_units = self.known_enemy_units.closer_than(15, marauder)
            if nearby_enemy_units.amount > 2:
                if marauder.health == marauder.health_max:
                    await self.do(marauder(EFFECT_STIM_MARAUDER))

    async def buildBay(self):
        if self.units(ENGINEERINGBAY).amount < 1:
            if self.townhalls.amount > 1:
                if self.can_afford(ENGINEERINGBAY) and not self.already_pending(ENGINEERINGBAY):
                    cc = self.townhalls.random
                    await self.build(ENGINEERINGBAY, near=cc.position.towards(self.game_info.map_center, 8))

    async def bayUpgrades(self):
        if not self.stopBuild:
            if self.units(ENGINEERINGBAY).exists:
                for forge in self.units(ENGINEERINGBAY).ready:
                    if forge.noqueue:
                        for upgrade_level in range(1, 4):
                            upgrade_armor_id = getattr(sc2.constants,
                                                       "ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL" + str(
                                                           upgrade_level))
                            upgrade_missle_id = getattr(sc2.constants,
                                                        "ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL" + str(
                                                            upgrade_level))
                            if await self.has_ability(upgrade_missle_id, forge):
                                if self.can_afford(upgrade_missle_id):
                                    await self.do(forge(upgrade_missle_id))
                            elif await self.has_ability(upgrade_armor_id, forge):
                                if self.can_afford(upgrade_armor_id):
                                    await self.do(forge(upgrade_armor_id))

    async def buildArmory(self):
        if self.units(ARMORY).amount < 1:
            if self.townhalls.exists:
                if self.can_afford(ARMORY) and not self.already_pending(ARMORY):
                    cc = self.townhalls.random
                    await self.build(ARMORY, near=cc.position.towards(self.game_info.map_center, 8))

    async def moveRaven(self):
        if self.armyUnits.exists:
            lowest_health = self.armyUnits.random
            for medic in self.units(RAVEN).ready.idle:
                await self.do(medic.attack(lowest_health.position))

    async def chooseMedivac(self):
        if self.units(MEDIVAC).exists:

            highest_health = self.units(MEDIVAC).random
            for unit in self.units(MEDIVAC).ready:
                if unit.health < highest_health.health:
                    highest_health = unit

            if self.dropMedivac:
                medivac = self.units(MEDIVAC).find_by_tag(self.dropMedivac)
                if not medivac:
                    self.dropMedivac = None

            if not self.dropMedivac:
                self.dropMedivac = highest_health.tag

    async def assignMarines(self):
        if self.dropMedivac:
            medivac = self.units(MEDIVAC).find_by_tag(self.dropMedivac)
            nearbyMarines = self.units(MARINE).ready
            for marine in nearbyMarines:
                print("yo")
                if not self.dropMarines or len(self.dropMarines) < 8:
                    print("hey")
                    dropMarine = marine.tag
                    self.dropMarines.append(dropMarine)

    async def loadMedivac(self):
        if len(self.dropMarines) > 7 and self.dropMedivac:
            print("ready")
            medivac = self.units(MEDIVAC).find_by_tag(self.dropMedivac)
            for marineTag in self.dropMarines:
                print("to")
                marine = self.units(MARINE).find_by_tag(marineTag)
                if marine:
                    print("rumble")
                    if await self.has_ability(LOAD_MEDIVAC, medivac):
                        print("yes")
                        await self.do(medivac(LOAD_MEDIVAC, marine.position))
                else:
                    if not marine.tag in medivac.passengers_tags
                        self.dropMarines.remove(marineTag)
                    
    async def moveDrop(self):
        enemyBase = self.known_enemy_structures.filter(lambda unit: unit.type_id in self.hqs).random
        target = enemyBase.position.towards(self.game_info.map_center, random.randrange(-10,-1)))
        medivac = self.units(MEDIVAC).find_by_tag(self.dropMedivac)
            if medivac.cargo_used > 7:
                if await self.has_ability(UNLOADALLAT_MEDIVAC, medivac):
                    await self.do(medivac(UNLOADALLAT_MEDIVAC, target))
        
    async def rushTerran(self):
        if self.get_game_time() < 300:
            if self.rush:
                self.stopWorker = True
                self.stopBuild = True
                self.nearby = True
                self.stopArmy = False
                self.attackSupply = 70
                if not self.units(BARRACKS).exists:
                    while not self.units(BARRACKS).exists:
                        await self.buildBarracks()
                for h in self.units(COMMANDCENTER):
                    if TERRANBUILDDROP_CANCEL in await self.get_available_abilities(h):
                        await self.do(h(TERRANBUILDDROP_CANCEL))

    async def turret(self):
        if not self.stopBuild:
            for hq in self.townhalls.ready:
                if self.units(ENGINEERINGBAY).exists:
                    if self.units(MISSILETURRET).closer_than(10, hq).amount < 1:
                        if self.can_afford(MISSILETURRET) and not self.already_pending(MISSILETURRET):
                            await self.build(MISSILETURRET, near=hq)

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
                    if self.supply_left < 10 and self.already_pending(OVERLORD) < 2:
                        if not self.stopArmy:
                            if self.can_afford(OVERLORD):
                                await self.do(larva.train(OVERLORD))

        if (self.units(LAIR) | self.units(HIVE)).exists and (
                self.units(OVERSEER) | self.units(OVERLORDCOCOON)).amount < 2:
            if self.units(OVERLORD).exists and self.can_afford(OVERSEER):
                ov = self.units(OVERLORD).random
                await self.do(ov(MORPH_OVERSEER))

    async def zergExpand(self):
        expand_every = self.expandTime * 60
        prefered_base_count = 2 + int(math.floor(self.get_game_time() / expand_every))
        current_base_count = self.townhalls.amount

        if self.nearby:
            prefered_base_count = 0

        if self.minerals > 900:
            prefered_base_count += 1

        if current_base_count < (len(self.expansion_locations.keys()) - (len(self.expansion_locations.keys()) / 2)):
            if current_base_count < prefered_base_count:
                self.stopWorker = True
                self.stopArmy = True
                self.stopBuild = True
                if self.can_afford(HATCHERY) and not self.already_pending(HATCHERY):
                    await self.expandNow(HATCHERY)

        if current_base_count >= prefered_base_count or self.already_pending(HATCHERY) and not self.nearby:
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
                if self.units(SPAWNINGPOOL).exists and not self.already_pending(ROACHWARREN) and not self.units(
                        ROACHWARREN).exists:
                    hq = self.townhalls.random
                    if self.can_afford(ROACHWARREN):
                        await self.build(ROACHWARREN, near=hq.position.towards(self.game_info.map_center, 8))
            elif self.rush:
                if self.units(SPAWNINGPOOL).exists and not self.already_pending(ROACHWARREN) and not self.units(
                        ROACHWARREN).exists:
                    hq = self.townhalls.random
                    if self.can_afford(ROACHWARREN):
                        await self.build(ROACHWARREN, near=hq.position.towards(self.game_info.map_center, 8))

    async def hasLair(self):
        if (self.units(LAIR).amount > 0):
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

    async def zergArmy(self):
        if not self.stopArmy:
            if not self.units(HIVE).exists:
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
        basesNoInjectPartner = self.townhalls.filter(
            lambda h: h.tag not in self.queensAssignedHatcheries.values() and h.build_progress > 0.8)

        for queen in queensNoInjectPartner:
            if basesNoInjectPartner.amount == 0:
                break
            closestBase = basesNoInjectPartner.closest_to(queen)
            self.queensAssignedHatcheries[queen.tag] = closestBase.tag
            basesNoInjectPartner = basesNoInjectPartner - [closestBase]
            break  # else one hatch gets assigned twice

    async def doQueenInjects(self, iteration):
        # list of all alive queens and bases, will be used for injecting
        aliveQueenTags = [queen.tag for queen in self.units(QUEEN)]  # list of numbers (tags / unit IDs)
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
                    if iteration % self.injectInterval == 0 and queen.is_idle and queen.position.distance_to(
                            hatch.position) > 10:
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

    async def buildInfestation(self):
        if self.units(LAIR).exists:
            if self.get_game_time() > 550:
                if not self.already_pending(INFESTATIONPIT) and not self.units(INFESTATIONPIT).exists:
                    if self.can_afford(INFESTATIONPIT):
                        hq = self.townhalls.random
                        await self.build(INFESTATIONPIT, near=hq.position.towards(self.game_info.map_center, 8))

    async def buildSpire(self):
        if self.units(LAIR).exists or self.units(HIVE).exists:
            if self.get_game_time() > 550:
                if not self.already_pending(SPIRE) and not self.units(SPIRE).exists and self.units(
                        GREATERSPIRE).amount + self.already_pending(GREATERSPIRE) < 1:
                    if self.can_afford(SPIRE):
                        hq = self.townhalls.random
                        await self.build(SPIRE, near=hq.position.towards(self.game_info.map_center, 8))

    async def upgradeHive(self):
        hive = None
        if self.units(LAIR).idle.exists and not self.units(HIVE).exists and self.units(INFESTATIONPIT):
            self.stopArmy = True
            self.stopWorker = True
            hive = True
            if self.can_afford(THOR):
                hq = self.units(LAIR).idle.first
                await self.do(hq.build(HIVE))
                hive = False
        elif hive == False:
            self.stopArmy = False
            self.stopWorker = False


    async def greaterSpire(self):
        if self.units(HIVE).exists and self.units(GREATERSPIRE).amount + self.already_pending(GREATERSPIRE) < 1:
            if not self.units(GREATERSPIRE).exists and self.units(SPIRE).ready.idle.exists and self.already_pending(
                    GREATERSPIRE) < 1:
                if self.can_afford(GREATERSPIRE):
                    await self.do(self.units(SPIRE).ready.idle.random(UPGRADETOGREATERSPIRE_GREATERSPIRE))

    async def trainLateZerg(self):
        if not self.stopArmy:
            if self.units(HIVE).exists:
                if self.units(LARVA).exists:
                    for larva in self.units(LARVA):
                        if self.units(SPAWNINGPOOL).exists and self.units(ZERGLING).amount + self.already_pending(ZERGLING) < 40:
                            await self.trainZerg(ZERGLING)
                        if self.units(SPIRE).exists or self.units(GREATERSPIRE).exists:
                            await self.trainZerg(CORRUPTOR)

    async def runbyGroupAdding(self):
        if self.units(HIVE).exists:
            for z in self.units(ZERGLING).filter(lambda z: z.tag not in self.runbyGroup).ready:
                if len(self.runbyGroup1) < 20 and z not in self.runbyGroup and z not in self.runbyGroup2:
                    # print("1")
                    self.runbyGroup1.append(z.tag)
                    self.runbyGroup.append(z.tag)

                elif len(self.runbyGroup2) < 20 and z not in self.runbyGroup and z not in self.runbyGroup1:
                    # print("2")
                    self.runbyGroup2.append(z.tag)
                    self.runbyGroup.append(z.tag)

    async def runby(self):
        if self.runbyGroup1:
            runby1Done = True
            target = random.choice(list(self.expansion_locations.keys()))
            for zerglingTag in self.runbyGroup1:
                zergling = self.units(ZERGLING).find_by_tag(zerglingTag)
                if not zergling:
                    self.runbyGroup1.remove(zerglingTag)
                    self.runbyGroup.remove(zerglingTag)

                if zergling:
                    if not zergling.is_idle:
                        runby1Done = False

            for zerglingTag in self.runbyGroup1:
                zergling = self.units(ZERGLING).find_by_tag(zerglingTag)
                if zergling:
                    if runby1Done:
                        await self.do(zergling.attack(target))


        if self.runbyGroup2:
            runby1Done = True
            target = random.choice(list(self.expansion_locations.keys()))
            for zerglingTag in self.runbyGroup2:
                zergling = self.units(ZERGLING).find_by_tag(zerglingTag)
                if not zergling:
                    self.runbyGroup2.remove(zerglingTag)
                    self.runbyGroup.remove(zerglingTag)

                if zergling:
                    if not zergling.is_idle:
                        runby1Done = False

            for zerglingTag in self.runbyGroup2:
                zergling = self.units(ZERGLING).find_by_tag(zerglingTag)
                if zergling:
                    if runby1Done:
                        await self.do(zergling.attack(target))

    async def spine(self):
        if not self.stopBuild:
            for hq in self.townhalls.ready:
                if self.units(SPAWNINGPOOL).exists:
                    if self.units(SPINECRAWLER).closer_than(10, hq).amount < 1:
                        if self.can_afford(SPINECRAWLER) and not self.already_pending(SPINECRAWLER):
                            await self.build(SPINECRAWLER, near=hq)

    async def roachSpeed(self):
        if self.units(ROACHWARREN).exists:
            rw = self.units(ROACHWARREN).first
            if rw.noqueue:
                if (self.units(LAIR).exists or self.units(HIVE).exists) and not self.already_pending(LAIR):
                    if await self.has_ability(RESEARCH_GLIALREGENERATION, rw):
                        if self.can_afford(RESEARCH_GLIALREGENERATION):
                            await self.do(rw(RESEARCH_GLIALREGENERATION))

    async def lingSpeed(self):
        if self.units(SPAWNINGPOOL).exists:
            rw = self.units(SPAWNINGPOOL).first
            if rw.noqueue:
                if await self.has_ability(RESEARCH_ZERGLINGMETABOLICBOOST, rw):
                    if self.can_afford(RESEARCH_ZERGLINGMETABOLICBOOST):
                        await self.do(rw(RESEARCH_ZERGLINGMETABOLICBOOST))

    async def hydraRange(self):
        if self.units(HYDRALISKDEN).exists:
            rw = self.units(HYDRALISKDEN).first
            if rw.noqueue:
                if await self.has_ability(RESEARCH_GROOVEDSPINES, rw):
                    if self.can_afford(RESEARCH_GROOVEDSPINES):
                        await self.do(rw(RESEARCH_GROOVEDSPINES))

    async def hydraSpeed(self):
        if self.units(HYDRALISKDEN).exists:
            rw = self.units(HYDRALISKDEN).first
            if rw.noqueue:
                if await self.has_ability(RESEARCH_MUSCULARAUGMENTS, rw):
                    if self.can_afford(RESEARCH_MUSCULARAUGMENTS):
                        await self.do(rw(RESEARCH_MUSCULARAUGMENTS))

    async def burrow(self):
        if self.townhalls.exists:
            rw = self.townhalls.first
            if rw.noqueue:
                if await self.has_ability(RESEARCH_BURROW, rw):
                    if self.can_afford(RESEARCH_BURROW):
                        await self.do(rw(RESEARCH_BURROW))

    async def burrowMicro(self):
        for unit in self.units(ROACH).ready:
            nearby_enemy_units = self.known_enemy_units.closer_than(10, unit)
            if unit.health / unit.health_max < 3/10 and nearby_enemy_units.amount > 2:
                abilities = await self.get_available_abilities(unit)
                if AbilityId.BURROWDOWN_ROACH in abilities and self.can_afford(BURROWDOWN_ROACH):
                    await self.do(unit(BURROWDOWN_ROACH))

        for unit in self.units(ROACHBURROWED).ready:
            nearby_enemy_units = self.known_enemy_units.closer_than(10, unit)
            if (unit.health / unit.health_max > 6 / 10 or nearby_enemy_units.amount < 2) and unit.is_burrowed:
                abilities = await self.get_available_abilities(unit)
                if AbilityId.BURROWUP_ROACH in abilities and self.can_afford(BURROWUP_ROACH):
                    await self.do(unit(BURROWUP_ROACH))

        for unit in self.units(HYDRALISK).ready:
            nearby_enemy_units = self.known_enemy_units.closer_than(10, unit)
            if unit.health / unit.health_max < 3/10 and nearby_enemy_units.amount > 2:
                abilities = await self.get_available_abilities(unit)
                if AbilityId.BURROWDOWN_HYDRALISK in abilities and self.can_afford(BURROWDOWN_HYDRALISK):
                    await self.do(unit(BURROWDOWN_HYDRALISK))

        for unit in self.units(HYDRALISKBURROWED).ready:
            nearby_enemy_units = self.known_enemy_units.closer_than(10, unit)
            if (unit.health / unit.health_max > 6 / 10 or nearby_enemy_units.amount < 2) and unit.is_burrowed:
                abilities = await self.get_available_abilities(unit)
                if AbilityId.BURROWUP_HYDRALISK in abilities and self.can_afford(BURROWUP_HYDRALISK):
                    await self.do(unit(BURROWUP_HYDRALISK))

    async def moveOverseer(self):
        if self.armyUnits.exists:
            lowest_health = self.armyUnits.random
            for medic in self.units(OVERSEER).ready.idle:
                await self.do(medic.attack(lowest_health.position))

    async def broodlords(self):
        armyCount = self.units(BROODLORD).amount | self.units(CORRUPTOR).amount
        broodlordsTotal = self.units(BROODLORD).amount + self.units(BROODLORDCOCOON).amount
        if armyCount > 0:
            for c in self.units(CORRUPTOR).ready:
                if (broodlordsTotal/armyCount) < 0.4:
                    #print("ready")
                    if self.can_afford(BROODLORD):
                        await self.do(c(MORPHTOBROODLORD_BROODLORD))

    async def upgradesZerg(self):
        if self.units(HIVE).exists:
            if not self.stopBuild:
                if self.units(EVOLUTIONCHAMBER).exists:
                    for evochamber in self.units(EVOLUTIONCHAMBER).ready:
                        if evochamber.noqueue:
                    # Go through each weapon, armor and shield upgrade and check if we can research it, and if so, do it
                            for upgrade_level in range(1, 4):
                                upgrade_armor_id = getattr(sc2.constants, "RESEARCH_ZERGGROUNDARMORLEVEL" + str(upgrade_level))
                                upgrade_missle_id = getattr(sc2.constants, "RESEARCH_ZERGMELEEWEAPONSLEVEL" + str(upgrade_level))
                                if await self.has_ability(upgrade_missle_id, evochamber):
                                    if self.can_afford(upgrade_missle_id):
                                        await self.do(evochamber(upgrade_missle_id))
                                elif await self.has_ability(upgrade_armor_id, evochamber):
                                    if self.can_afford(upgrade_armor_id):
                                        await self.do(evochamber(upgrade_armor_id))

                if self.units(GREATERSPIRE).exists:
                    evochamber = self.units(GREATERSPIRE).first
                    # Only if we're not upgrading anything yet
                    if evochamber.noqueue:
                        # Go through each weapon, armor and shield upgrade and check if we can research it, and if so, do it
                        for upgrade_level in range(1, 4):
                            upgrade_armor_id = getattr(sc2.constants,
                                                       "RESEARCH_ZERGFLYERATTACKLEVEL" + str(upgrade_level))
                            upgrade_missle_id = getattr(sc2.constants,
                                                        "RESEARCH_ZERGFLYERARMORLEVEL" + str(upgrade_level))
                            if await self.has_ability(upgrade_missle_id, evochamber):
                                if self.can_afford(upgrade_missle_id):
                                    await self.do(evochamber(upgrade_missle_id))
                            elif await self.has_ability(upgrade_armor_id, evochamber):
                                if self.can_afford(upgrade_armor_id):
                                    await self.do(evochamber(upgrade_armor_id))
        else:
            if not self.stopBuild:
                if self.units(EVOLUTIONCHAMBER).exists:
                    for evochamber in self.units(EVOLUTIONCHAMBER).ready:
                        if evochamber.noqueue:
                            # Go through each weapon, armor and shield upgrade and check if we can research it, and if so, do it
                            for upgrade_level in range(1, 4):
                                upgrade_armor_id = getattr(sc2.constants,
                                                           "RESEARCH_ZERGGROUNDARMORLEVEL" + str(upgrade_level))
                                upgrade_missle_id = getattr(sc2.constants,
                                                            "RESEARCH_ZERGMISSILEWEAPONSLEVEL" + str(upgrade_level))
                                if await self.has_ability(upgrade_missle_id, evochamber):
                                    if self.can_afford(upgrade_missle_id):
                                        await self.do(evochamber(upgrade_missle_id))
                                elif await self.has_ability(upgrade_armor_id, evochamber):
                                    if self.can_afford(upgrade_armor_id):
                                        await self.do(evochamber(upgrade_armor_id))


    async def buildEvochamber(self):
        if self.townhalls.exists:
            if self.units(LAIR).exists or self.units(HIVE).exists:
                if self.can_afford(EVOLUTIONCHAMBER) and self.already_pending(EVOLUTIONCHAMBER) < 2 and self.units(
                        EVOLUTIONCHAMBER).amount < 2:
                    hq = self.townhalls.random
                    await self.build(EVOLUTIONCHAMBER, near=hq.position.towards(self.game_info.map_center, 8))
    async def rushZerg(self):
        if self.get_game_time() < 300:
            if self.rush:
                self.stopWorker = True
                self.stopBuild = True
                self.nearby = True
                self.stopArmy = False
                self.attackSupply = 70
                if not self.units(SPAWNINGPOOL).exists:
                    while not self.units(SPAWNINGPOOL).exists:
                        await self.buildPool()
                if self.units(SPAWNINGPOOL).exists:
                    if self.units(SPINECRAWLER).amount < 5:
                        await self.buildSpine()
                for h in self.units(HATCHERY):
                    if ZERGBUILD_CANCEL in await self.get_available_abilities(h):
                        await self.do(h(ZERGBUILD_CANCEL))

    async def buildSpine(self):
        if self.townhalls.exists:
            if self.can_afford(SPINECRAWLER):
                hatch = self.townhalls.random
                await self.build(SPINECRAWLER, near=hatch)



    ###USE FUNCTIONS###
    def get_rally_location(self):
        if self.townhalls.exists:
            hq = self.townhalls.closest_to(self.game_info.map_center).position
            rally_location = hq.position.towards(self.game_info.map_center, 6)
            return rally_location

    def get_game_time(self):
        return self.state.game_loop * 0.725 * (1 / 16)

    async def expandNow(self, townhall, building=None, max_distance=10, location=None):
        """Takes new expansion."""

        # if not building:
        #     building = self.townhalls.first.type_id
        #
        # assert isinstance(building, UnitTypeId)

        if not location:
            location = await self.get_next_expansion()

        if self.can_afford(townhall):
            await self.build(townhall, near=location, max_distance=max_distance, random_alternative=False,
                             placement_step=1)

    async def has_ability(self, ability, unit):
        abilities = await self.get_available_abilities(unit)
        if ability in abilities:
            return True
        else:
            return False

    def get_base_build_location(self, base, min_distance=2, max_distance=15):
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

    def find_target(self, state):
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        else:
            return self.enemy_start_locations[0]

    async def execute_order_queue(self):
        await self._client.actions(self.order_queue, game_data=self._game_data)
        self.order_queue = []  # Reset order queue

    async def do(self, action):

        self.order_queue.append(action)  # await self._client.actions(action, game_data=self._game_data)

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
            for alpha in range(locationAmount)
            # alpha is the angle here, locationAmount is the variable on how accurate the attempts look like a circle (= how many points on a circle)
            for distance in range(minRange, maxRange + 1)]  # distance depending on minrange and maxrange
        return positions

    def has_order(self, orders, units):
        if type(orders) != list:
            orders = [orders]

        count = 0

        if type(units) == sc2.unit.Unit:
            unit = units
            if len(unit.orders) >= 1 and unit.orders[0].ability.id in orders:
                count += 1
        else:
            for unit in units:
                if len(unit.orders) >= 1 and unit.orders[0].ability.id in orders:
                  count += 1

        return count

    async def order(self, units, order, target=None, silent=True):
        if type(units) != list:
            unit = units
            await self.do(unit(order, target=target))
        else:
            for unit in units:
                await self.do(unit(order, target=target))

    async def distributeWorkers(self):
        """
        Distributes workers across all the bases taken.
        WARNING: This is quite slow when there are lots of workers or multiple bases.
        """

        # TODO:
        # OPTIMIZE: Assign idle workers smarter
        # OPTIMIZE: Never use same worker mutltiple times

        expansion_locations = self.expansion_locations
        owned_expansions = self.owned_expansions
        worker_pool = []
        for idle_worker in self.workers.idle:
            if idle_worker.tag != self.scouter:
                mf = self.state.mineral_field.closest_to(idle_worker)
                await self.do(idle_worker.gather(mf))

        for location, townhall in owned_expansions.items():
            workers = self.workers.closer_than(20, location)
            actual = townhall.assigned_harvesters
            ideal = townhall.ideal_harvesters
            excess = actual - ideal
            if actual > ideal:
                worker_pool.extend(workers.random_group_of(min(excess, len(workers))))
                continue
        for g in self.geysers:
            workers = self.workers.closer_than(5, g)
            actual = g.assigned_harvesters
            ideal = g.ideal_harvesters
            excess = actual - ideal
            if actual > ideal:
                worker_pool.extend(workers.random_group_of(min(excess, len(workers))))
                continue

        for g in self.geysers:
            actual = g.assigned_harvesters
            ideal = g.ideal_harvesters
            deficit = ideal - actual

            for x in range(0, deficit):
                if worker_pool:
                    w = worker_pool.pop()
                    if w.tag != self.scouter:
                        if len(w.orders) == 1 and w.orders[0].ability.id in [AbilityId.HARVEST_RETURN]:
                            await self.do(w.move(g))
                            await self.do(w.return_resource(queue=True))
                        else:
                            await self.do(w.gather(g))

        for location, townhall in owned_expansions.items():
            actual = townhall.assigned_harvesters
            ideal = townhall.ideal_harvesters

            deficit = ideal - actual
            for x in range(0, deficit):
                if worker_pool:
                    w = worker_pool.pop()
                    mf = self.state.mineral_field.closest_to(townhall)
                    if w.tag != self.scouter:
                        if len(w.orders) == 1 and w.orders[0].ability.id in [AbilityId.HARVEST_RETURN]:
                            await self.do(w.move(townhall))
                            await self.do(w.return_resource(queue=True))
                            await self.do(w.gather(mf, queue=True))
                        else:
                            await self.do(w.gather(mf))

# for i in range(10):
# run_game(maps.get("AcidPlantLE"), [
#     # Human(Race.Zerg),
#     # Bot(Race.Terran, Trinity()),
#     # Bot(Race.Zerg, Trinity()),
#     # Bot(Race.Protoss, Trinity()),
#     Bot(Race.Random, Trinity()),
#     Computer(Race.Random, Difficulty.VeryHard)
# ], realtime=True)

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
        # self.remember_enemy_units()
        # self.remember_friendly_units()
        await self.distribute_workers()

        if self.myRace == "Terran":
            print(self.myRace)
        elif self.myRace == "Zerg":
           print(self.myRace)
        elif self.myRace == "Protoss":
            await self.buildPylons()
            await self.buildProbes()

    async def onStart(self):
        await self.chat_send("(glhf)")
        if self.townhalls == self.units(COMMANDCENTER):
            self.myRace = "Terran"
        elif self.townhalls == self.units(HATCHERY):
            self.myRace = "Zerg"
        elif self.townhalls == self.units(NEXUS):
            self.myRace = "Protoss"

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


    def remember_enemy_units(self):
        # Every 60 seconds, clear all remembered units (to clear out killed units)
        # if round(self.get_game_time() % 60) == 0:
        #    self.remembered_enemy_units_by_tag = {}

        # Look through all currently seen units and add them to list of remembered units (override existing)
        for unit in self.known_enemy_units:
            unit.is_known_this_step = True
            self.remembered_enemy_units_by_tag[unit.tag] = unit

        # Convert to an sc2 Units object and place it in self.remembered_enemy_units
        self.remembered_enemy_units = sc2.units.Units([], self._game_data)
        for tag, unit in list(self.remembered_enemy_units_by_tag.items()):
            # Make unit.is_seen = unit.is_visible
            if unit.is_known_this_step:
                unit.is_seen = unit.is_visible  # There are known structures that are not visible
                unit.is_known_this_step = False  # Set to false for next step
            else:
                unit.is_seen = False

            # Units that are not visible while we have friendly units nearby likely don't exist anymore, so delete them
            if not unit.is_seen and self.units.closer_than(7, unit).exists:
                del self.remembered_enemy_units_by_tag[tag]
                continue

            self.remembered_enemy_units.append(unit)

    def remember_friendly_units(self):
        for unit in self.units:
            unit.is_taking_damage = False

            # If we already remember this friendly unit
            if unit.tag in self.remembered_friendly_units_by_tag:
                health_old = self.remembered_friendly_units_by_tag[unit.tag].health
                shield_old = self.remembered_friendly_units_by_tag[unit.tag].shield

                # Compare its health/shield since last step, to find out if it has taken any damage
                if unit.health < health_old or unit.shield < shield_old:
                    unit.is_taking_damage = True

            self.remembered_friendly_units_by_tag[unit.tag] = unit

run_game(maps.get("(2)CatalystLE"), [
    # Human(Race.Zerg),
    Bot(Race.Protoss, Trinity()),
    # Bot(Race.Protoss, CannonLoverBot())
    Computer(Race.Zerg, Difficulty.VeryHard)
], realtime=True)

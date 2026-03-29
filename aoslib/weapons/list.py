from shared.constants import *
from grenadeTool import GrenadeTool
from classicGrenadeTool import ClassicGrenadeTool
from antipersonnelGrenadeTool import AntipersonnelGrenadeTool
from classicRifleWeapon import ClassicRifleWeapon
from smgWeapon import SMGWeapon
from minigunWeapon import MinigunWeapon
from shotgunWeapon import ShotgunWeapon
from shotgun2Weapon import Shotgun2Weapon
from blockTool import BlockTool
from pickAxeTool import PickAxeTool
from ugcPickAxeTool import UGCPickAxeTool
from knifeTool import KnifeTool
from spadeTool import SpadeTool
from superSpadeTool import SuperSpadeTool
from ugcSuperSpadeTool import UGCSuperSpadeTool
from classicSpadeTool import ClassicSpadeTool
from prefabTool import PrefabTool
from rpgWeapon import RPGWeapon
from rpg2Weapon import RPG2Weapon
from ugcRPG2Weapon import UGCRPG2Weapon
from drillgunWeapon import DrillgunWeapon
from ugcDrillgunWeapon import UGCDrillgunWeapon
from mgWeapon import MGWeapon
from rocketTurretWeapon import RocketTurretWeapon
from pistolWeapon import PistolWeapon
from sniperWeapon import SniperWeapon
from sniper2Weapon import Sniper2Weapon
from landmineWeapon import LandmineWeapon
from dynamiteWeapon import DynamiteWeapon
from flareBlockTool import FlareBlockTool
from zombieHandTool import ZombieHandTool
from bombTool import BombTool
from diamondTool import DiamondTool
from intelTool import IntelTool
from zombiePrefabTool import ZombiePrefabTool
from snowBlowerWeapon import SnowBlowerWeapon
from ugcSnowBlowerWeapon import UGCSnowBlowerWeapon
from molotovWeapon import MolotovWeapon
from crowbarTool import CrowbarTool
from tommyGunWeapon import TommyGunWeapon
from snubPistolWeapon import SnubPistolWeapon
from classicShotgunWeapon import ClassicShotgunWeapon
from classicSmgWeapon import ClassicSmgWeapon
from nullTool import NullTool
from ugcTool import UGCTool
from fakePistolTool import FakePistolTool
from ugcPrefabTool import UGCPrefabTool
from paintbrushTool import PaintbrushTool
from riotStickTool import RiotStickTool
from macheteTool import MacheteTool
from medPackWeapon import MedPackWeapon
from riotShieldTool import RiotShieldTool
from autoPistolWeapon import AutoPistolWeapon
from chemicalbombWeapon import ChemicalBombWeapon
from grenadeLauncherWeapon import GrenadeLauncherWeapon
from stickygrenadeWeapon import StickyGrenadeWeapon
from radarStationWeapon import RadarStationWeapon
from c4Weapon import C4Weapon
from assaultRifleWeapon import AssaultRifleWeapon
from lightMachineGunWeapon import LightMachineGunWeapon
from autoShotgunWeapon import AutoShotgunWeapon
from blockSuckerWeapon import BlockSuckerWeapon
from disguiseTool import DisguiseTool
from mineLauncherWeapon import MineLauncherWeapon
WEAPONS = {GRENADE_TOOL: GrenadeTool, 
   CLASSIC_GRENADE_TOOL: ClassicGrenadeTool, 
   ANTIPERSONNEL_GRENADE_TOOL: AntipersonnelGrenadeTool, 
   RIFLE_TOOL: ClassicRifleWeapon, 
   SMG_TOOL: SMGWeapon, 
   MINIGUN_TOOL: MinigunWeapon, 
   SHOTGUN_TOOL: ShotgunWeapon, 
   SHOTGUN2_TOOL: Shotgun2Weapon, 
   RPG_TOOL: RPGWeapon, 
   RPG2_TOOL: RPG2Weapon, 
   UGC_RPG2_TOOL: UGCRPG2Weapon, 
   SNOWBLOWER_TOOL: SnowBlowerWeapon, 
   UGC_SNOWBLOWER_TOOL: UGCSnowBlowerWeapon, 
   DRILLGUN_TOOL: DrillgunWeapon, 
   UGC_DRILLGUN_TOOL: UGCDrillgunWeapon, 
   MG_TOOL: MGWeapon, 
   ROCKET_TURRET_TOOL: RocketTurretWeapon, 
   PISTOL_TOOL: PistolWeapon, 
   SNIPER_TOOL: SniperWeapon, 
   SNIPER2_TOOL: Sniper2Weapon, 
   LANDMINE_TOOL: LandmineWeapon, 
   DYNAMITE_TOOL: DynamiteWeapon, 
   FLAREBLOCK_TOOL: FlareBlockTool, 
   PREFAB_TOOL: PrefabTool, 
   PICKAXE_TOOL: PickAxeTool, 
   UGC_PICKAXE_TOOL: UGCPickAxeTool, 
   KNIFE_TOOL: KnifeTool, 
   SPADE_TOOL: SpadeTool, 
   SUPERSPADE_TOOL: SuperSpadeTool, 
   UGC_SUPERSPADE_TOOL: UGCSuperSpadeTool, 
   CLASSIC_SPADE_TOOL: ClassicSpadeTool, 
   BLOCK_TOOL: BlockTool, 
   ZOMBIEHAND_TOOL: ZombieHandTool, 
   BOMB_TOOL: BombTool, 
   DIAMOND_TOOL: DiamondTool, 
   SHRAPNEL_TOOL: BlockTool, 
   ZOMBIE_PREFAB_TOOL: ZombiePrefabTool, 
   INTEL_TOOL: IntelTool, 
   MOLOTOV_TOOL: MolotovWeapon, 
   CROWBAR_TOOL: CrowbarTool, 
   TOMMYGUN_TOOL: TommyGunWeapon, 
   SNUB_PISTOL_TOOL: SnubPistolWeapon, 
   CLASSIC_SHOTGUN_TOOL: ClassicShotgunWeapon, 
   CLASSIC_SMG_TOOL: ClassicSmgWeapon, 
   NULL_TOOL: NullTool, 
   UGC_TOOL: UGCTool, 
   FAKE_PISTOL_TOOL: FakePistolTool, 
   UGC_PREFAB_TOOL: UGCPrefabTool, 
   PAINTBRUSH_TOOL: PaintbrushTool, 
   RIOTSTICK_TOOL: RiotStickTool, 
   MACHETE_TOOL: MacheteTool, 
   MEDPACK_TOOL: MedPackWeapon, 
   RIOTSHIELD_TOOL: RiotShieldTool, 
   CHEMICALBOMB_TOOL: ChemicalBombWeapon, 
   AUTOMATIC_PISTOL_TOOL: AutoPistolWeapon, 
   GRENADE_LAUNCHER_WEAPON_TOOL: GrenadeLauncherWeapon, 
   STICKY_GRENADE_TOOL: StickyGrenadeWeapon, 
   RADAR_STATION_TOOL: RadarStationWeapon, 
   MINE_LAUNCHER_TOOL: MineLauncherWeapon, 
   C4_TOOL: C4Weapon, 
   ASSAULT_RIFLE_TOOL: AssaultRifleWeapon, 
   LIGHT_MACHINE_GUN_TOOL: LightMachineGunWeapon, 
   AUTO_SHOTGUN_TOOL: AutoShotgunWeapon, 
   BLOCK_SUCKER_TOOL: BlockSuckerWeapon, 
   DISGUISE_TOOL: DisguiseTool}
for id, weapon in WEAPONS.iteritems():
    if len(weapon.model) != len(weapon.view_model):
        if id != ZOMBIE_PREFAB_TOOL:
            raise Exception('Weapon/Tools - model list for ', weapon.name, 'should have same length as view_model list.')

PICKUPS = {BOMB_PICKUP: BOMB_TOOL, DIAMOND_PICKUP: DIAMOND_TOOL, 
   INTEL_PICKUP: INTEL_TOOL}

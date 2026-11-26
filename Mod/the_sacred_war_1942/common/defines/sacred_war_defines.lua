NDefines.NCountry.ARMY_IMPORTANCE_FACTOR = 10.0
NDefines.NMilitary.RECON_SKILL_IMPACT = 10
NDefines.NMilitary.COMBAT_MINIMUM_TIME = 2
NDefines.NMilitary.LAND_COMBAT_STR_ARMOR_DEFLECTION_FACTOR = 0.6
NDefines.NMilitary.LAND_COMBAT_ORG_ARMOR_DEFLECTION_FACTOR = 0.6
NDefines.NMilitary.BASE_CAPTURE_EQUIPMENT_RATIO = 0.03
NDefines.NMilitary.ENEMY_AIR_SUPERIORITY_SPEED_IMPACT = -0.1
NDefines.NMilitary.INITIATIVE_PICK_COUNTER_ADVANTAGE_FACTOR  = 0.40
NDefines.NMilitary.WAR_SCORE_AIR_IC_LOSS_FACTOR = 0.008						-- war score gained for every IC of damage done to an enemy's air mission
NDefines.NMilitary.WAR_SCORE_LAND_DAMAGE_FACTOR = 0.01          				-- war score gained for every strengh damage done to an enemy's army
NDefines.NMilitary.WAR_SCORE_LAND_IC_LOSS_FACTOR = 0.008         				-- war score gained for every IC damage done to an enemy's army
NDefines.NAir.AIR_WING_FLIGHT_SPEED_MULT = 0.04
NDefines.NAir.AIR_WING_MAX_STATS_BOMBING = 200
NDefines.NAir.AIR_DEPLOYMENT_DAYS = 1	-- #MOD-- was 2,				-- Days to deploy one air wing
NDefines.NNavy.AGGRESSION_SETTINGS_VALUES = { -- ships will use this values while deciding to attack enemies
		0,		-- do not engage
		1.0,	-- low
		1.5,	-- medium
		2.5,	-- high
		10000,	-- I am death incarnate!
	}
NDefines.NNavy.WAR_SCORE_GAIN_FOR_SUNK_SHIP_MANPOWER_FACTOR = 0.002			-- war score gained for every manpower killed when sinking a ship
NDefines.NNavy.WAR_SCORE_GAIN_FOR_SUNK_SHIP_PRODUCTION_COST_FACTOR = 0.01		-- war score gained for every IC of the sunk ship
NDefines.NAir.AIR_WING_BOMB_DAMAGE_FACTOR = 5					-- Used to balance the damage done while bombing.
NDefines.NSupply.AVAILABLE_MANPOWER_STATE_SUPPLY = 0.5
NDefines.NMilitary.LAND_COMBAT_COLLATERAL_INFRA_FACTOR = 0.007
NDefines.NAI.ENTRENCHMENT_WEIGHT = 2.5
NDefines.NAI.MAX_MICRO_ATTACKS_PER_ORDER = 5
NDefines.NAI.ATTACK_HEAVILY_DEFENDED_LIMIT = 0.42
-- EXPERT AI
NDefines.NAI.RESEARCH_DAYS_BETWEEN_WEIGHT_UPDATE = 1

NDefines.NAI.RESEARCH_LAND_DOCTRINE_NEED_GAIN_FACTOR = 0                      	-- Multiplies value based on relative military industry size / country size.
NDefines.NAI.RESEARCH_NAVAL_DOCTRINE_NEED_GAIN_FACTOR = 0                       -- Multiplies value based on relative naval industry size / country size.
NDefines.NAI.RESEARCH_AIR_DOCTRINE_NEED_GAIN_FACTOR = 0                         -- Multiplies value based on relative number of air base / country size.
NDefines.NAI.RESEARCH_NEW_DOCTRINE_RANDOM_FACTOR = 0

NDefines.NAI.MAX_AHEAD_RESEARCH_PENALTY = 10
NDefines.NAI.RESEARCH_NEW_WEIGHT_FACTOR = 0			                            -- Impact of previously unexplored tech weights. Higher means more random exploration.
NDefines.NAI.RESEARCH_BONUS_FACTOR = 3 				                       		-- To which extent AI should care about bonuses to research
NDefines.NAI.RESEARCH_AHEAD_OF_TIME_FACTOR = 0		                            -- To which extent AI should care about ahead of time penalties to research
NDefines.NAI.RESEARCH_BASE_DAYS = 0					                            -- AI adds a base number of days when weighting completion time for techs to ensure it doesn't only research quick techs
NDefines.NAI.RESEARCH_MULTI_DOCTRINE_SCORE = 0
NDefines.NAI.XP_RATIO_REQUIRED_TO_RESEARCH_WITH_XP = 3.0		-- AI will at least need this amount of xp compared to cost of a tech to reserch it with XP			
NDefines.NAI.RESEARCH_WITH_XP_AI_WEIGHT_MULT = 1.8			-- AI will bump score of a research with this mult if it can use XP
NDefines.NAI.LAND_DESIGN_DEMAND_FIELD_DIVISION = 50
NDefines.NAI.LAND_DESIGN_DEMAND_TRAINING_DIVISION = 50
NDefines.NAI.LAND_DESIGN_DEMAND_GARRISON_DIVISION = 10
NDefines.NAI.LAND_DESIGN_DEMAND_UNUSED_TEMPLATE = 10 --1
NDefines.NAI.LAND_DESIGN_DEMAND_ABSENT = 10 --0
NDefines.NAI.DESIRE_USE_XP_TO_UNLOCK_ARMY_SPIRIT = 0.4
NDefines.NAI.UPGRADE_DIVISION_RELUCTANCE = 1 
NDefines.NAI.UPGRADE_PERCENTAGE_OF_FORCES = 0.01
NDefines.NAI.DEPLOY_MIN_TRAINING_SURRENDER_FACTOR = 0.5		-- Required percentage of training (1.0 = 100%) for AI to deploy unit in wartime while surrender progress is higher than 0 
NDefines.NAI.DEPLOY_MIN_EQUIPMENT_SURRENDER_FACTOR = 0.8	-- Required percentage of equipment (1.0 = 100%) for AI to deploy unit in wartime while surrender progress is higher than 0 
NDefines.NAI.DEPLOY_MIN_TRAINING_PEACE_FACTOR = 0.4		-- Required percentage of training (1.0 = 100%) for AI to deploy unit in peacetime
NDefines.NAI.DEPLOY_MIN_EQUIPMENT_PEACE_FACTOR = 0.9	-- Required percentage of equipment (1.0 = 100%) for AI to deploy unit in peacetime
NDefines.NAI.DEPLOY_MIN_TRAINING_WAR_FACTOR = 0.9		-- Required percentage of training (1.0 = 100%) for AI to deploy unit in wartime
NDefines.NAI.DEPLOY_MIN_EQUIPMENT_WAR_FACTOR = 0.9		-- Required percentage of equipment (1.0 = 100%) for AI to deploy unit in wartime
NDefines.NAI.DEPLOY_MIN_EQUIPMENT_CAP_DEPLOY_FACTOR = 0.85 -- If training is capped by equipment deficit and we have reached that cap, deploy unit anyway if percentage is above this (reinforce in field instead).
NDefines.NAI.PRODUCTION_EQUIPMENT_SURPLUS_FACTOR = 1
NDefines.NAI.NEW_LEADER_EXTRA_PP_FACTOR = 1 --2.0	
NDefines.NAI.MIN_AI_UNITS_PER_TILE_FOR_STANDARD_COHESION = 2.0	-- How many units should we have for each tile along a front in order to switch to standard cohesion (less moving around)
NDefines.NAI.MIN_FRONT_SIZE_TO_CONSIDER_STANDARD_COHESION = 2000
NDefines.NAI.ASSIGN_TANKS_TO_WAR_FRONT = 8.0 --4.0
NDefines.NAI.ASSIGN_TANKS_TO_NON_WAR_FRONT = 0.2 --0.4
NDefines.NAI.FALLBACK_LOSING_FACTOR = 0.0 	
NDefines.NAI.HOUR_BAD_COMBAT_REEVALUATE = 24
NDefines.NAI.PLAN_ATTACK_MIN_ORG_FACTOR_LOW = 0.85							-- Minimum org % for a unit to actively attack an enemy unit when executing a plan
NDefines.NAI.PLAN_ATTACK_MIN_STRENGTH_FACTOR_LOW = 0.85						-- Minimum strength for a unit to actively attack an enemy unit when executing a plan

NDefines.NAI.PLAN_ATTACK_MIN_ORG_FACTOR_MED = 0.65							-- (LOW,MED,HIGH) corresponds to the plan execution agressiveness level.
NDefines.NAI.PLAN_ATTACK_MIN_STRENGTH_FACTOR_MED = 0.65	

NDefines.NAI.PLAN_ATTACK_MIN_ORG_FACTOR_HIGH = 0.5		
NDefines.NAI.PLAN_ATTACK_MIN_STRENGTH_FACTOR_HIGH = 0.5	
NDefines.NAI.PLAN_FACTION_STRONG_TO_EXECUTE = 0.65
NDefines.NAI.ORG_UNIT_STRONG = 0.75												-- Organization % for unit to be considered strong
NDefines.NAI.STR_UNIT_STRONG = 0.75		
NDefines.NAI.PLAN_FACTION_NORMAL_TO_EXECUTE = 0.65
NDefines.NAI.ORG_UNIT_NORMAL = 0.6 --6												-- Organization % for unit to be considered normal
NDefines.NAI.STR_UNIT_NORMAL = 0.6 --6												-- Strength (equipment) % for unit to be considered normal

NDefines.NAI.PLAN_FACTION_WEAK_TO_ABORT = 0.5 --0.50		0.65		        -- % or more of units in an order to consider ececuting the plan
NDefines.NAI.ORG_UNIT_WEAK = 0.45 --0.45												-- Organization % for unit to be considered weak
NDefines.NAI.STR_UNIT_WEAK = 0.4 --0.45		
NDefines.NAI.AI_FRONT_MOVEMENT_FACTOR_FOR_READY = 0.5
NDefines.NAI.MAX_INVASION_SIZE = 18
NDefines.NAI.LAND_DEFENSE_FIGHERS_PER_PLANE = 1				-- Amount of air superiority planes requested per enemy plane
NDefines.NAI.LAND_DEFENSE_INTERSEPTORS_PER_BOMBERS = 1		-- Amount of air interceptor planes requested per enemy bomber
NDefines.NAI.UNIT_ASSIGNMENT_TERRAIN_IMPORTANCE = 150.0
NDefines.NMilitary.FRONTLINE_EXPANSION_FACTOR = 0.0
NDefines.NProduction.BASE_FACTORY_SPEED_MIL = 5.5
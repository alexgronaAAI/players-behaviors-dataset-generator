# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import random
from datetime import timedelta
import numpy as np
from pbdg.common import *

def random_gauss_clamp(mu, sigma, factor=3):
    return min(mu+factor*sigma, max(mu-factor*sigma, random.gauss(mu, sigma)))

def random_time(mu, sigma):
    return timedelta(seconds=random.gauss(mu.total_seconds(), sigma.total_seconds()))

def random_duration_clamp(mu, sigma, factor=2):
    return timedelta(seconds=random_gauss_clamp(mu.total_seconds(), sigma.total_seconds(), factor))

class LinearInterpolator:
    '''A class to interpolate a number from a list of numbers.
       
       Example:
       linterp = LinearInterpolator({
         1: 10,
         6: 20,
         10: 100
       })
       value = wdict[0] # value == 10
       value = wdict[1] # value == 10
       value = wdict[3] # value == 15
       value = wdict[40] # value == 100
    '''

    def __init__(self, dictionary, mod = False):
        self.keys = []
        self.values = []
        self.mod = mod

        for key in dictionary:
            self.keys.append(float(key))
            self.values.append(float(dictionary[key]))

    def __getitem__(self, key):
        mod_key = key
        if mod_key > self.keys[-1] and self.mod:
            mod_key = key % self.keys[-1]
        return np.interp(key, self.keys, self.values)

    def __mul__(self, value):
        return LinearInterpolator(dict(zip(self.keys, (v * value for v in self.values))))

    __rmul__ = __mul__

class WeightedDictionary:
    '''A class to select one the value of a dictionay using the keys as the probability interval for each value.
       
       Example:
       wdict = WeightedDictionary({
         0.10: value1,
         0.45: value2,
         1.00: value3
       })
       value = wdict[0.05] # value == value1
       value = wdict[0.3] # value == value2
       value = wdict[0.5] # value == value3
    '''

    def __init__(self, dictionary):
        self.dictionary = {k: v for k, v in sorted(dictionary.items(), key=lambda item: item[1])}

    def __getitem__(self, p):
        for key, value in self.dictionary.items():
            if p < value:
                return key
            else:
                last_key = key
        return last_key

class PurchaseOptions:
    """A purchase options class."""
    def __init__(self, amount_per_spend=0, amount_per_spend_sigma=0,
                 spend_time_per_session=0, spend_time_per_session_sigma=0, spend_per_visit_ratio=0):
        self.amount_per_spend = amount_per_spend
        self.amount_per_spend_sigma = amount_per_spend_sigma
        self.spend_time_per_session = spend_time_per_session
        self.spend_time_per_session_sigma = spend_time_per_session_sigma
        self.spend_per_visit_ratio = spend_per_visit_ratio

    def amount(self):
        return int(max(0, random.gauss(self.amount_per_spend, self.amount_per_spend_sigma)))

    def spend_count(self):
        return int(max(0, random.gauss(self.spend_time_per_session, self.spend_time_per_session_sigma)))

    def must_spend(self):
        return random.random() < self.spend_per_visit_ratio

class StageOptions:
    """A stage options class."""
    def __init__(self, duration_mu, duration_sigma, duration_ratio,
                        score_mu, score_sigma):
        self.duration_mu = duration_mu
        self.duration_sigma = duration_sigma
        self.duration_ratio = duration_ratio
        self.score_mu = score_mu
        self.score_sigma = score_sigma

    def duration(self, factor=2):
        return random_duration_clamp(self.duration_mu, self.duration_sigma, factor)

    def interval_duration(self, factor=2):
        return self.duration_ratio * random_duration_clamp(self.duration_mu, self.duration_sigma, factor)

    def score(self):
        return int(max(0, random.gauss(self.score_mu, self.score_sigma)))
            
class SessionOptions:
    """A session options class."""
    def __init__(self, time_mu, time_sigma, 
                 duration_mu, duration_sigma):
        self.time_mu = time_mu
        self.time_sigma = time_sigma
        self.duration_mu = duration_mu
        self.duration_sigma = duration_sigma

    def time(self):
        return random_time(self.time_mu, self.time_sigma)
    
    def duration(self, factor=3):
        return random_duration_clamp(self.duration_mu, self.duration_sigma, factor)

class PlayerOptions:
    """A player options class."""   
    def __init__(self, player_type, 
                        sessions_options,
                        purchase_options,
                        stages_options,
                        lifetime):
        self.player_type = player_type
        self.sessions_options = sessions_options
        self.purchase_options = purchase_options
        self.stages_options = stages_options
        self.lifetime = lifetime

class GameRules:

    def __init__(self, correlations):
        self.correlations = correlations

class GameOptions:
    """A game options class."""
    def __init__(self, players_options, players_acquisition, simulation_days):
        self.players_options = players_options
        self.players_acquisition = players_acquisition
        self.simulation_days = simulation_days

def default_game_options(players, days, players_options_days, players_acquisition_days, players_options_presets, players_acquisition_presets):

    # sessions options
    morning_session_options = SessionOptions(
        timedelta(hours=7), # session time mean
        timedelta(minutes=30), # session time standard deviation
        timedelta(minutes=30), # session duration mean
        timedelta(minutes=10) # session duration standard deviation
    )

    noon_session_options = SessionOptions(
        timedelta(hours=12), # session time mean
        timedelta(hours=30), # session time standard deviation
        timedelta(minutes=45), # session duration mean
        timedelta(minutes=15) # session duration standard deviation
    )

    afternoon_session_options = SessionOptions(
        timedelta(hours=17), # session time mean
        timedelta(hours=1), # session time standard deviation
        timedelta(minutes=30), # session duration mean
        timedelta(minutes=20) # session duration standard deviation
    )

    night_session_options = SessionOptions(
        timedelta(hours=20), # session time mean
        timedelta(hours=3), # session time standard deviation
        timedelta(hours=2), # session duration mean
        timedelta(minutes=1) # session duration standard deviation
    )

    # purchase options
    hardcore_buyer_options = PurchaseOptions(
        amount_per_spend=8,
        amount_per_spend_sigma=3,
        spend_time_per_session=3,
        spend_time_per_session_sigma=1,
        spend_per_visit_ratio=0.8
    )
    casual_buyer_options = PurchaseOptions(
        amount_per_spend=2,
        amount_per_spend_sigma=1,
        spend_time_per_session=1,
        spend_time_per_session_sigma=1,
        spend_per_visit_ratio=0.2
    )
    no_buyer_options = PurchaseOptions()

    # stages options
    strong_stage_options = StageOptions(
        timedelta(minutes=1), # stage duration mean
        timedelta(seconds=10), # stage duration standard deviation
        2.0, # stage duration ratio
        1000, # stage score mean
        100 # stage score standard deviation
    )

    medimum_stage_options = StageOptions(
        timedelta(minutes=1), # stage duration mean
        timedelta(seconds=10), # stage duration standard deviation
        4.0, # stage duration ratio
        700, # stage score mean
        300 # stage score standard deviation
    )

    weak_stage_options = StageOptions(
        timedelta(minutes=1), # stage duration mean
        timedelta(seconds=10), # stage duration standard deviation
        5.0, # stage duration ratio
        500, # stage score mean
        500 # stage score standard deviation
    )

    # players options
    bot_player = PlayerOptions(
        'bot',
        {
            WeekDay.MONDAY: {
                night_session_options: 1.0,
                noon_session_options: 1.0,
                afternoon_session_options: 1.0,
                night_session_options: 1.0
            },
            WeekDay.TUESDAY: {
                morning_session_options: 1.0,
                noon_session_options: 1.0,
                afternoon_session_options: 1.0,
                night_session_options: 1.0
            },
            WeekDay.WEDNESDAY:  {
                night_session_options: 1.0,
                noon_session_options: 1.0,
                afternoon_session_options: 1.0,
                night_session_options: 1.0
            },
            WeekDay.THURSDAY:  {
                night_session_options: 1.0,
                noon_session_options: 1.0,
                afternoon_session_options: 1.0,
                night_session_options: 1.0
            },
            WeekDay.FRIDAY:  {
                night_session_options: 1.0,
                noon_session_options: 1.0,
                afternoon_session_options: 1.0,
                night_session_options: 1.0
            },
            WeekDay.SATURDAY:  {
                night_session_options: 1.0,
                noon_session_options: 1.0,
                afternoon_session_options: 1.0,
                night_session_options: 1.0
            },
            WeekDay.SATURDAY: {
                night_session_options: 1.0,
                noon_session_options: 1.0,
                afternoon_session_options: 1.0,
                night_session_options: 1.0
            },
            WeekDay.SUNDAY: {
                night_session_options: 1.0,
                noon_session_options: 1.0,
                afternoon_session_options: 1.0,
                night_session_options: 1.0
            }
        },
        WeightedDictionary({
            no_buyer_options: 1
        }),
        WeightedDictionary({
            strong_stage_options: 1.0
        }),
        LinearInterpolator({
            0: 1.0
        })
    )

    hardcore_player_options = PlayerOptions(
        'hardcore',
        {
            WeekDay.MONDAY: {
                night_session_options: 0.5  # 50% chance to play a night session on monday
            },
            WeekDay.TUESDAY: {
                morning_session_options: 0.3,
                noon_session_options: 0.5,
                night_session_options: 1.0
            },
            WeekDay.WEDNESDAY:  {
                morning_session_options: 0.3,
                noon_session_options: 0.5,
                night_session_options: 1.0
            },
            WeekDay.THURSDAY:  {
                morning_session_options: 0.3,
                noon_session_options: 0.5,
                night_session_options: 1.0
            },
            WeekDay.FRIDAY:  {
                morning_session_options: 0.3,
                noon_session_options: 0.5,
                night_session_options: 1.0
            },
            WeekDay.SATURDAY:  {
                morning_session_options: 0.3,
                noon_session_options: 0.5,
                night_session_options: 1.0
            },
            WeekDay.SATURDAY: {
                morning_session_options: 0.5
            },
            WeekDay.SUNDAY: {
                afternoon_session_options: 0.8
            }
        },
        WeightedDictionary({
            no_buyer_options: 0.1,
            casual_buyer_options: 0.6,
            hardcore_buyer_options: 1.0
        }),
        WeightedDictionary({
            strong_stage_options: 0.3,
            medimum_stage_options: 0.8,
            weak_stage_options: 1.0
        }),
        LinearInterpolator({
            0: 0.7, # day 1 modifier for session probability
            6: 1.0,
            days * 0.1 : 0.7,
            days * 0.3: 0.5,
            days * 0.6: 0.2,
            days * 0.8: 0.1
        })
    )

    casual_player_options = PlayerOptions(
        'casual',
        {
            WeekDay.TUESDAY: {
                noon_session_options: 0.5,
                night_session_options: 0.5
            },
            WeekDay.WEDNESDAY:  {
                noon_session_options: 0.5,
                night_session_options: 0.5
            },
            WeekDay.THURSDAY:  {
                noon_session_options: 0.5,
                night_session_options: 0.5
            },
            WeekDay.FRIDAY:  {
                noon_session_options: 0.5,
                night_session_options: 0.5
            }
        },
        WeightedDictionary({
            hardcore_buyer_options: 0.2,
            casual_buyer_options: 0.7,
            no_buyer_options: 1
        }),
        WeightedDictionary({
            strong_stage_options: 0.1,
            medimum_stage_options: 0.5,
            weak_stage_options: 1.0
        }),
        LinearInterpolator({
            0: 0.7, # day 1 modifier for session probability
            days * 0.01: 1.0,
            days * 0.1 : 0.5,
            days * 0.3: 0.2,
            days * 0.6: 0.1
        })
    )    

    churner_player_options = PlayerOptions(
        'churner',
        {
            WeekDay.TUESDAY: {
                night_session_options: 1.0
            },
            WeekDay.WEDNESDAY:  {
                night_session_options: 1.0
            },
            WeekDay.THURSDAY:  {
                night_session_options: 1.0
            },
            WeekDay.FRIDAY:  {
                night_session_options: 1.0
            },
            WeekDay.SUNDAY:  {
                night_session_options: 1.0
            }
        },
        WeightedDictionary({
            hardcore_buyer_options: 0.1,
            casual_buyer_options: 0.5,
            no_buyer_options: 0.6
        }),
        WeightedDictionary({
            strong_stage_options: 0.05,
            medimum_stage_options: 0.3,
            weak_stage_options: 1.0
        }),
        LinearInterpolator({
            0: 1.0, # day 1 modifier for session probability
            1: 1.0,
            2: 0.5,
            max(6, days * 0.1): 0.3,
            max(6, days * 0.2): 0.1,
            max(6, days * 0.3): 0.0,
        })
    )

    # Generate player acquisition with exponential decay and exponentially decreasing noise
    def player_acquisition_with_noise(players, days, decay_rate=0.3, noise_scale=0.1, noise_decay_rate=0.3):
        return [
            max(0, int(
                players * np.exp(-decay_rate * day) +
                random.gauss(0, players * noise_scale * np.exp(-noise_decay_rate * day))
            ))
            for day in range(days)
        ]
    
    players_options_sets = []

    for players_options_preset in players_options_presets:
        players_options_sets.append(WeightedDictionary({
            #bot_player: 1.0,
            hardcore_player_options: players_options_preset[0],
            casual_player_options: players_options_preset[1],
            churner_player_options: players_options_preset[2],
        }))

    players_acquisition_sets = []

    for players_acquisition_preset in players_acquisition_presets:
        players_acquisition_sets.append(player_acquisition_with_noise(players, days, players_acquisition_preset[0], players_acquisition_preset[1], players_acquisition_preset[2]))

    players_options = []
    players_acquisition = []
    for i in range(days):
        players_options.append(players_options_sets[players_options_days[i]])
        players_acquisition.append(players_acquisition_sets[players_acquisition_days[i]])

    game_options = GameOptions(
        players_options, 
        # players_acquisition = players * LinearInterpolator({
        #         0: 1, # one player acquired day one
        #         6: 2,
        #         7: 0,
    
        #         13: 0,
        #         14: 2,
        #         20: 5,
        #         21: 0,
    
        #         27: 0,
        #         28: 1,
        #         34: 3,
        #         35: 0
        #     }, 
        #     mod=True
        # ),
        players_acquisition,
        simulation_days = days # simulation days
    )

    return game_options
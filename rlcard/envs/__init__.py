''' Register new environments
'''
from rlcard.envs.env import Env
from rlcard.envs.registration import register, make

register(
    env_id='spades',
    entry_point='rlcard.envs.spades:SpadesEnv'
)
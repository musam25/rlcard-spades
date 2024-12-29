import os
import argparse

import rlcard
from rlcard.agents import (
    DQNAgent,
    RandomAgent,
)
from rlcard.utils import (
    get_device,
    set_seed,
    tournament,
)
import torch
import modal
image = modal.Image.debian_slim().pip_install(
    "torch",
    "rlcard",
    "tqdm",
     'matplotlib',
     'numpy'
)
vol = modal.Volume.from_name("bin_reward")

app = modal.App(name="dqn_model_eval")

@app.function(gpu='T4', timeout = 3600, image=image, volumes={"/data": vol})
def load_model(model_path, env=None, position=None, device=None):
    print(model_path)
    if os.path.isfile(model_path):  # Torch model
        agent = torch.load(model_path, map_location=device)
        agent.set_device(device)
    elif os.path.isdir(model_path):  # CFR model
        from rlcard.agents import CFRAgent
        agent = CFRAgent(env, model_path)
        agent.load()
    elif model_path == 'random':  # Random model
        agent = RandomAgent(num_actions=env.num_actions)
    else:  # A model in the model zoo
        from rlcard import models
        agent = models.load(model_path).agents[position]
    
    return agent

@app.function(gpu='A100', timeout = 3600, image=image, volumes={"/data": vol})
def evaluate(env: str='spades', models:str="model_spades_dqn_5ep.pth", device:str='0', seed:int=42, games:int=10 ):

    # Check whether gpu is available
    device = get_device()
        
    # Seed numpy, torch, random
    set_seed(seed)

    # Make the environment with seed
    env = rlcard.make(env, config={'seed':seed})

    # Load models
    agents = []
    agents.append(load_model.remote(f'/data/{models}/model_spades_a100_dqn_4000ep.pt', env, "AI Model", device))
    agents.append(RandomAgent(num_actions=env.num_actions))
    agents.append(load_model.remote(f'/data/{models}/model_spades_a100_dqn_4000ep.pt', env, "AI Model", device))
    agents.append(RandomAgent(num_actions=env.num_actions))
    env.set_agents(agents)

    # Evaluate
    rewards = tournament(env, games)
    for position, reward in enumerate(rewards):
        print(position, models[position], reward)

@app.local_entrypoint()
def main(env: str='spades', models:str="models", device:str='0', seed:int=42, games:int=1000 ):
    evaluate.remote(
        env = env, 
        models = models, 
        device = device, 
        seed = seed, 
        games = games
    )
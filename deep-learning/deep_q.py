import os
import torch
from tqdm import tqdm
import rlcard
from rlcard.agents import RandomAgent
from rlcard.utils import (
    get_device,
    set_seed,
    tournament,
    reorganize,
    Logger,
    spades_reorganize,
)
import modal
import csv
import matplotlib.pyplot as plt
app = modal.App(name="rl-training-large")
vol = modal.Volume.from_name("bin_reward", create_if_missing=True)
# Define image with dependencies
image = modal.Image.debian_slim().pip_install(
    "torch",
    "rlcard",
    "tqdm",
     'matplotlib'
)


@app.function(gpu="H100", image=image, timeout=72000, volumes={"/data": vol})
def train_rl(env_name: str = "spades", algorithm: str = "dqn", num_episodes: int = 5000, seed: int = 42,num_eval_games: int = 2000, evaluate_every:int=100, log_directory:str = "experiments/testing-a100/" ):
    # Initialize environment and agents
    env = rlcard.make(env_name, config={'seed': seed})
    device = get_device()
    set_seed(seed)
    
    # Create agent based on algorithm choice
    if algorithm == 'dqn':
        from rlcard.agents import DQNAgent
        agent = DQNAgent(
            num_actions=env.num_actions,
            state_shape=env.state_shape[0],
            mlp_layers=[64,64],
            device=device,
        )
    else:  # nfsp
        from rlcard.agents import NFSPAgent
        agent = NFSPAgent(
            num_actions=env.num_actions,
            state_shape=env.state_shape[0],
            hidden_layers_sizes=[64,64],
            q_mlp_layers=[64,64],
            device=device,
        )
    
    # Set up environment with our agent and random opponents
    agents = [agent] + [RandomAgent(num_actions=env.num_actions) 
                       for _ in range(env.num_players - 1)]
    env.set_agents(agents)
    
    with Logger('/data/'+log_directory) as logger:
        # Training loop
        for episode in tqdm(range(num_episodes)):
            if algorithm == 'nfsp':
                agents[0].sample_episode_policy()
                
            trajectories, payoffs = env.run(is_training=True)
            trajectories = reorganize(trajectories, payoffs)
            
            if env_name == 'spades':
                trajectories = spades_reorganize(trajectories, payoffs)
            
            # Train agent on trajectories
            for transition in trajectories[0]:
                agent.feed(transition)
            if episode % evaluate_every == 0:
                logger.log_performance(
                    episode,
                    tournament(env, num_eval_games)[0]
                )
                csv_path, fig_path = logger.csv_path, logger.fig_path
                def plot_curve(csv_path, save_path, algorithm):
                    ''' Read data from csv file and plot the results
                    '''
                    with open(csv_path) as csvfile:
                        reader = csv.DictReader(csvfile)
                        xs = []
                        ys = []
                        for row in reader:
                            print(row)
                            xs.append(int(row['episode']))
                            ys.append(float(row['reward']))
                        print(xs)
                        fig, ax = plt.subplots()
                        ax.plot(xs, ys, label=algorithm)
                        ax.set(xlabel='episode', ylabel='reward')
                        ax.legend()
                        ax.grid()
                        fig.savefig("/data/fig.png")
                        vol.commit()
                # Plot the learning curve
                #vol.commit()
        model_filename = f"/data/models/model_{env_name}_a100_{algorithm}_{num_episodes}ep.pt"
        os.makedirs('/data/models/',exist_ok=True)
        save_path = os.path.join(model_filename)
        print(f"Saving model to {save_path}")
        torch.save(agent, save_path)
        vol.commit()
    return model_filename

@app.local_entrypoint()
def main(env_name: str = "spades", algorithm: str = "dqn", episodes: int = 1000000, seed: int = 42, evals: int = 500, evaluate:int=100, log:str = "experiments/testing-a100/" ):
    model_path = train_rl.remote(
        env_name=env_name, 
        algorithm=algorithm,
        num_episodes=episodes, 
        seed = seed, 
        num_eval_games = evals,
        evaluate_every = evaluate,
        log_directory = log
    )
    print(f"Training completed! Model saved at: {model_path}")

if __name__ == "__main__":
    modal.runner.main(app)
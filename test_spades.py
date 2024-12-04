import rlcard
from rlcard.agents.random_agent import RandomAgent
import numpy as np
from collections import defaultdict

def validate_spades_game(num_games=10):
    """Run multiple games and validate game mechanics"""
    
    config = {'allow_step_back': True, 'seed': 42}
    env = rlcard.make('spades', config=config)
    
    # Statistics tracking
    stats = {
        'bids': [],               # Track all bids
        'tricks_per_round': [],   # Should always sum to 13
        'round_lengths': [],      # Should be 13 tricks per round
        'spades_breaking': [],    # When spades first played in each round
        'scores': [],             # Final scores
        'game_lengths': [],       # Number of rounds per game
        'team1_wins': 0,          # Team 1 wins (500 points)
        'team2_wins': 0,          # Team 2 wins (500 points)
        'team1_losses': 0,        # Team 1 losses (-200 points)
        'team2_losses': 0,        # Team 2 losses (-200 points)
        'normal_endings': 0       # Games ended normally
    }
    
    for game in range(num_games):
        print(f"\nStarting Game {game + 1}")
        
        # Create new random agents for each game
        agents = [RandomAgent(env.num_actions) for _ in range(env.num_players)]
        env.set_agents(agents)
        
        round_count = 0
        round_tricks = defaultdict(int)
        spades_broken = False
        
        trajectories, payoffs = env.run(is_training=False)
        
        # Analyze game results
        for trajectory in trajectories:
            for step in trajectory:
                state = step['state']['raw_obs']
                
                if state['stage'] == 'bidding':
                    stats['bids'].extend([b for b in state['bids'] if b != -1])
                
                if 'tricks_won' in state:
                    round_tricks[round_count] = sum(state['tricks_won'])
                
                if state.get('spades_broken', False) and not spades_broken:
                    stats['spades_breaking'].append(round_tricks[round_count])
                    spades_broken = True
            
            if round_tricks[round_count] == 13:
                round_count += 1
                spades_broken = False
        
        stats['round_lengths'].append(list(round_tricks.values()))
        stats['game_lengths'].append(round_count)
        stats['scores'].append(payoffs)
        
        # Track game ending conditions
        final_scores = env.game.team_scores
        if final_scores[0] >= 500:
            stats['team1_wins'] += 1
        elif final_scores[1] >= 500:
            stats['team2_wins'] += 1
        elif final_scores[0] <= -200:
            stats['team1_losses'] += 1
        elif final_scores[1] <= -200:
            stats['team2_losses'] += 1
        else:
            stats['normal_endings'] += 1
    
    # Print validation results
    print("\nGame Mechanics Validation:")
    print("-" * 50)
    
    print("\nBidding Analysis:")
    print(f"Average bid: {np.mean(stats['bids']):.2f}")
    print(f"Bid range: {min(stats['bids'])} to {max(stats['bids'])}")
    print(f"Bid distribution: {np.bincount(stats['bids'])}")
    
    print("\nTricks Analysis:")
    for game_idx, rounds in enumerate(stats['round_lengths']):
        for round_idx, tricks in enumerate(rounds):
            if tricks != 13:
                print(f"WARNING: Game {game_idx}, Round {round_idx} had {tricks} tricks (should be 13)")
    
    print("\nSpades Breaking Analysis:")
    if stats['spades_breaking']:
        print(f"Average trick when spades first broken: {np.mean(stats['spades_breaking']):.2f}")
    
    print("\nScoring Analysis:")
    print(f"Average game length: {np.mean(stats['game_lengths']):.2f} rounds")
    print(f"Team 1 wins: {stats['team1_wins']}")
    print(f"Team 2 wins: {stats['team2_wins']}")
    print(f"Team 1 losses: {stats['team1_losses']}")
    print(f"Team 2 losses: {stats['team2_losses']}")
    print(f"Normal endings: {stats['normal_endings']}")
    
    all_scores = [score for game_scores in stats['scores'] for score in game_scores]
    print(f"Score ranges: {min(all_scores):.1f} to {max(all_scores):.1f}")
    
    # Final verdict
    print("\nValidation Checks:")
    checks = [
        ("All bids valid", all(0 <= bid <= 13 for bid in stats['bids'])),
        ("All rounds have 13 tricks", all(tricks == 13 for rounds in stats['round_lengths'] for tricks in rounds)),
        ("No infinite games", max(stats['game_lengths']) < 50),
        ("Games end at appropriate scores", _validate_game_endings(stats))
    ]
    
    for check_name, passed in checks:
        print(f"{check_name}: {'✓' if passed else '✗'}")
    
    return stats

def _validate_game_endings(stats):
    """Validate that games end appropriately"""
    total_games = (stats['team1_wins'] + stats['team2_wins'] + 
                  stats['team1_losses'] + stats['team2_losses'] + 
                  stats['normal_endings'])
    
    if total_games == 0:
        return False
    
    # Check win/loss distribution
    team1_outcomes = stats['team1_wins'] + stats['team1_losses']
    team2_outcomes = stats['team2_wins'] + stats['team2_losses']
    
    # Validation criteria
    balanced_wins = abs(stats['team1_wins'] - stats['team2_wins']) <= total_games * 0.4
    has_normal_endings = stats['normal_endings'] > 0
    not_all_same_type = (stats['team1_wins'] + stats['team2_wins']) < total_games
    reasonable_distribution = abs(team1_outcomes - team2_outcomes) <= total_games * 0.4
    
    return (
        balanced_wins and
        has_normal_endings and
        not_all_same_type and
        reasonable_distribution
    )

if __name__ == "__main__":
    validation_stats = validate_spades_game(num_games=10)
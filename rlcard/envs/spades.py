import numpy as np
from collections import OrderedDict
from rlcard.envs import Env
from rlcard.games.spades import Game

DEFAULT_GAME_CONFIG = {
    'game_num_players': 4,
    'game_num_decks': 1
}

class SpadesEnv(Env):
    ''' Spades Environment '''

    def __init__(self, config):
        self.name = 'spades'
        self.default_game_config = DEFAULT_GAME_CONFIG
        self.game = Game()
        super().__init__(config)
        
        # State shape: [hand(52), current trick(52), spades broken(1), 
        # bids(4), tricks won(4), scores(2), bags(2), stage(1)]
        self.state_shape = [[118] for _ in range(self.num_players)]
        self.action_shape = [None for _ in range(self.num_players)]

    def _get_legal_actions(self):
        ''' Get all legal actions for current state '''
        legal_actions = OrderedDict()
        raw_legal_actions = self.game.get_legal_actions()
        for i, action in enumerate(raw_legal_actions):
            legal_actions[i] = action
        return legal_actions

    def step(self, action):
        """Execute one step in the environment"""
        try:
            # Get next state from game
            next_state, next_player = self.game.step(action)
            
            # Calculate rewards and check end conditions
            done = False
            reward = 0
            
            # Check if round is over
            all_cards_played = all(len(player.hand) == 0 for player in self.game.players)
            if all_cards_played:
                reward = self._calculate_round_reward()
                
                # Check if game is over
                if self.game.is_over():
                    done = True
                    reward += self._calculate_game_reward()
                else:
                    # Start new round
                    next_state, next_player = self.game.init_game()
            
            extracted_state = self._extract_state(next_state)
            return extracted_state, reward, done, {}
            
        except Exception as e:
            # Handle the case where we need to start a new round
            if str(e) == "Player has no cards in hand":
                if self.game.is_over():
                    state = self.game.get_state(self.game.get_player_id())
                    return self._extract_state(state), self._calculate_game_reward(), True, {}
                    
                # Start new round if game isn't over
                next_state, next_player = self.game.init_game()
                return self._extract_state(next_state), self._calculate_round_reward(), False, {}
                
            raise e

    def reset(self):
        """Reset the environment"""
        state, player_id = self.game.init_game()
        return self._extract_state(state), player_id

    def _calculate_round_reward(self):
        """Calculate reward at end of round"""
        current_player = self.game.round.current_player
        team = current_player % 2
        
        # Calculate if team made their contract
        team_tricks = sum(self.game.round.tricks_won[i] for i in [team, team + 2])
        team_bid = sum(self.game.round.bids[i] for i in [team, team + 2])
        
        if team_tricks >= team_bid:
            return 1.0  # Made contract
        return -1.0  # Missed contract

    def _calculate_game_reward(self):
        """Calculate reward at end of game"""
        current_player = self.game.round.current_player
        team = current_player % 2
        
        if self.game.team_scores[team] > self.game.team_scores[1-team]:
            return 5.0  # Won game
        elif self.game.team_scores[team] < self.game.team_scores[1-team]:
            return -5.0  # Lost game
        return 0.0  # Tie

    def _extract_state(self, state):
        ''' Extract state information for RL agent '''
        obs = np.zeros(118, dtype=int)
        
        # Encode player's hand (52 bits)
        for card in state['hand']:
            card_idx = self._card_to_idx(card)
            obs[card_idx] = 1
        
        # Encode current trick (52 bits)
        if 'current_trick' in state:
            for card in state['current_trick']:
                if card is not None:
                    card_idx = self._card_to_idx(card)
                    obs[52 + card_idx] = 1
        
        # Game state information
        obs[104] = int(state.get('spades_broken', False))
        
        # Encode bids (4 positions)
        bids = state.get('bids', [-1, -1, -1, -1])
        for i, bid in enumerate(bids):
            obs[105 + i] = bid if bid != -1 else 0
            
        # Encode tricks won (4 positions)
        tricks_won = state.get('tricks_won', [0, 0, 0, 0])
        for i, tricks in enumerate(tricks_won):
            obs[109 + i] = tricks
            
        # Encode team scores and bags
        if 'team_scores' in state:
            obs[113:115] = state['team_scores']
        if 'team_bags' in state:
            obs[115:117] = state['team_bags']
            
        # Encode game stage (1 bit)
        obs[117] = 1 if state.get('stage') == 'playing' else 0
        
        legal_actions = self._get_legal_actions()
        
        extracted_state = {
            'obs': obs,
            'legal_actions': legal_actions,
            'raw_obs': state,
            'raw_legal_actions': list(legal_actions.keys())
        }
        return extracted_state

    def get_payoffs(self):
        ''' Get payoffs at the end of the game '''
        if not self.game.is_over():
            return np.array([0.0 for _ in range(self.num_players)])
            
        payoffs = np.zeros(self.num_players)
        scores = self.game.team_scores
        
        # Assign team scores to player payoffs
        for i in range(self.num_players):
            team_idx = i % 2
            payoffs[i] = scores[team_idx]
            
        return payoffs

    def _decode_action(self, action_id):
        ''' Decode action id to an action in the game '''
        legal_actions = self.game.get_legal_actions()
        if action_id < len(legal_actions):
            return legal_actions[action_id]
        return legal_actions[0]  # Default to first legal action if invalid

    def _card_to_idx(self, card):
        ''' Convert card to index for encoding '''
        suit_order = {'S': 0, 'H': 1, 'D': 2, 'C': 3}
        rank_order = {'2': 0, '3': 1, '4': 2, '5': 3, '6': 4, '7': 5, '8': 6,
                     '9': 7, 'T': 8, 'J': 9, 'Q': 10, 'K': 11, 'A': 12}
        
        suit = card.get_suit()
        rank = card.get_rank()
        return suit_order[suit] * 13 + rank_order[rank]

    def get_perfect_information(self):
        ''' Get perfect information of the current state '''
        state = {}
        state['hands'] = [p.hand for p in self.game.players]
        state['current_trick'] = self.game.round.current_trick if self.game.round else []
        state['trick_history'] = self.game.round.trick_history if self.game.round else []
        state['bids'] = self.game.round.bids if self.game.round else [-1, -1, -1, -1]
        state['tricks_won'] = self.game.round.tricks_won if self.game.round else [0, 0, 0, 0]
        state['spades_broken'] = self.game.round.spades_broken if self.game.round else False
        state['team_scores'] = self.game.team_scores
        state['team_bags'] = self.game.team_bags
        state['stage'] = self.game.round.stage if self.game.round else 'bidding'
        state['current_player'] = self.game.round.current_player if self.game.round else 0
        return state
        
    def run(self, is_training=False):
        """Run a complete game"""
        trajectories = [[] for _ in range(self.num_players)]
        state, player_id = self.reset()
        
        done = False
        while not done:
            # Get current player's action
            action = self.agents[player_id].step(state)
            
            # Record state and action
            trajectories[player_id].append({
                'state': state,
                'action': action
            })
            
            # Take step
            try:
                next_state, reward, done, _ = self.step(action)
                state = next_state
                
                if not done:
                    player_id = self.game.get_player_id()
                    
            except Exception as e:
                print(f"Game ended: {str(e)}")
                done = True
                break
        
        # Get final payoffs
        payoffs = self.get_payoffs()
        
        print("\nGame Over!")
        print(f"Final scores: {self.game.team_scores}")
        if max(self.game.team_scores) >= 500:
            winning_team = 0 if self.game.team_scores[0] >= 500 else 1
            print(f"Team {winning_team + 1} won by reaching 500!")
        elif min(self.game.team_scores) <= -200:
            losing_team = 0 if self.game.team_scores[0] <= -200 else 1
            print(f"Team {losing_team + 1} lost by reaching -200!")
        
        return trajectories, payoffs
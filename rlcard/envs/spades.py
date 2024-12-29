import numpy as np
from collections import OrderedDict
from rlcard.envs import Env
from rlcard.games.spades import Game

DEFAULT_GAME_CONFIG = {
    'game_num_players': 4,
    'game_num_decks': 1
}

class SpadesEnv(Env):
    ''' Spades Environment with simplified reward structure focused on winning '''

    def __init__(self, config):
        self.name = 'spades'
        self.default_game_config = DEFAULT_GAME_CONFIG
        self.game = Game()
        super().__init__(config)
        
        # State shape includes:
        # - hand (52 cards)
        # - current trick (52 cards)
        # - game state (14 values: spades_broken, bids[4], tricks[4], scores[2], bags[2], stage)
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
        """Execute one step and return simple rewards based on game outcome"""
        try:
            next_state, next_player = self.game.step(action)
            reward = 0
            done = False
            
            # Check if round is over (all cards played)
            if all(len(player.hand) == 0 for player in self.game.players):
                if self.game.is_over():
                    done = True
                    # Only give reward at game end
                    reward = self._calculate_game_reward()
                else:
                    # Start new round
                    next_state, next_player = self.game.init_game()
            
            extracted_state = self._extract_state(next_state)
            return extracted_state, reward, done, {'player_id': next_player}
            
        except Exception as e:
            if str(e) == "Player has no cards in hand":
                if self.game.is_over():
                    state = self.game.get_state(self.game.get_player_id())
                    return self._extract_state(state), self._calculate_game_reward(), True, {}
                    
                next_state, next_player = self.game.init_game()
                return self._extract_state(next_state), 0, False, {}
                
            raise e

    def reset(self):
        """Reset the environment for a new game"""
        state, player_id = self.game.init_game()
        return self._extract_state(state), player_id

    def _calculate_game_reward(self):
        """Simple binary reward for winning/losing"""
        current_player = self.game.round.current_player
        team = current_player % 2
        
        if self.game.team_scores[team] > self.game.team_scores[1-team]:
            return 1.0  # Won game
        return 0.0  # Lost game

    def _extract_state(self, state):
        ''' Extract and encode state information for the RL agent '''
        obs = np.zeros(118, dtype=int)
        
        # Encode player's hand
        for card in state['hand']:
            card_idx = self._card_to_idx(card)
            obs[card_idx] = 1
        
        # Encode current trick
        if 'current_trick' in state:
            for card in state['current_trick']:
                if card is not None:
                    card_idx = self._card_to_idx(card)
                    obs[52 + card_idx] = 1
        
        # Encode game state information
        obs[104] = int(state.get('spades_broken', False))
        
        # Encode bids
        bids = state.get('bids', [-1, -1, -1, -1])
        for i, bid in enumerate(bids):
            obs[105 + i] = bid if bid != -1 else 0
            
        # Encode tricks won
        tricks_won = state.get('tricks_won', [0, 0, 0, 0])
        for i, tricks in enumerate(tricks_won):
            obs[109 + i] = tricks
            
        # Encode team scores and bags
        if 'team_scores' in state:
            obs[113:115] = state['team_scores']
        if 'team_bags' in state:
            obs[115:117] = state['team_bags']
            
        # Encode game stage (bidding vs playing)
        obs[117] = 1 if state.get('stage') == 'playing' else 0
        
        legal_actions = self._get_legal_actions()
        
        return {
            'obs': obs,
            'legal_actions': legal_actions,
            'raw_obs': state,
            'raw_legal_actions': list(legal_actions.keys())
        }

    def get_payoffs(self):
        ''' Get binary payoffs for all players at game end '''
        if not self.game.is_over():
            return np.array([0.0 for _ in range(self.num_players)])
            
        payoffs = np.zeros(self.num_players)
        scores = self.game.team_scores
        
        # Binary payoffs based on winning team
        winning_team = 0 if scores[0] > scores[1] else 1
        for i in range(self.num_players):
            team_idx = i % 2
            payoffs[i] = 1.0 if team_idx == winning_team else 0.0
            
        return payoffs

    def _decode_action(self, action_id):
        ''' Convert action ID to game action '''
        legal_actions = self.game.get_legal_actions()
        if action_id < len(legal_actions):
            return legal_actions[action_id]
        return legal_actions[0]

    def _card_to_idx(self, card):
        ''' Convert card to numeric index '''
        suit_order = {'S': 0, 'H': 1, 'D': 2, 'C': 3}
        rank_order = {'2': 0, '3': 1, '4': 2, '5': 3, '6': 4, '7': 5, '8': 6,
                     '9': 7, 'T': 8, 'J': 9, 'Q': 10, 'K': 11, 'A': 12}
        
        suit = card.get_suit()
        rank = card.get_rank()
        return suit_order[suit] * 13 + rank_order[rank]

    def get_perfect_information(self):
        ''' Get complete game state information '''
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
        """Run a complete game and return trajectories and payoffs"""
        trajectories = [[] for _ in range(self.num_players)]
        state, player_id = self.reset()
        done = False
        
        while not done:
            action = self.agents[player_id].step(state)
            trajectories[player_id].append({
                'state': state,
                'action': action
            })
            
            try:
                next_state, reward, done, _ = self.step(action)
                state = next_state
                
                if not done:
                    player_id = self.game.get_player_id()
                    
            except Exception as e:
                done = True
                break
        
        payoffs = self.get_payoffs()
        
        # Determine winner and reset game
        winning_team = 0 if self.game.team_scores[0] > self.game.team_scores[1] else 1
        self.game.winner = winning_team
        self.game = Game()
        
        return trajectories, payoffs
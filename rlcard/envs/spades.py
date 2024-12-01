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
        legal_actions = self.game.get_legal_actions()
        legal_ids = {idx: None for idx in range(len(legal_actions))}
        return OrderedDict(legal_ids)

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
            'raw_legal_actions': list(legal_actions.keys()),
            'action_record': self.action_recorder
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
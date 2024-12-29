from .dealer import SpadesDealer
from .round import SpadesRound
from .player import SpadesPlayer
from .judger import SpadesJudger
import numpy as np
from rlcard.utils import init_standard_deck

class SpadesGame:
    def __init__(self, allow_step_back=False):
        self.num_players = 4
        self.allow_step_back = allow_step_back
        self.np_random = np.random.RandomState()
        # Players (Teams: 0,2 and 1,3 are partners)
        self.players = [SpadesPlayer(i) for i in range(self.num_players)]
        # Dealer and judger
        self.dealer = SpadesDealer(self.np_random)
        self.judger = SpadesJudger()
        self.round = None
        self.winner = None
        self.team_scores = [0, 0]  # Team 0,2 and Team 1,3
        self.team_bags = [0, 0]
        
        self.round_number = 0
        self.max_rounds = 50  # Preventing infinite games

    def init_game(self):
        """Initialize a new game or round"""
        if not hasattr(self, 'round_number'):
            # First time initialization
            self.round_number = 0
            self.team_scores = [0, 0]
            self.team_bags = [0, 0]
        else:
            self.round_number += 1
            print(f"Round number is: {self.round_number}")
            
        # Deal new hands
        self.dealer = SpadesDealer(self.np_random)
        self.dealer.shuffle()
        for player in self.players:
            player.reset()
        self.dealer.deal_cards(self.players)
        
        # Initialize new round
        self.round = SpadesRound(self.dealer, self.players)
        
        return self.get_state(self.round.current_player), self.round.current_player

    def step(self, action):
        """Execute one game step"""
        if not self.round:
            return self.init_game()
        
        # Process the action
        self.round.proceed_round(self.round.current_player, action)
        
        # Check if trick is complete
        if len(self.round.current_trick) == 4:
            winner = self.judger.judge_trick(self.round.current_trick)
            self.round.tricks_won[winner] += 1
            self.round.current_player = winner
            self.round.current_trick = []
        
        # Check if round is over
        if all(len(player.hand) == 0 for player in self.players):
            self.round_over()
            if self.is_over():
                return self.get_state(self.round.current_player), self.round.current_player
            # Set up new round
            self.round_number += 1
            self.dealer.deck = init_standard_deck()
            self.dealer.shuffle()
            for player in self.players:
                player.reset()
            self.dealer.deal_cards(self.players)
            self.round = SpadesRound(self.dealer, self.players)
        
        return self.get_state(self.round.current_player), self.round.current_player

    
    def round_over(self):
        """Calculate scores for the round"""
        team1_tricks = self.round.tricks_won[0] + self.round.tricks_won[2]
        team2_tricks = self.round.tricks_won[1] + self.round.tricks_won[3]
        
        # Get team bids
        team1_bid = self.round.bids[0] + self.round.bids[2]
        team2_bid = self.round.bids[1] + self.round.bids[3]
        

        # Calculate scores for each team
        for team_idx, (bid, tricks) in enumerate([(team1_bid, team1_tricks), 
                                                (team2_bid, team2_tricks)]):
            score_change = 0
            team_players = [0, 2] if team_idx == 0 else [1, 3]

            # Calculate base score for regular bids
            regular_bid_total = sum(self.round.bids[i] for i in team_players if self.round.bids[i] > 0)
            if regular_bid_total > 0:
                if tricks >= regular_bid_total:
                    # Made contract
                    score_change += regular_bid_total * 10  # Base score
                    
                    # Bonus for making bigger bids
                    if regular_bid_total >= 4:
                        score_change += 20  # Bonus for ambitious successful bids
                    
                    # Add overtrick points
                    bags = tricks - regular_bid_total
                    if bags > 0:
                        score_change += bags  # One point per overtrick
                        self.team_bags[team_idx] += bags
                        
                        # More forgiving bag penalty
                        if self.team_bags[team_idx] >= 10:
                            score_change -= 20  # Reduced penalty
                            self.team_bags[team_idx] -= 10
                else:
                    # Failed contract but with reduced penalty
                    penalty = max(10, regular_bid_total * 3)  # Minimum penalty of 10
                    score_change -= penalty

            # Handle nil bids
            for player in team_players:
                if self.round.bids[player] == 0:  # Nil bid
                    if self.round.tricks_won[player] == 0:
                        score_change += 100  # Made nil
                    else:
                        score_change -= 20  # Very small penalty for failed nil

            # Recovery mechanism
            if self.team_scores[team_idx] < 0:
                # Stronger recovery for teams that are behind
                if score_change > 0:
                    boost = min(abs(self.team_scores[team_idx]) // 5, 30)
                    score_change += boost

            # Progressive scoring (helps reaching 500)
            if self.team_scores[team_idx] > 200:
                score_change = int(score_change * 1.2)  # 20% bonus for high scores

            # Apply score change
            new_score = self.team_scores[team_idx] + score_change
            
            # Ensure scores stay in reasonable range
            if new_score < -200:
                new_score = -200
                
            self.team_scores[team_idx] = new_score
            
        #print(f"Team scores: {self.team_scores}")


    def is_over(self):
        """Check if the game is over"""
        # Game ends if either team:
        # 1. Reaches 500 points
        # 2. Goes below -200 points
        # 3. Max rounds reached
        if max(self.team_scores) >= 500:
            return True
        if min(self.team_scores) <= -200:
            return True
        if self.round_number >= 50:
            return True
        return False
    
    def is_round_over(self):
        """Check if current round is over"""
        return all(len(player.hand) == 0 for player in self.players)

    def get_state(self, player_id):
        """Get state for the given player id"""
        state = {}
        player = self.players[player_id]
        
        if not player:
            raise ValueError(f"Player {player_id} is not valid")
        
        state['hand'] = player.hand
        
        if self.round:
            state['current_trick'] = self.round.current_trick
            state['stage'] = self.round.stage
            state['bids'] = self.round.bids
            state['tricks_won'] = self.round.tricks_won
            state['spades_broken'] = self.round.spades_broken
        else:
            state['current_trick'] = []
            state['stage'] = 'bidding'
            state['bids'] = [-1, -1, -1, -1]
            state['tricks_won'] = [0, 0, 0, 0]
            state['spades_broken'] = False
        
        state['team_scores'] = self.team_scores
        state['team_bags'] = self.team_bags
        state['round_number'] = self.round_number
        
        return state

    def get_num_players(self):
        """Return the number of players in the game"""
        return self.num_players

    def get_num_actions(self):
        """Return the number of possible actions in the game"""
        return 52  # Maximum number of possible actions

    def get_player_id(self):
        """Return the current player's id"""
        return self.round.current_player

    def get_legal_actions(self):
        """Return the legal actions for current player"""
        return self.players[self.round.current_player].get_legal_actions(self.round)

    def step_back(self):
        """Restore the game to the previous state"""
        if not self.allow_step_back:
            raise Exception('Step back not allowed')
        self.round = self.history.pop()
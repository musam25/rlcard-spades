from rlcard.games.spades.dealer import SpadesDealer
from rlcard.games.spades.round import SpadesRound
from rlcard.games.spades.player import SpadesPlayer

class SpadesGame:
    def __init__(self, allow_step_back=False):
        self.num_players = 4
        self.allow_step_back = allow_step_back
        self.np_random = np.random.RandomState()
        # Initialize players (Teams: 0,2 and 1,3 are partners)
        self.players = [SpadesPlayer(i) for i in range(self.num_players)]
        # Initialize dealer and judger
        self.dealer = SpadesDealer(self.np_random)
        self.judger = SpadesJudger()
        self.round = None
        # Game state
        self.team_scores = [0, 0]  # Team 0,2 and Team 1,3
        self.team_bags = [0, 0]

    def init_game(self):
        """Initialize a new round"""
        # Shuffle and deal
        self.dealer.shuffle()
        self.dealer.deal_cards(self.players)
        # Initialize round
        self.round = SpadesRound(self.dealer, self.players)
        # Get first player's state
        state = self.get_state(self.round.current_player)
        return state, self.round.current_player
    def step(self, action):
        """Execute one game step"""
        # Process the action
        self.round.proceed_round(self.round.current_player, action)
        
        # Check if trick is complete
        if len(self.round.current_trick) == 4:
            winner = self.judger.judge_trick(self.round.current_trick)
            self.round.tricks_won[winner] += 1
            self.round.current_player = winner
            self.round.current_trick = []
            
        # Check if round is over
        if len(self.players[0].hand) == 0:
            self.round_over()
            
        # Get next state
        state = self.get_state(self.round.current_player)
        return state, self.round.current_player
    def get_state(self, player_id):
        """Return player's state
        
        Args:
            player_id (int): The player id
            
        Returns:
            dict: The state dictionary
        """
        state = {}
        
        # Get player's hand
        state['hand'] = self.players[player_id].hand
        
        # Get bidding information
        state['bids'] = self.round.bids.copy()
        
        # Get current trick information
        state['current_trick'] = self.round.current_trick.copy()
        
        # Get trick counts
        state['tricks_won'] = self.round.tricks_won.copy()
        
        # Get spades broken status
        state['spades_broken'] = self.round.spades_broken
        
        # Get game score
        state['team_scores'] = self.team_scores.copy()
        state['team_bags'] = self.team_bags.copy()
        
        # Get current game stage
        state['stage'] = self.round.stage
        
        return state

    def round_over(self):
        """Calculate scores and reset for next round"""
        # Calculate team tricks
        team1_tricks = self.round.tricks_won[0] + self.round.tricks_won[2]
        team2_tricks = self.round.tricks_won[1] + self.round.tricks_won[3]
        
        # Get team bids
        team1_bid = self.round.bids[0] + self.round.bids[2]
        team2_bid = self.round.bids[1] + self.round.bids[3]
        
        # Calculate scores and bags
        for team_idx, (bid, tricks) in enumerate([(team1_bid, team1_tricks), 
                                                (team2_bid, team2_tricks)]):
            if tricks >= bid:  # Made contract
                self.team_scores[team_idx] += bid * 10  # 10 points per trick bid
                bags = tricks - bid
                self.team_bags[team_idx] += bags
                self.team_scores[team_idx] += bags  # 1 point per overtrick
                
                # Check for bag penalty
                if self.team_bags[team_idx] >= 10:
                    self.team_scores[team_idx] -= 100  # Penalty for 10 bags
                    self.team_bags[team_idx] -= 10
            else:  # Set (didn't make contract)
                self.team_scores[team_idx] -= bid * 10

    def is_over(self):
        """Check if the game is over"""
        # Game ends when a team reaches 500 points
        return max(self.team_scores) >= 500

    def get_num_players(self):
        """Return the number of players in the game"""
        return self.num_players

    def get_num_actions(self):
        """Return the number of possible actions in the game"""
        # During bidding: 14 possible bids (0-13)
        # During play: 52 possible cards (though only some will be legal)
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
        # Restore from history
        self.round = self.history.pop()
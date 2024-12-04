import numpy as np

class SpadesRound:
    def __init__(self, dealer, players):
        """Initialize a round class
        
        Args:
            dealer: The dealer instance
            players: List of 4 player instances
        """
        self.dealer = dealer
        self.players = players
        self.current_player = 0  # First player to bid/play
        self.current_trick = []
        self.trick_leader = 0  # Player who led current trick
        self.trick_history = []  # Keep track of all tricks played
        self.spades_broken = False
        self.bids = [-1, -1, -1, -1]  # -1 means hasn't bid yet
        self.tricks_won = [0, 0, 0, 0]
        self.stage = 'bidding'  # 'bidding' or 'playing'
        self.led_suit = None  # Current trick's led suit

    def proceed_round(self, player_id, action):
        """Process a player's action in the round"""
        if player_id != self.current_player:
            raise ValueError(f"Not player {player_id}'s turn")

        # Check if player has cards before proceeding
        if not self.players[player_id].hand:
            return True

        if self.stage == 'bidding':
            # Convert action to bid (should be 0-13)
            bid = int(action) if isinstance(action, (int, np.integer)) else 0
            bid = max(0, min(13, bid))  # Ensure bid is between 0 and 13
            return self._handle_bid(player_id, bid)
        else:  # stage == 'playing'
            legal_actions = self.players[player_id].get_legal_actions(self)
            if not legal_actions:
                return True  # No valid actions means round should end
            
            # Convert action index to actual card
            if isinstance(action, (int, np.integer)):
                action_idx = action % len(legal_actions)
                card = legal_actions[action_idx]
            else:
                card = np.random.choice(legal_actions)
            
            return self._handle_play(player_id, card)

    def _handle_bid(self, player_id, bid):
        """Handle a player's bid"""
        # Ensure bid is reasonable
        if not isinstance(bid, (int, np.integer)) or bid < 0 or bid > 13:
            # Generate a more realistic bid based on hand strength
            hand = self.players[player_id].hand
            spades = len([c for c in hand if c.suit == 'S'])
            high_cards = len([c for c in hand if c.rank in ['A', 'K', 'Q']])
            suggested_bid = min(13, max(1, (spades + high_cards) // 3))
            bid = suggested_bid
            
        self.bids[player_id] = bid
        self.players[player_id].set_bid(bid)
        self.current_player = (player_id + 1) % 4
        
        # Check if bidding is complete
        if all(b != -1 for b in self.bids):
            self.stage = 'playing'
            self.current_player = (self.dealer.first_player + 1) % 4
            self.trick_leader = self.current_player
        
        return True

    def _handle_play(self, player_id, card):
        """Handle a player playing a card"""
        # Validate card can be played
        if not self._is_valid_play(player_id, card):
            raise ValueError(f"Invalid play: {card}")

        # Play the card
        self.players[player_id].play_card(card)
        self.current_trick.append(card)
        
        # Set led suit for first card of trick
        if len(self.current_trick) == 1:
            self.led_suit = card.suit
            
        # Check if spades are broken
        if card.suit == 'S' and not self.spades_broken:
            self.spades_broken = True

        # Move to next player or complete trick
        if len(self.current_trick) == 4:
            self._complete_trick()
        else:
            self.current_player = (player_id + 1) % 4
            
        return True

    def _is_valid_play(self, player_id, card):
        """Check if a card play is valid"""
        player = self.players[player_id]
        
        # Must have the card
        if card not in player.hand:
            return False
            
        # If leading, check spades restriction
        if not self.current_trick:
            if card.suit == 'S' and not self.spades_broken:
                # Can only lead spades if no other option
                return all(c.suit == 'S' for c in player.hand)
        
        # Must follow suit if possible
        elif self.led_suit:
            has_suit = any(c.suit == self.led_suit for c in player.hand)
            if has_suit and card.suit != self.led_suit:
                return False
                
        return True

    def _complete_trick(self):
        """Handle completion of a trick"""
        # Determine winner
        winning_card = max(self.current_trick, 
                        key=lambda c: (c.suit == 'S', c.suit == self.led_suit, c.rank))
        winner = (self.trick_leader + self.current_trick.index(winning_card)) % 4
        
        # Update state
        self.tricks_won[winner] += 1
        self.trick_history.append(self.current_trick.copy())
        
        # Setup next trick
        self.current_trick = []
        self.led_suit = None
        self.current_player = winner
        self.trick_leader = winner

    def get_led_suit(self):
        """Get the current trick's led suit"""
        return self.led_suit

    def is_round_over(self):
        """Check if the round is complete"""
        return len(self.trick_history) == 13

    def get_trick_winner(self, trick):
        """Get the winner of a specific trick"""
        winning_card = max(trick, 
                         key=lambda c: (c.suit == 'S', c.suit == trick[0].suit, c.rank))
        return (self.trick_leader + trick.index(winning_card)) % 4
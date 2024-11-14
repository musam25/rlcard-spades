class SpadesPlayer:
    def __init__(self, player_id):
        self.player_id = player_id
        self.hand = []
        self.bid = -1
        self.tricks_won = 0  # Track tricks won by this player

    def get_legal_actions(self, round_state):
        """Get legal cards that can be played
        
        Args:
            round_state: Current round state containing game information
            
        Returns:
            list: List of legal actions (cards or bids)
        """
        if not round_state:
            raise ValueError("Round state cannot be None")

        if round_state.stage == 'bidding':
            return list(range(14))  # Can bid 0-13 tricks
        
        if not self.hand:
            raise ValueError("Player has no cards in hand")

        # If playing stage
        legal_actions = []
        led_suit = round_state.get_led_suit()
        
        # Must follow suit if possible
        if led_suit:
            same_suit_cards = [card for card in self.hand if card.suit == led_suit]
            if same_suit_cards:
                return same_suit_cards
                
        # Leading the trick
        if not round_state.current_trick:
            # Can't lead spades unless broken or only has spades
            if not round_state.spades_broken:
                non_spades = [card for card in self.hand if card.suit != 'S']
                if non_spades:
                    return non_spades
                    
        # Can play anything if can't follow suit or leading with only spades
        return self.hand.copy()  # Return copy to prevent modification

    def play_card(self, card):
        """Play a card from the player's hand
        
        Args:
            card: Card to play
            
        Returns:
            bool: True if card was successfully played
        """
        if card not in self.hand:
            raise ValueError(f"Card {card} not in player's hand")
        self.hand.remove(card)
        return True

    def add_card(self, card):
        """Add a card to the player's hand
        
        Args:
            card: Card to add
        """
        self.hand.append(card)

    def set_bid(self, bid):
        """Set the player's bid
        
        Args:
            bid (int): Number of tricks bid (0-13)
        """
        if not 0 <= bid <= 13:
            raise ValueError(f"Invalid bid: {bid}. Must be between 0 and 13")
        self.bid = bid

    def get_partner_id(self):
        """Get the ID of this player's partner"""
        return (self.player_id + 2) % 4

    def get_team_id(self):
        """Get the team ID (0 or 1) for this player"""
        return self.player_id % 2

    def reset(self):
        """Reset player state for new round"""
        self.hand = []
        self.bid = -1
        self.tricks_won = 0
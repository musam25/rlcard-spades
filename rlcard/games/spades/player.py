import numpy as np
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
        
        if not self.hand:
            return []
        
        if round_state.stage == 'bidding':
            return list(range(14))  # Can bid 0-13 tricks
        
        # If playing stage
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
    def evaluate_hand_strength(self):
        """Evaluate the strength of a hand for bidding"""
        score = 0
        spades_count = 0
        high_cards = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}
        
        for card in self.hand:
            # Count spades separately
            if card.suit == 'S':
                spades_count += 1
                if card.rank in high_cards:
                    score += high_cards[card.rank] * 1.5  # Spades worth more
            else:
                # Score high cards in other suits
                if card.rank in high_cards:
                    score += high_cards[card.rank]
                
            # Add points for void suits (no cards in a suit)
            suits = {'H': 0, 'D': 0, 'C': 0}
            for card in self.hand:
                if card.suit in suits:
                    suits[card.suit] += 1
            for count in suits.values():
                if count == 0:  # Void in suit
                    score += 2
                elif count == 1:  # Singleton
                    score += 1
                    
        # Estimate tricks based on hand strength
        estimated_tricks = (score / 3) + (spades_count / 2)
        return max(0, min(13, round(estimated_tricks)))

    def suggest_bid(self, round_state):
        """Suggest a reasonable bid based on hand strength and partner's bid"""
        if round_state.stage != 'bidding':
            return 0
        return np.random.randint(2,4)   
        # Get partner's bid if made
        partner_id = (self.player_id + 2) % 4
        partner_bid = round_state.bids[partner_id]
        
        # Evaluate own hand
        hand_strength = self.evaluate_hand_strength()
        
        # If partner hasn't bid yet
        if partner_bid == -1:
            return min(hand_strength, 7)  # Conservative initial bid
            
        # If partner has bid, ensure combined bid is reasonable
        max_possible_bid = 13 - partner_bid
        suggested_bid = min(hand_strength, max_possible_bid)
        
        return suggested_bid
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
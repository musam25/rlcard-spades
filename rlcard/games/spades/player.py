import numpy as np
class SpadesPlayer:
    def __init__(self, player_id):
        self.player_id = player_id
        self.hand = []
        self.bid = -1
        self.tricks_won = 0

    def evaluate_hand_for_bid(self, partner_bid=-1):
        """Evaluate hand strength to make an intelligent bid
        
        Args:
            partner_bid (int): Partner's bid if they've already bid, -1 if not yet bid
            
        Returns:
            int: Recommended bid (0-13)
        """
        if not self.hand:
            return 0
            
        # Initialize trick count
        probable_tricks = 0
        
        # Count spades and high cards
        spades = [card for card in self.hand if card.get_suit() == 'S']
        high_spades = [card for card in spades if card.get_rank() in ['A', 'K', 'Q']]
        
        # Each high spade is likely a trick
        probable_tricks += len(high_spades)
        
        # Lower spades might win tricks too
        if len(spades) > 3:
            probable_tricks += (len(spades) - 3) * 0.5
        
        # Count aces and kings in other suits
        for suit in ['H', 'D', 'C']:
            suit_cards = [card for card in self.hand if card.get_suit() == suit]
            aces = len([card for card in suit_cards if card.get_rank() == 'A'])
            kings = len([card for card in suit_cards if card.get_rank() == 'K'])
            
            # Aces are likely tricks
            probable_tricks += aces
            
            # Kings are probable tricks if we have length in the suit
            if len(suit_cards) >= 3:
                probable_tricks += kings * 0.75
        
        # Consider void suits
        for suit in ['H', 'D', 'C']:
            if not any(card.get_suit() == suit for card in self.hand):
                probable_tricks += len(spades) * 0.25  # Potential ruff
        
        # Check for nil potential
        high_cards = len([card for card in self.hand 
                         if card.get_rank() in ['A', 'K', 'Q', 'J']])
        if high_cards <= 2 and len(spades) <= 2:
            return 0  # Good nil hand
        
        # Adjust based on partner's bid if available
        if partner_bid != -1:
            team_bid = partner_bid + int(probable_tricks)
            if team_bid > 13:  # Don't overbid as a team
                probable_tricks = max(1, 13 - partner_bid)
        
        # Final adjustments
        final_bid = int(round(probable_tricks))
        final_bid = max(1, min(13, final_bid))  # Ensure bid is between 1 and 13
        
        return final_bid

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
            # If bidding, use hand evaluation
            partner_bid = round_state.bids[(self.player_id + 2) % 4]
            suggested_bid = self.evaluate_hand_for_bid(partner_bid)
            
            # Return reasonable range around suggested bid
            lower = max(0, suggested_bid - 1)
            upper = min(13, suggested_bid + 1)
            return list(range(lower, upper + 1))
        
        # Playing stage
        if not self.hand:
            raise ValueError("Player has no cards in hand")
            
        led_suit = round_state.get_led_suit()
        
        # Must follow suit if possible
        if led_suit:
            same_suit_cards = [card for card in self.hand if card.get_suit() == led_suit]
            if same_suit_cards:
                return same_suit_cards
                
        # Leading the trick
        if not round_state.current_trick:
            # Can't lead spades unless broken or only has spades
            if not round_state.spades_broken:
                non_spades = [card for card in self.hand if card.get_suit() != 'S']
                if non_spades:
                    return non_spades
                    
        # Can play anything if can't follow suit or leading with only spades
        return self.hand.copy()

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
        """Add a card to the player's hand"""
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
from rlcard.utils import init_standard_deck
import numpy as np

STARTING_HAND = 13

class SpadesDealer:
    def __init__(self, np_random):
        ''' Initialize a Spades dealer class
        Note: Spades always uses exactly one deck
        '''
        self.np_random = np_random
        self.deck = init_standard_deck()
        self.first_player = 0  # Add this property to track who plays first
        self.shuffle()

    def shuffle(self):
        ''' Shuffle the deck and rotate dealer position
        '''
        shuffle_deck = np.array(self.deck)
        self.np_random.shuffle(shuffle_deck)
        self.deck = list(shuffle_deck)
        # Rotate first player (dealer's left) for next hand
        self.first_player = (self.first_player + 1) % 4

    def deal_cards(self, players):
        """Deal 13 cards to each player at the start of a round"""
        if len(players) != 4:
            print(f"Error: Got {len(players)} players instead of 4")  # Debug
            raise ValueError("Spades requires exactly 4 players")
        if len(self.deck) != 52:
            print(f"Error: Deck size is {len(self.deck)} instead of 52")  # Debug
            raise ValueError("Deck must be full before dealing")
            
        print("Starting to deal cards")  # Debug
        for _ in range(STARTING_HAND):
            for player in players:
                card = self.deck.pop()
                player.hand.append(card)
        print("All cards dealt")
    def get_deck(self):
        ''' Return the current deck
        '''
        return self.deck
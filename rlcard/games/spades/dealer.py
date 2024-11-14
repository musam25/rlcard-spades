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
        self.shuffle()

    def shuffle(self):
        ''' Shuffle the deck
        '''
        shuffle_deck = np.array(self.deck)
        self.np_random.shuffle(shuffle_deck)
        self.deck = list(shuffle_deck)

    def deal_cards(self, players):
        ''' Deal 13 cards to each player at the start of a round
        
        Args:
            players (list): List of 4 player objects
        '''
        if len(players) != 4:
            raise ValueError("Spades requires exactly 4 players")
        if len(self.deck) != 52:
            raise ValueError("Deck must be full before dealing")
        # In Spades, each player gets exactly 13 cards
        for _ in range(STARTING_HAND):
            for player in players:
                card = self.deck.pop()
                player.hand.append(card)

    def get_deck(self):
        ''' Return the current deck
        '''
        return self.deck
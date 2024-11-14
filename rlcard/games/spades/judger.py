class SpadesJudger:
    @staticmethod
    def judge_trick(trick, led_suit):
        """Judge the winner of a trick
        
        Args:
            trick (list): List of 4 cards played in the trick
            led_suit (string): The suit that was led
            
        Returns:
            int: The player_id of the winner (0-3)
        """
        highest_spade = -1
        highest_led = -1
        winner = -1
        
        # First look for highest spade (trump)
        for i, card in enumerate(trick):
            if card.suit == 'S':
                if highest_spade == -1 or card.rank > trick[highest_spade].rank:
                    highest_spade = i
                    winner = i
        
        # If no spades, look for highest card of led suit
        if highest_spade == -1:
            for i, card in enumerate(trick):
                if card.suit == led_suit:
                    if highest_led == -1 or card.rank > trick[highest_led].rank:
                        highest_led = i
                        winner = i
        
        return winner
    
    @staticmethod
    def calculate_nil_score(bid, tricks):
        """Calculate score for a nil bid
        
        Args:
            bid (int): Player's bid (should be 0 for nil)
            tricks (int): Number of tricks taken
            
        Returns:
            int: Score (100 for successful nil, -100 for failed nil)
        """
        if bid == 0 and tricks == 0:
            return 100  # Successful nil
        return -100    # Failed nil
    
    @staticmethod
    def calculate_team_score(bid, tricks):
        """Calculate score for a team's regular (non-nil) bid
        
        Args:
            bid (int): Team's combined bid
            tricks (int): Team's combined tricks
            
        Returns:
            tuple: (score, bags)
        """
        if tricks < bid:
            return (-bid * 10, 0)  # Set (failed to make bid)
        
        score = bid * 10  # Base score for making bid
        bags = tricks - bid  # Overtricks
        score += bags  # Add 1 point per bag
        
        return (score, bags)
    
    @staticmethod
    def check_bag_penalty(current_bags):
        """Check if team has accumulated 10 bags
        
        Args:
            current_bags (int): Current number of bags
            
        Returns:
            tuple: (penalty_points, remaining_bags)
        """
        if current_bags >= 10:
            return (-100, current_bags - 10)
        return (0, current_bags)

    def judge_round(self, bids, tricks_won):
        """Judge the entire round
        
        Args:
            bids (list): List of 4 bids
            tricks_won (list): List of tricks won by each player
            
        Returns:
            tuple: (team1_score, team2_score, team1_bags, team2_bags)
        """
        # Calculate team tricks
        team1_tricks = tricks_won[0] + tricks_won[2]
        team2_tricks = tricks_won[1] + tricks_won[3]
        
        # Calculate team bids (excluding nil)
        team1_bid = sum(b for i, b in enumerate(bids) if i % 2 == 0 and b != 0)
        team2_bid = sum(b for i, b in enumerate(bids) if i % 2 == 1 and b != 0)
        
        # Calculate regular bid scores
        team1_score, team1_bags = self.calculate_team_score(team1_bid, team1_tricks)
        team2_score, team2_bags = self.calculate_team_score(team2_bid, team2_tricks)
        
        # Add nil bid scores
        for i, bid in enumerate(bids):
            if bid == 0:  # Nil bid
                nil_score = self.calculate_nil_score(bid, tricks_won[i])
                if i % 2 == 0:  # Team 1
                    team1_score += nil_score
                else:  # Team 2
                    team2_score += nil_score
        
        return (team1_score, team2_score, team1_bags, team2_bags)
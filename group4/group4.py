"""
**Submitted to ANAC 2024 Automated Negotiation League**
*Team* type your team name here
*Authors* type your team member names with their emails here

This code is free to use or update given that proper attribution is given to
the authors and the ANAC 2024 ANL competition.
"""
import random

from negmas.outcomes import Outcome
from negmas.sao import ResponseType, SAONegotiator, SAOResponse, SAOState


class Group4(SAONegotiator):
    """
    Your agent code. This is the ONLY class you need to implement
    """

    rational_outcomes = tuple()

    partner_reserved_value = 0.01

    def on_preferences_changed(self, changes):
        """
        Called when preferences change. In ANL 2024, this is equivalent with initializing the agent.

        Remarks:
            - Can optionally be used for initializing your agent.
            - We use it to save a list of all rational outcomes.

        """
        # If there a no outcomes (should in theory never happen)
        if self.ufun is None:
            return

        self.rational_outcomes = self.get_outcomes()

        # Estimate the reservation value, as a first guess, the opponent has the same reserved_value as you
        self.partner_reserved_value = 0

    def __call__(self, state: SAOState) -> SAOResponse:
        """
        Called to (counter-)offer.

        Args:
            state: the `SAOState` containing the offer from your partner (None if you are just starting the negotiation)
                   and other information about the negotiation (e.g. current step, relative time, etc).
        Returns:
            A response of type `SAOResponse` which indicates whether you accept, or reject the offer or leave the negotiation.
            If you reject an offer, you are required to pass a counter offer.

        Remarks:
            - This is the ONLY function you need to implement.
            - You can access your ufun using `self.ufun`.
            - You can access the opponent's ufun using self.opponent_ufun(offer)
            - You can access the mechanism for helpful functions like sampling from the outcome space using `self.nmi` (returns an `SAONMI` instance).
            - You can access the current offer (from your partner) as `state.current_offer`.
              - If this is `None`, you are starting the negotiation now (no offers yet).
        """
        offer = state.current_offer

        self.update_partner_reserved_value(state)

        # if there are no outcomes (should in theory never happen)
        if self.ufun is None:
            return SAOResponse(ResponseType.END_NEGOTIATION, None)

        # Determine the acceptability of the offer in the acceptance_strategy
        if self.acceptance_strategy(state):
            return SAOResponse(ResponseType.ACCEPT_OFFER, offer)

        # If it's not acceptable, determine the counter offer in the bidding_strategy
        return SAOResponse(ResponseType.REJECT_OFFER, self.bidding_strategy(state))

    def acceptance_strategy(self, state: SAOState) -> bool:
        """
        This is one of the functions you need to implement.
        It should determine whether or not to accept the offer.

        Returns: a bool.
        """
        assert self.ufun

        offer = state.current_offer
        process = self.relative_time(state)
        outcomes = self.get_outcomes()
        best_outcomes = outcomes[:int(0.3 * len(outcomes))]
        
        if(offer in best_outcomes):
            return True
        
        if process > 0.5:
            if self.ufun(offer) > (2 * self.ufun.reserved_value):
                return True
        
        if process > 0.9:
            if self.ufun(offer) > (self.ufun.reserved_value):
                return True
        
        return False

    def bidding_strategy(self, state: SAOState) -> Outcome | None:
        """
        This is one of the functions you need to implement.
        It should determine the counter offer.

        Returns: The counter offer as Outcome.
        """

        # The opponent's ufun can be accessed using self.opponent_ufun, which is not used yet.
        offer = state.current_offer

        outcomes = self.get_outcomes()
        best_outcomes = outcomes[:int(0.2 * len(outcomes))]
        possible_outcomes = sorted(best_outcomes, key=lambda o: self.opponent_ufun(o), reverse=True)

        return possible_outcomes[0]
 
    def update_partner_reserved_value(self, state: SAOState) -> None:
        """This is one of the functions you can implement.
        Using the information of the new offers, you can update the estimated reservation value of the opponent.

        returns: None.
        """
        assert self.ufun and self.opponent_ufun

        offer = state.current_offer
        process = self.relative_time(state)

        # If the opponent's ufun is lower than the current reserved value, 
        if self.opponent_ufun(offer) < self.partner_reserved_value:
            self.partner_reserved_value = float(self.opponent_ufun(offer)) / 2
        
        else:
            self.partner_reserved_value = 0.75 * process
        # update rational_outcomes by removing the outcomes that are below the reservation value of the opponent
        # Watch out: if the reserved value decreases, this will not add any outcomes.
        self.rational_outcomes = self.get_outcomes()

    # Helper functions

    # def get_step(self, state: SAOState) -> tuple[float, int, int]: # that is actually the same as self.relative_time
    #     step = state.step
    #     total = self.nmi.n_steps
    #     progress = step / total
    #     # print(f"Progress is {progress} and relative_time is {state.relative_time}")
    #     return progress, step, total # check later what actually needed to return
    
    def get_outcomes(self): 
        outcomes = [
            x for x in self.nmi.outcome_space.enumerate_or_sample()  # enumerates outcome space when finite, samples when infinite
            if self.ufun(x) > self.ufun.reserved_value
        ]
        
        possible_outcomes = [
            x for x in outcomes
            if self.opponent_ufun(x) >= self.partner_reserved_value
        ]

        possible_outcomes = sorted(possible_outcomes, key=lambda o: self.ufun(o), reverse=True)
        return possible_outcomes
        
    def track_opponent_behavior(self, state: SAOState) -> None:
        """
        Tracks the opponent's behavior (Conceder/Boulware) based on the last 5 offers.
        """
        if not hasattr(self, "opponent_offers"):
            self.opponent_offers = []

        offer = state.current_offer
        if offer:
            self.opponent_offers.append(self.opponent_ufun(offer))

        # Keep only the last 5 offers
        if len(self.opponent_offers) > 5:
            self.opponent_offers.pop(0)

        # Analyze the trend of concessions by the opponent
        if len(self.opponent_offers) == 5:
            concessions = [self.opponent_offers[i] - self.opponent_offers[i + 1] for i in range(len(self.opponent_offers)-1)]
            avg_concession = sum(concessions) / len(concessions)

            # Determine opponent's behavior
            self.opponent_style = "Conceder" if avg_concession > 0.05 else "Boulware"
        else:
            self.opponent_style = None


# if you want to do a very small test, use the parameter small=True here. Otherwise, you can use the default parameters.
if __name__ == "__main__":
    from .helpers.runner import run_a_tournament
    run_a_tournament(Group4, small=False, debug=True)
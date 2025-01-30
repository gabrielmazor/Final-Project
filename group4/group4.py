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

    rational_outcomes = []


    partner_reserved_value = 0

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
        self.partner_reserved_value = 0.05

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
        # print(state.step)
        # print(self.nmi.n_steps)
        self.update_partner_reserved_value(state)
        print()
        print(f"Agent reserved value: {self.ufun.reserved_value}")
        print(f"Opponent reserved value: {self.partner_reserved_value}")
        print(f"Step ratio: {self.step_ratio(state)}")
        # if there are no outcomes (should in theory never happen)
        if self.ufun is None:
            return SAOResponse(ResponseType.END_NEGOTIATION, None)

        # Determine the acceptability of the offer in the acceptance_strategy
        if self.acceptance_strategy(state):
            return SAOResponse(ResponseType.ACCEPT_OFFER, offer)

        # If it's not acceptable, determine the counter offer in the bidding_strategy
        bid = self.bidding_strategy(state)
        print(f"Agent utility: {self.ufun(bid)}")
        print(f"Opponent utility: {self.opponent_ufun(bid)}")
        return SAOResponse(ResponseType.REJECT_OFFER, bid)

    def acceptance_strategy(self, state: SAOState) -> bool:
        """
        This is one of the functions you need to implement.
        It should determine whether or not to accept the offer.

        Returns: a bool.
        """
        assert self.ufun

        offer = state.current_offer
        outcomes = self.get_outcomes()
        top_outcomes = outcomes[:0.25*len(outcomes)]
        
        utility = self.ufun(offer)
        opp_utility = self.opponent_ufun(offer)
        if self.step_ratio(state) > 0.9:
            if utility > (self.ufun.reserved_value):
                return True

        if utility > self.ufun.reserved_value:
            return random.choice(self.top_outcomes)
            return True
        return False

    def bidding_strategy(self, state: SAOState) -> Outcome | None:
        """
        This is one of the functions you need to implement.
        It should determine the counter offer.

        Returns: The counter offer as Outcome.
        """
        # opponent_ufun = self.opponent_ufun(state.current_offer)
        # ufun = self.ufun(state.current_offer)
        # # The opponent's ufun can be accessed using self.opponent_ufun, which is not used yet.

        # return random.choice(self.rational_outcomes)
        
        outcomes = self.get_outcomes()

        if not outcomes:
            # fallback: if nothing is feasible for the opponent
            # at least pick something feasible for you:
            # feasible_outcomes = list(self.rational_outcomes)
            # if not feasible_outcomes:
            #     return None
            return None

        # Among feasible outcomes, pick the one that gives the maximum sum of utilities
        out_len = len(outcomes)
        bid = max(
            outcomes[:0.25*out_len],
            key=lambda o: 0.7 * self.ufun(o) + 0.3 * self.opponent_ufun(o)
        )
        print(bid)
        return bid

    def update_partner_reserved_value(self, state: SAOState) -> None:
        """This is one of the functions you can implement.
        Using the information of the new offers, you can update the estimated reservation value of the opponent.

        returns: None.
        """
        assert self.ufun and self.opponent_ufun
        step_ratio = self.step_ratio(state)
        
        offer = state.current_offer
        self.partner_reserved_value += step_ratio * 0.1 * self.opponent_ufun(offer)

        if self.opponent_ufun(offer) < self.partner_reserved_value:
            self.partner_reserved_value = float(self.opponent_ufun(offer)) / 2

        # update rational_outcomes by removing the outcomes that are below the reservation value of the opponent
        # Watch out: if the reserved value decreases, this will not add any outcomes.
        self.rational_outcomes = self.get_outcomes()    
    

    ######
    # Helper functions

    def step_ratio(self, state: SAOState) -> float:
        step = state.step
        total_steps = self.nmi.n_steps
        return step / total_steps

    def get_outcomes(self):
        """
        Update the liest of rational outcomes.
        """

        outcomes = [
            x for x in self.nmi.outcome_space.enumerate_or_sample()  # enumerates outcome space when finite, samples when infinite
            if self.ufun(x) > self.ufun.reserved_value
        ]
        
        possible_outcomes = [
            x for x in outcomes
            if self.opponent_ufun(x) >= self.partner_reserved_value
        ]

        possible_outcomes = possible_outcomes.sort(key=lambda o: self.ufun(o), reverse=True)

        return possible_outcomes
    
# if you want to do a very small test, use the parameter small=True here. Otherwise, you can use the default parameters.
if __name__ == "__main__":
    from helpers.runner import run_a_tournament

    run_a_tournament(Group4, small=True, debug=True)

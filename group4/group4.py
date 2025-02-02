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
    opponent_rational_outcomes = tuple()
    joint_outcomes = tuple()

    opponent_reserved_value = 0.01
    opponent_style = None
    opponent_offers = []
    opponent_avg = 1
    lowest_offer = 1

    exp = 1

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
        
        # Estimate the reservation value, as a first guess, the opponent has the same reserved_value as you
        self.opponent_reserved_value = self.ufun.reserved_value

        # Get the rational outcomes for both parties
        self.rational_outcomes = [
            _
            for _ in self.nmi.outcome_space.enumerate_or_sample()  # enumerates outcome space when finite, samples when infinite
            if self.ufun(_) > self.ufun.reserved_value
        ]

        self.opponent_rational_outcomes = [
            _
            for _ in self.nmi.outcome_space.enumerate_or_sample()  # enumerates outcome space when finite, samples when infinite
            if self.opponent_ufun(_) > self.opponent_reserved_value
        ]
        
        self.joint_outcomes = list(set(self.rational_outcomes) & set(self.opponent_rational_outcomes))
        
        # Sort rational outcomes by utility
        self.joint_outcomes.sort(key=lambda o: self.ufun(o), reverse=True)

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
        
        if state.relative_time < 0.5:
            self.classify_opponent(state)

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

        tresh = self.ufun.reserved_value + (self.ufun(self.joint_outcomes[0]) - self.ufun.reserved_value) * (1-state.relative_time ** self.exp)
        
        if state.relative_time < 0.5:
            if self.ufun(offer) > tresh:
                if self.opponent_ufun(offer) < self.ufun(offer):
                    return True
        
        if self.opponent_style == "Boulware":
            if state.relative_time < 0.9:
                return False

        if self.ufun(offer) > tresh:
            return True
        return False

    def bidding_strategy(self, state: SAOState) -> Outcome | None:
        """
        This is one of the functions you need to implement.
        It should determine the counter offer.

        Returns: The counter offer as Outcome.
        """

        if self.opponent_style == "Conceder":
            options = [o for o in self.joint_outcomes if self.opponent_ufun(o) > self.lowest_offer]
            options = [o for o in options if self.ufun(o) > self.opponent_ufun(o)]
            if options:
                return options[0]
        elif self.opponent_style == "Boulware":
            options = [o for o in self.joint_outcomes if abs(self.opponent_ufun(o) - self.lowest_offer) <= 0.1]
            options = [o for o in options if self.ufun(o) > self.opponent_ufun(o)]
            if options:
                return options[0]
            else:
                options = [o for o in self.joint_outcomes if self.opponent_ufun(o) > self.lowest_offer]
                options = [o for o in options if self.ufun(o) > self.opponent_ufun(o)]
                if options:
                    return options[0]
        # The opponent's ufun can be accessed using self.opponent_ufun, which is not used yet.
        return self.joint_outcomes[0]

    def update_partner_reserved_value(self, state: SAOState) -> None:
        """This is one of the functions you can implement.
        Using the information of the new offers, you can update the estimated reservation value of the opponent.

        returns: None.
        """
        assert self.ufun and self.opponent_ufun

        offer = state.current_offer
        
        # Update lowest offer
        if self.opponent_ufun(offer) < self.lowest_offer:
            self.lowest_offer = self.opponent_ufun(offer)

        # Append offer to opponent offers
        self.opponent_offers.append(self.opponent_ufun(offer))
        if len(self.opponent_offers) >= 5:
            self.opponent_avg = sum(self.opponent_offers[-5:]) / 5
        else:
            self.opponent_avg = self.lowest_offer

        if self.opponent_style == "Boulware":
            r = self.opponent_avg * state.relative_time * 0.75
        else:
            r = self.opponent_avg * state.relative_time * 0.4

        if r >= self.opponent_reserved_value:
            self.opponent_reserved_value = r
        else:
        # reserved value decreased, updating the rational outcomes
            self.opponent_rational_outcomes = [
                _
                for _ in self.nmi.outcome_space.enumerate_or_sample()  # enumerates outcome space when finite, samples when infinite
                if self.opponent_ufun(_) > self.opponent_reserved_value
            ]

        # update rational_outcomes by removing the outcomes that are below the reservation value of the opponent
   
        self.opponent_rational_outcomes = [
            _
            for _ in self.opponent_rational_outcomes
            if self.opponent_ufun(_) > self.opponent_reserved_value
        ]
        
        self.joint_outcomes = list(set(self.rational_outcomes) & set(self.opponent_rational_outcomes))
        
        # if no intersection, set joint_outcomes to rational_outcomes
        if not self.joint_outcomes:
            self.joint_outcomes = self.rational_outcomes
        
        self.joint_outcomes.sort(key=lambda o: self.ufun(o), reverse=True)
    

    # Helper functions
    def classify_opponent(self, state: SAOState) -> None:
        if len(self.opponent_offers) < 10:
            self.exp = 1
            self.opponent_style = None
        else:
        # Calculate the slope of the opponent's offers         
            slope = (self.opponent_offers[0] - self.opponent_offers[-1]) / state.relative_time

            if slope < 0.015:
                self.opponent_style = "Boulware"
                self.exp = 1.3
            else:
                self.opponent_style = "Conceder"
                self.exp = 0.6
            




# if you want to do a very small test, use the parameter small=True here. Otherwise, you can use the default parameters.
if __name__ == "__main__":
    from .helpers.runner import run_a_tournament

    run_a_tournament(Group4, small=True, debug=True)

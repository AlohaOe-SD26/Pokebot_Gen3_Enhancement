"""Test-side code for the AI player: gates, fault tests and live proof drivers.

Nothing in here runs inside the AI's play loop, and no play-loop file may import from here
(`check_purity.py` rule c). Files here may inspect the game through the framework to GRADE the AI,
which the play loop itself may not do.
"""

"""
apps/risks_core/services.py

Shared service utilities for all Risk subclasses.
Place any business logic that spans multiple risk types here for reuse and modularity.
"""

# Example function to discover available risk types; can be extended as needed.
def get_registered_risk_types():
    """
    Return a list of registered risk subclass URL segments.
    Used in the API layer to dynamically route based on risk class.
    """
    return ['credit-political', 'directors-officers'] 
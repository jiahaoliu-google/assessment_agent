"""
Agent 1: User Profile & Goal Analyzer Agent (ProfileAnalyzerAgent).
Parses biometric inputs and natural language user goals.
"""

import re
from typing import Dict, Any, Tuple, List, Optional
from meal_planner.agents.base_agent import BaseAgent
from meal_planner.models import UserProfile
from meal_planner.tools.registry import ToolRegistry
from meal_planner.utils.ui import BRIGHT_CYAN


class ProfileAnalyzerAgent(BaseAgent):
    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        super().__init__(
            name="ProfileAnalyzerAgent",
            role="Evaluates user physical biometric metrics and extracts structured parameters from natural language goals.",
            tool_registry=tool_registry
        )

    def parse_height(self, raw_height: Any) -> float:
        """Parses height string or numeric into centimeters."""
        if isinstance(raw_height, (int, float)):
            return float(raw_height)

        s = str(raw_height).strip().lower()
        # Feet and inches check e.g. 5'11, 5ft 11in, 6 foot 1 inch
        ft_match = re.search(r'(\d+)\s*(?:ft|\'|feet)\s*(\d+)?\s*(?:in|\"|inches)?', s)
        if ft_match:
            feet = float(ft_match.group(1))
            inches = float(ft_match.group(2)) if ft_match.group(2) else 0.0
            return round((feet * 12 + inches) * 2.54, 1)

        # Meter check e.g. 1.75m or 1.75
        m_match = re.search(r'(\d+\.\d+)\s*m?', s)
        if m_match and float(m_match.group(1)) < 3.0:
            return round(float(m_match.group(1)) * 100, 1)

        # Direct number extraction (assume cm)
        num_match = re.search(r'(\d+(?:\.\d+)?)', s)
        if num_match:
            val = float(num_match.group(1))
            if val < 3.0:  # height in meters
                return round(val * 100, 1)
            return round(val, 1)

        return 175.0  # Reasonable default if parsing fails

    def parse_weight(self, raw_weight: Any) -> float:
        """Parses weight string or numeric into kilograms."""
        if isinstance(raw_weight, (int, float)):
            return float(raw_weight)

        s = str(raw_weight).strip().lower()
        # Lbs check e.g. 160lbs, 160 lbs, 160 pounds
        if "lb" in s or "pound" in s:
            num = re.search(r'(\d+(?:\.\d+)?)', s)
            if num:
                return round(float(num.group(1)) * 0.453592, 1)

        # Kg check or pure number
        num = re.search(r'(\d+(?:\.\d+)?)', s)
        if num:
            val = float(num.group(1))
            if val > 250:  # likely lbs entered without unit
                return round(val * 0.453592, 1)
            return round(val, 1)

        return 70.0  # Reasonable default

    def analyze_goal(self, raw_goal: str) -> Tuple[str, float, List[str], List[str]]:
        """
        Uses NLP heuristic patterns to extract:
        (goal_type, calorie_offset_ratio, preferences, exclusions)
        """
        goal_lower = raw_goal.lower()
        
        goal_type = "maintenance"
        cal_offset = 0.0
        preferences = []
        exclusions = []

        # Goal Classification
        if any(w in goal_lower for w in ["lose", "loss", "cutting", "fat", "slim", "shed", "drop weight"]):
            goal_type = "weight_loss"
            cal_offset = -0.20  # 20% deficit
        elif any(w in goal_lower for w in ["muscle", "gain", "bulk", "hypertrophy", "mass", "build"]):
            goal_type = "muscle_gain"
            cal_offset = +0.15  # 15% surplus
        elif any(w in goal_lower for w in ["keto", "ketogenic"]):
            goal_type = "keto"
            cal_offset = -0.10
        elif any(w in goal_lower for w in ["marathon", "endurance", "triathlon", "stamina", "run"]):
            goal_type = "endurance"
            cal_offset = +0.10
        elif any(w in goal_lower for w in ["recomp", "tone", "lean out"]):
            goal_type = "recomposition"
            cal_offset = -0.05

        # Dietary Exclusions
        exclusion_keywords = {
            "dairy": ["dairy", "lactose", "no milk", "no cheese"],
            "nuts": ["nut", "peanut", "almond", "tree nut"],
            "seafood": ["fish", "seafood", "salmon", "shrimp", "tuna"],
            "gluten": ["gluten", "wheat", "celiac"],
            "pork": ["pork", "bacon", "ham"],
            "eggs": ["egg", "no eggs"],
            "poultry": ["chicken", "turkey"]
        }

        for exc_name, keywords in exclusion_keywords.items():
            if any(k in goal_lower for k in keywords):
                exclusions.append(exc_name)

        # Dietary Preferences
        preference_keywords = {
            "vegetarian": ["vegetarian", "no meat"],
            "vegan": ["vegan", "plant-based", "plant based"],
            "high-protein": ["high protein", "protein", "muscle"],
            "low-carb": ["low carb", "keto", "no carbs"],
            "mediterranean": ["mediterranean", "clean eating"]
        }

        for pref_name, keywords in preference_keywords.items():
            if any(k in goal_lower for k in keywords):
                preferences.append(pref_name)

        # If vegan, automatically exclude dairy, meat, seafood, eggs
        if "vegan" in preferences:
            exclusions.extend(["dairy", "pork", "seafood", "poultry", "eggs"])
            exclusions = list(set(exclusions))

        # If vegetarian, exclude pork, poultry, seafood
        if "vegetarian" in preferences:
            exclusions.extend(["pork", "poultry", "seafood"])
            exclusions = list(set(exclusions))

        return goal_type, cal_offset, preferences, exclusions

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes profile analysis.
        Expects input_data to contain 'height', 'weight', 'raw_goal', and optionally 'age', 'sex', 'activity_level'.
        """
        self.log("Receiving user raw inputs for biometric telemetry evaluation...", color=BRIGHT_CYAN)

        raw_height = input_data.get("height", 175)
        raw_weight = input_data.get("weight", 70)
        raw_goal = input_data.get("goal", "Maintain healthy weight and build lean strength")
        age = int(input_data.get("age", 28))
        sex = str(input_data.get("sex", "male")).lower()
        activity = str(input_data.get("activity_level", "moderate")).lower()

        height_cm = self.parse_height(raw_height)
        weight_kg = self.parse_weight(raw_weight)
        goal_type, cal_offset, preferences, exclusions = self.analyze_goal(raw_goal)

        profile = UserProfile(
            height_cm=height_cm,
            weight_kg=weight_kg,
            age=age,
            sex=sex,
            activity_level=activity,
            raw_goal=raw_goal,
            parsed_goal_type=goal_type,
            caloric_target_offset=cal_offset,
            diet_preferences=preferences,
            dietary_exclusions=exclusions
        )

        self.log(f"Parsed Metrics: Height={profile.height_cm}cm, Weight={profile.weight_kg}kg, BMI={profile.bmi} ({profile.bmi_category})")
        self.log(f"Goal Analysis: Type='{goal_type}', Calorie Offset={cal_offset*100:+.0f}%, Exclusions={exclusions if exclusions else 'None'}")

        # Construct outgoing payload message
        self.send_message(
            recipient="NutritionistAgent",
            message_type="USER_PROFILE_READY",
            payload={"user_profile": profile}
        )

        return {"user_profile": profile}

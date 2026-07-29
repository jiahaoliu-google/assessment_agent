from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class UserProfile:
    """Stores user physical metrics and plain-text goal evaluation."""
    height_cm: float
    weight_kg: float
    age: int = 28
    sex: str = "male"  # 'male', 'female', 'other'
    activity_level: str = "moderate"  # 'sedentary', 'light', 'moderate', 'heavy', 'athlete'
    raw_goal: str = ""
    parsed_goal_type: str = "maintenance"  # 'weight_loss', 'muscle_gain', 'maintenance', 'keto', etc.
    caloric_target_offset: float = 0.0  # Percentage e.g. -0.20 for 20% deficit
    diet_preferences: List[str] = field(default_factory=list)  # e.g., ['high-protein', 'mediterranean']
    dietary_exclusions: List[str] = field(default_factory=list)  # e.g., ['dairy', 'nuts', 'seafood']

    @property
    def bmi(self) -> float:
        """Calculate Body Mass Index (BMI)."""
        height_m = self.height_cm / 100.0
        if height_m <= 0:
            return 0.0
        return round(self.weight_kg / (height_m ** 2), 1)

    @property
    def bmi_category(self) -> str:
        """Classify BMI into standard WHO categories."""
        bmi_val = self.bmi
        if bmi_val < 18.5:
            return "Underweight"
        elif 18.5 <= bmi_val < 25.0:
            return "Normal weight"
        elif 25.0 <= bmi_val < 30.0:
            return "Overweight"
        else:
            return "Obese"


@dataclass
class NutritionTarget:
    """Stores calculated energy and macronutrient goals."""
    bmr: float
    tdee: float
    target_calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    water_liters: float
    meal_macro_distribution: Dict[str, Dict[str, float]] = field(default_factory=dict)
    micronutrient_focus: List[str] = field(default_factory=list)


@dataclass
class Ingredient:
    """Represents a specific ingredient quantity and category."""
    name: str
    amount: float
    unit: str
    category: str = "Pantry"

    def __str__(self) -> str:
        if self.amount == int(self.amount):
            amt_str = str(int(self.amount))
        else:
            amt_str = f"{self.amount:.1f}"
        return f"{amt_str} {self.unit} {self.name}".strip()


@dataclass
class Meal:
    """Represents an individual meal entry."""
    name: str
    meal_type: str  # 'Breakfast', 'Lunch', 'Dinner', 'Snack'
    prep_time_mins: int
    cook_time_mins: int
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    ingredients: List[Ingredient] = field(default_factory=list)
    instructions: List[str] = field(default_factory=list)


@dataclass
class DailyMealPlan:
    """Represents a full day of meals (Breakfast, Lunch, Dinner, Snack)."""
    day_number: int
    day_name: str  # e.g., "Day 1 - Monday"
    meals: List[Meal] = field(default_factory=list)

    @property
    def total_calories(self) -> float:
        return round(sum(m.calories for m in self.meals), 1)

    @property
    def total_protein_g(self) -> float:
        return round(sum(m.protein_g for m in self.meals), 1)

    @property
    def total_carbs_g(self) -> float:
        return round(sum(m.carbs_g for m in self.meals), 1)

    @property
    def total_fat_g(self) -> float:
        return round(sum(m.fat_g for m in self.meals), 1)


@dataclass
class FullMealPlan:
    """Complete 7-day meal plan container."""
    user_profile: UserProfile
    nutrition_target: NutritionTarget
    daily_plans: List[DailyMealPlan] = field(default_factory=list)

    @property
    def average_daily_calories(self) -> float:
        if not self.daily_plans:
            return 0.0
        return round(sum(d.total_calories for d in self.daily_plans) / len(self.daily_plans), 1)

    @property
    def average_daily_protein(self) -> float:
        if not self.daily_plans:
            return 0.0
        return round(sum(d.total_protein_g for d in self.daily_plans) / len(self.daily_plans), 1)

    @property
    def average_daily_carbs(self) -> float:
        if not self.daily_plans:
            return 0.0
        return round(sum(d.total_carbs_g for d in self.daily_plans) / len(self.daily_plans), 1)

    @property
    def average_daily_fat(self) -> float:
        if not self.daily_plans:
            return 0.0
        return round(sum(d.total_fat_g for d in self.daily_plans) / len(self.daily_plans), 1)


@dataclass
class AuditResult:
    """Quality control audit report for the meal plan."""
    score: int  # 0 to 100
    passed: bool
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    macro_variances: Dict[str, float] = field(default_factory=dict)


@dataclass
class GroceryCategory:
    """Categorized shopping list section."""
    category_name: str
    items: List[str] = field(default_factory=list)


@dataclass
class GroceryList:
    """Aggregated shopping list and prep advice."""
    categories: List[GroceryCategory] = field(default_factory=list)
    prep_tips: List[str] = field(default_factory=list)


@dataclass
class AgentMessage:
    """Standardized message format for inter-agent communication."""
    sender: str
    recipient: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

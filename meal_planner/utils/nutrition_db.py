"""
Nutritional Database and Recipe Library Engine.
Provides a comprehensive set of recipes, ingredient items, and macro scaling functions.
"""

from typing import List, Dict, Any, Optional
from meal_planner.models import Meal, Ingredient


RECIPE_DATABASE: List[Dict[str, Any]] = [
    # ---------------- BREAKFAST RECIPES ----------------
    {
        "name": "High-Protein Oatmeal with Berries & Whey",
        "meal_type": "Breakfast",
        "tags": ["high-protein", "standard", "vegetarian", "endurance", "muscle_gain"],
        "prep_time": 5,
        "cook_time": 5,
        "base_calories": 420,
        "base_protein": 32.0,
        "base_carbs": 52.0,
        "base_fat": 8.0,
        "ingredients": [
            {"name": "Rolled Oats", "amount": 60, "unit": "g", "category": "Grains & Complex Carbs"},
            {"name": "Whey Protein Powder (Vanilla)", "amount": 30, "unit": "g", "category": "Proteins"},
            {"name": "Fresh Blueberries", "amount": 75, "unit": "g", "category": "Produce"},
            {"name": "Chia Seeds", "amount": 10, "unit": "g", "category": "Healthy Fats & Seeds"},
            {"name": "Unsweetened Almond Milk", "amount": 250, "unit": "ml", "category": "Dairy Alternatives"}
        ],
        "instructions": [
            "Combine oats and almond milk in a pot or microwave safe bowl.",
            "Heat for 2-3 minutes until soft and creamy.",
            "Stir in whey protein powder and chia seeds.",
            "Top with fresh blueberries and serve warm."
        ]
    },
    {
        "name": "Avocado & Egg White Omelet with Spinach",
        "meal_type": "Breakfast",
        "tags": ["high-protein", "low-carb", "keto", "vegetarian", "dairy-free"],
        "prep_time": 5,
        "cook_time": 8,
        "base_calories": 380,
        "base_protein": 28.0,
        "base_carbs": 12.0,
        "base_fat": 24.0,
        "ingredients": [
            {"name": "Large Eggs (Whole)", "amount": 2, "unit": "pcs", "category": "Proteins"},
            {"name": "Egg Whites", "amount": 100, "unit": "ml", "category": "Proteins"},
            {"name": "Fresh Spinach", "amount": 50, "unit": "g", "category": "Produce"},
            {"name": "Sliced Avocado", "amount": 60, "unit": "g", "category": "Produce"},
            {"name": "Extra Virgin Olive Oil", "amount": 1, "unit": "tsp", "category": "Oils & Condiments"}
        ],
        "instructions": [
            "Whisk whole eggs and egg whites together with pinch of salt and pepper.",
            "Heat olive oil in non-stick skillet, add spinach until wilted.",
            "Pour egg mixture over spinach, cook on medium heat until set.",
            "Fold in fresh sliced avocado and serve immediately."
        ]
    },
    {
        "name": "Greek Yogurt Power Bowl with Honey & Nuts",
        "meal_type": "Breakfast",
        "tags": ["high-protein", "standard", "vegetarian", "muscle_gain"],
        "prep_time": 5,
        "cook_time": 0,
        "base_calories": 410,
        "base_protein": 34.0,
        "base_carbs": 38.0,
        "base_fat": 12.0,
        "ingredients": [
            {"name": "Plain Non-Fat Greek Yogurt", "amount": 250, "unit": "g", "category": "Dairy & Alternatives"},
            {"name": "Sliced Almonds", "amount": 20, "unit": "g", "category": "Healthy Fats & Seeds"},
            {"name": "Banana", "amount": 1, "unit": "medium", "category": "Produce"},
            {"name": "Raw Honey", "amount": 1, "unit": "tbsp", "category": "Pantry Staples"},
            {"name": "Flaxseed Meal", "amount": 10, "unit": "g", "category": "Healthy Fats & Seeds"}
        ],
        "instructions": [
            "Scoop Greek yogurt into a serving bowl.",
            "Slice banana into rounds and place on top.",
            "Sprinkle with almonds and flaxseed meal.",
            "Drizzle with raw honey."
        ]
    },
    {
        "name": "Keto Bacon, Egg & Cheddar Scramble",
        "meal_type": "Breakfast",
        "tags": ["keto", "low-carb", "high-fat"],
        "prep_time": 5,
        "cook_time": 7,
        "base_calories": 490,
        "base_protein": 30.0,
        "base_carbs": 3.0,
        "base_fat": 39.0,
        "ingredients": [
            {"name": "Large Eggs", "amount": 3, "unit": "pcs", "category": "Proteins"},
            {"name": "Center-Cut Bacon", "amount": 2, "unit": "slices", "category": "Proteins"},
            {"name": "Shredded Cheddar Cheese", "amount": 30, "unit": "g", "category": "Dairy & Alternatives"},
            {"name": "Butter", "amount": 1, "unit": "tbsp", "category": "Oils & Condiments"}
        ],
        "instructions": [
            "Crisp bacon in pan, remove and chop.",
            "Melt butter in pan, whisk eggs and scramble softly.",
            "Stir in cheddar cheese and bacon until melted."
        ]
    },
    {
        "name": "Vegan Tofu Scramble with Whole Wheat Toast",
        "meal_type": "Breakfast",
        "tags": ["vegan", "vegetarian", "dairy-free", "standard"],
        "prep_time": 10,
        "cook_time": 8,
        "base_calories": 360,
        "base_protein": 24.0,
        "base_carbs": 35.0,
        "base_fat": 14.0,
        "ingredients": [
            {"name": "Firm Tofu (Crumble)", "amount": 180, "unit": "g", "category": "Proteins"},
            {"name": "Bell Pepper & Onion", "amount": 75, "unit": "g", "category": "Produce"},
            {"name": "Whole Wheat Bread", "amount": 2, "unit": "slices", "category": "Grains & Complex Carbs"},
            {"name": "Nutritional Yeast", "amount": 1, "unit": "tbsp", "category": "Spices & Seasonings"},
            {"name": "Olive Oil", "amount": 1, "unit": "tsp", "category": "Oils & Condiments"}
        ],
        "instructions": [
            "Saute peppers and onions in olive oil until soft.",
            "Crumble firm tofu into pan with turmeric and nutritional yeast.",
            "Cook for 5-6 mins until hot. Serve alongside toasted whole wheat bread."
        ]
    },
    {
        "name": "Smoked Salmon & Cream Cheese Rice Cakes",
        "meal_type": "Breakfast",
        "tags": ["high-protein", "pescatarian", "low-carb"],
        "prep_time": 5,
        "cook_time": 0,
        "base_calories": 370,
        "base_protein": 27.0,
        "base_carbs": 24.0,
        "base_fat": 16.0,
        "ingredients": [
            {"name": "Smoked Salmon", "amount": 100, "unit": "g", "category": "Proteins"},
            {"name": "Whole Grain Rice Cakes", "amount": 3, "unit": "pcs", "category": "Grains & Complex Carbs"},
            {"name": "Light Cream Cheese", "amount": 30, "unit": "g", "category": "Dairy & Alternatives"},
            {"name": "Cucumber Slices & Dill", "amount": 50, "unit": "g", "category": "Produce"}
        ],
        "instructions": [
            "Spread cream cheese evenly on rice cakes.",
            "Top with smoked salmon slices.",
            "Garnish with thin cucumber rounds and fresh dill."
        ]
    },

    # ---------------- LUNCH RECIPES ----------------
    {
        "name": "Grilled Chicken Quinoa Harvest Salad",
        "meal_type": "Lunch",
        "tags": ["high-protein", "standard", "dairy-free", "gluten-free", "weight_loss"],
        "prep_time": 10,
        "cook_time": 15,
        "base_calories": 520,
        "base_protein": 44.0,
        "base_carbs": 48.0,
        "base_fat": 14.0,
        "ingredients": [
            {"name": "Chicken Breast (Boneless Skinless)", "amount": 160, "unit": "g", "category": "Proteins"},
            {"name": "Cooked Quinoa", "amount": 150, "unit": "g", "category": "Grains & Complex Carbs"},
            {"name": "Mixed Salad Greens", "amount": 80, "unit": "g", "category": "Produce"},
            {"name": "Cherry Tomatoes", "amount": 60, "unit": "g", "category": "Produce"},
            {"name": "Extra Virgin Olive Oil & Lemon Dressing", "amount": 1, "unit": "tbsp", "category": "Oils & Condiments"}
        ],
        "instructions": [
            "Season chicken breast with herbs, salt, and pepper; grill for 6-7 mins per side.",
            "Slice chicken breast.",
            "Toss mixed greens, cherry tomatoes, and cooked quinoa in olive oil lemon dressing.",
            "Top salad with warm grilled chicken slices."
        ]
    },
    {
        "name": "Keto Turkey & Guacamole Lettuce Wraps",
        "meal_type": "Lunch",
        "tags": ["keto", "low-carb", "high-protein", "dairy-free"],
        "prep_time": 10,
        "cook_time": 5,
        "base_calories": 460,
        "base_protein": 38.0,
        "base_carbs": 10.0,
        "base_fat": 28.0,
        "ingredients": [
            {"name": "Lean Ground Turkey (93/7)", "amount": 170, "unit": "g", "category": "Proteins"},
            {"name": "Fresh Guacamole", "amount": 75, "unit": "g", "category": "Produce"},
            {"name": "Romaine Lettuce Leaves", "amount": 4, "unit": "large leaves", "category": "Produce"},
            {"name": "Pico de Gallo / Salsa", "amount": 40, "unit": "g", "category": "Produce"}
        ],
        "instructions": [
            "Brown ground turkey in pan with taco seasoning.",
            "Spoon cooked turkey into Romaine lettuce cups.",
            "Top with fresh guacamole and pico de gallo."
        ]
    },
    {
        "name": "Mediterranean Tuna & Chickpea Bowl",
        "meal_type": "Lunch",
        "tags": ["high-protein", "pescatarian", "dairy-free", "standard"],
        "prep_time": 10,
        "cook_time": 0,
        "base_calories": 480,
        "base_protein": 42.0,
        "base_carbs": 42.0,
        "base_fat": 15.0,
        "ingredients": [
            {"name": "Canned Albacore Tuna in Water", "amount": 150, "unit": "g", "category": "Proteins"},
            {"name": "Canned Chickpeas (Rinsed)", "amount": 130, "unit": "g", "category": "Grains & Complex Carbs"},
            {"name": "Diced Cucumbers & Red Onion", "amount": 70, "unit": "g", "category": "Produce"},
            {"name": "Kalamata Olives", "amount": 20, "unit": "g", "category": "Pantry Staples"},
            {"name": "Olive Oil & Red Wine Vinegar", "amount": 1, "unit": "tbsp", "category": "Oils & Condiments"}
        ],
        "instructions": [
            "Drain canned tuna and rinsed chickpeas.",
            "Combine tuna, chickpeas, diced cucumber, onion, and Kalamata olives in a bowl.",
            "Drizzle with olive oil and red wine vinegar; toss thoroughly."
        ]
    },
    {
        "name": "Lean Beef Sweet Potato Buddha Bowl",
        "meal_type": "Lunch",
        "tags": ["high-protein", "muscle_gain", "standard", "dairy-free"],
        "prep_time": 10,
        "cook_time": 20,
        "base_calories": 560,
        "base_protein": 45.0,
        "base_carbs": 55.0,
        "base_fat": 16.0,
        "ingredients": [
            {"name": "Lean Ground Beef (90/10)", "amount": 160, "unit": "g", "category": "Proteins"},
            {"name": "Roasted Sweet Potato Cubes", "amount": 180, "unit": "g", "category": "Produce"},
            {"name": "Steamed Broccoli Florets", "amount": 100, "unit": "g", "category": "Produce"},
            {"name": "Tahini Dressing", "amount": 1, "unit": "tbsp", "category": "Oils & Condiments"}
        ],
        "instructions": [
            "Roast sweet potato cubes at 200°C (400°F) for 20 mins.",
            "Pan sear lean ground beef until browned.",
            "Steam broccoli for 4-5 minutes.",
            "Assemble bowl with sweet potatoes, beef, broccoli, and drizzle with tahini."
        ]
    },
    {
        "name": "Lentil & Quinoa Mediterranean Power Bowl",
        "meal_type": "Lunch",
        "tags": ["vegan", "vegetarian", "dairy-free", "high-fiber"],
        "prep_time": 10,
        "cook_time": 15,
        "base_calories": 490,
        "base_protein": 24.0,
        "base_carbs": 68.0,
        "base_fat": 12.0,
        "ingredients": [
            {"name": "Cooked Brown Lentils", "amount": 150, "unit": "g", "category": "Proteins"},
            {"name": "Cooked Quinoa", "amount": 140, "unit": "g", "category": "Grains & Complex Carbs"},
            {"name": "Diced Cucumbers & Tomatoes", "amount": 80, "unit": "g", "category": "Produce"},
            {"name": "Hummus", "amount": 2, "unit": "tbsp", "category": "Pantry Staples"},
            {"name": "Lemon Juice & Olive Oil", "amount": 1, "unit": "tbsp", "category": "Oils & Condiments"}
        ],
        "instructions": [
            "Mix cooked brown lentils and quinoa in bowl.",
            "Add diced fresh vegetables and dollop of hummus.",
            "Dress with lemon juice and olive oil."
        ]
    },

    # ---------------- DINNER RECIPES ----------------
    {
        "name": "Pan-Seared Salmon with Asparagus & Wild Rice",
        "meal_type": "Dinner",
        "tags": ["high-protein", "pescatarian", "dairy-free", "standard", "gluten-free"],
        "prep_time": 10,
        "cook_time": 15,
        "base_calories": 580,
        "base_protein": 42.0,
        "base_carbs": 44.0,
        "base_fat": 24.0,
        "ingredients": [
            {"name": "Atlantic Salmon Fillet", "amount": 170, "unit": "g", "category": "Proteins"},
            {"name": "Cooked Wild Rice Blend", "amount": 150, "unit": "g", "category": "Grains & Complex Carbs"},
            {"name": "Fresh Asparagus Spears", "amount": 120, "unit": "g", "category": "Produce"},
            {"name": "Olive Oil", "amount": 1, "unit": "tbsp", "category": "Oils & Condiments"},
            {"name": "Lemon & Garlic", "amount": 1, "unit": "unit", "category": "Produce"}
        ],
        "instructions": [
            "Sear salmon skin-side down in olive oil for 4 mins, flip and cook 3 mins more.",
            "Saute asparagus spears in garlic and lemon juice until tender-crisp.",
            "Serve salmon and asparagus over hot cooked wild rice."
        ]
    },
    {
        "name": "Grilled Steak with Roasted Vegetables & Herb Butter",
        "meal_type": "Dinner",
        "tags": ["high-protein", "keto", "muscle_gain", "low-carb"],
        "prep_time": 10,
        "cook_time": 15,
        "base_calories": 620,
        "base_protein": 48.0,
        "base_carbs": 14.0,
        "base_fat": 40.0,
        "ingredients": [
            {"name": "Sirloin Steak", "amount": 200, "unit": "g", "category": "Proteins"},
            {"name": "Roasted Zucchini & Bell Peppers", "amount": 150, "unit": "g", "category": "Produce"},
            {"name": "Herb Garlic Butter", "amount": 15, "unit": "g", "category": "Dairy & Alternatives"}
        ],
        "instructions": [
            "Season sirloin steak with coarse salt and black pepper.",
            "Grill or pan-sear steak to desired doneness (medium-rare ~4 mins per side).",
            "Rest steak for 5 minutes, top with herb garlic butter alongside roasted veggies."
        ]
    },
    {
        "name": "Lemon Herb Chicken Breast with Roasted Potatoes & Green Beans",
        "meal_type": "Dinner",
        "tags": ["high-protein", "standard", "dairy-free", "muscle_gain"],
        "prep_time": 10,
        "cook_time": 25,
        "base_calories": 540,
        "base_protein": 46.0,
        "base_carbs": 48.0,
        "base_fat": 15.0,
        "ingredients": [
            {"name": "Chicken Breast", "amount": 180, "unit": "g", "category": "Proteins"},
            {"name": "Roasted Red Potatoes", "amount": 170, "unit": "g", "category": "Produce"},
            {"name": "Fresh Green Beans", "amount": 100, "unit": "g", "category": "Produce"},
            {"name": "Olive Oil", "amount": 1, "unit": "tbsp", "category": "Oils & Condiments"}
        ],
        "instructions": [
            "Toss red potato wedges with olive oil, salt, rosemary and roast at 200°C for 25 mins.",
            "Pan roast lemon herb marinated chicken breast until internal temp reaches 74°C (165°F).",
            "Steam green beans and serve together."
        ]
    },
    {
        "name": "Keto Sesame Pork Stir-Fry with Broccoli & Cauliflower Rice",
        "meal_type": "Dinner",
        "tags": ["keto", "low-carb", "dairy-free", "high-protein"],
        "prep_time": 10,
        "cook_time": 10,
        "base_calories": 510,
        "base_protein": 42.0,
        "base_carbs": 12.0,
        "base_fat": 32.0,
        "ingredients": [
            {"name": "Pork Tenderloin (Strips)", "amount": 170, "unit": "g", "category": "Proteins"},
            {"name": "Cauliflower Rice", "amount": 180, "unit": "g", "category": "Produce"},
            {"name": "Broccoli & Snap Peas", "amount": 100, "unit": "g", "category": "Produce"},
            {"name": "Sesame Oil & Tamari Soy Sauce", "amount": 1, "unit": "tbsp", "category": "Oils & Condiments"}
        ],
        "instructions": [
            "Heat sesame oil in wok over high heat.",
            "Stir-fry pork tenderloin strips until browned.",
            "Add broccoli, snap peas, and cauliflower rice with Tamari; toss until cooked."
        ]
    },
    {
        "name": "Chickpea & Coconut Curry with Jasmine Rice",
        "meal_type": "Dinner",
        "tags": ["vegan", "vegetarian", "dairy-free", "gluten-free"],
        "prep_time": 10,
        "cook_time": 15,
        "base_calories": 530,
        "base_protein": 19.0,
        "base_carbs": 72.0,
        "base_fat": 18.0,
        "ingredients": [
            {"name": "Chickpeas", "amount": 160, "unit": "g", "category": "Proteins"},
            {"name": "Light Coconut Milk", "amount": 120, "unit": "ml", "category": "Pantry Staples"},
            {"name": "Spinach & Diced Tomatoes", "amount": 100, "unit": "g", "category": "Produce"},
            {"name": "Jasmine Rice (Cooked)", "amount": 160, "unit": "g", "category": "Grains & Complex Carbs"},
            {"name": "Yellow Curry Paste", "amount": 1, "unit": "tbsp", "category": "Spices & Seasonings"}
        ],
        "instructions": [
            "Saute curry paste, add coconut milk and chickpeas.",
            "Simmer for 10 minutes until thickened, stir in spinach.",
            "Serve warm over fluffy jasmine rice."
        ]
    },

    # ---------------- SNACK RECIPES ----------------
    {
        "name": "Whey Protein Shake with Peanut Butter & Almond Milk",
        "meal_type": "Snack",
        "tags": ["high-protein", "standard", "vegetarian", "muscle_gain"],
        "prep_time": 3,
        "cook_time": 0,
        "base_calories": 280,
        "base_protein": 30.0,
        "base_carbs": 10.0,
        "base_fat": 12.0,
        "ingredients": [
            {"name": "Whey Protein Powder", "amount": 30, "unit": "g", "category": "Proteins"},
            {"name": "Natural Peanut Butter", "amount": 15, "unit": "g", "category": "Healthy Fats & Seeds"},
            {"name": "Unsweetened Almond Milk", "amount": 300, "unit": "ml", "category": "Dairy Alternatives"}
        ],
        "instructions": [
            "Blend protein powder, almond milk, and peanut butter with ice until smooth."
        ]
    },
    {
        "name": "Cottage Cheese with Pineapple & Walnuts",
        "meal_type": "Snack",
        "tags": ["high-protein", "standard", "vegetarian"],
        "prep_time": 3,
        "cook_time": 0,
        "base_calories": 240,
        "base_protein": 24.0,
        "base_carbs": 18.0,
        "base_fat": 8.0,
        "ingredients": [
            {"name": "Low-Fat Cottage Cheese", "amount": 180, "unit": "g", "category": "Dairy & Alternatives"},
            {"name": "Fresh Pineapple Chunks", "amount": 80, "unit": "g", "category": "Produce"},
            {"name": "Crushed Walnuts", "amount": 10, "unit": "g", "category": "Healthy Fats & Seeds"}
        ],
        "instructions": [
            "Scoop cottage cheese into bowl, top with pineapple chunks and walnuts."
        ]
    },
    {
        "name": "Hard Boiled Eggs & Pumpkin Seeds",
        "meal_type": "Snack",
        "tags": ["keto", "low-carb", "high-protein", "dairy-free"],
        "prep_time": 2,
        "cook_time": 0,
        "base_calories": 220,
        "base_protein": 18.0,
        "base_carbs": 4.0,
        "base_fat": 15.0,
        "ingredients": [
            {"name": "Hard Boiled Eggs", "amount": 2, "unit": "pcs", "category": "Proteins"},
            {"name": "Roasted Pumpkin Seeds", "amount": 15, "unit": "g", "category": "Healthy Fats & Seeds"}
        ],
        "instructions": [
            "Peel eggs, sprinkle with sea salt, and serve with pumpkin seeds."
        ]
    },
    {
        "name": "Apple Slices with Almond Butter",
        "meal_type": "Snack",
        "tags": ["vegan", "vegetarian", "dairy-free", "standard"],
        "prep_time": 3,
        "cook_time": 0,
        "base_calories": 210,
        "base_protein": 4.0,
        "base_carbs": 26.0,
        "base_fat": 11.0,
        "ingredients": [
            {"name": "Medium Apple", "amount": 1, "unit": "pc", "category": "Produce"},
            {"name": "Natural Almond Butter", "amount": 20, "unit": "g", "category": "Healthy Fats & Seeds"}
        ],
        "instructions": [
            "Slice apple into wedges and serve with almond butter dip."
        ]
    },
    {
        "name": "Edamame Beans with Sea Salt",
        "meal_type": "Snack",
        "tags": ["vegan", "vegetarian", "dairy-free", "high-protein", "gluten-free"],
        "prep_time": 2,
        "cook_time": 5,
        "base_calories": 190,
        "base_protein": 17.0,
        "base_carbs": 14.0,
        "base_fat": 7.0,
        "ingredients": [
            {"name": "Steamed Edamame Pods", "amount": 150, "unit": "g", "category": "Proteins"},
            {"name": "Coarse Sea Salt", "amount": 1, "unit": "pinch", "category": "Spices & Seasonings"}
        ],
        "instructions": [
            "Steam edamame pods for 4-5 minutes, toss with sea salt."
        ]
    }
]


def scale_meal(recipe: Dict[str, Any], target_calories: float) -> Meal:
    """Scales a recipe's ingredients and macronutrients to match a target calorie requirement."""
    base_cal = recipe["base_calories"]
    ratio = target_calories / base_cal if base_cal > 0 else 1.0

    scaled_ingredients = []
    for ing in recipe["ingredients"]:
        scaled_amount = round(ing["amount"] * ratio, 1)
        scaled_ingredients.append(
            Ingredient(
                name=ing["name"],
                amount=scaled_amount,
                unit=ing["unit"],
                category=ing.get("category", "Pantry Staples")
            )
        )

    return Meal(
        name=recipe["name"],
        meal_type=recipe["meal_type"],
        prep_time_mins=recipe["prep_time"],
        cook_time_mins=recipe["cook_time"],
        calories=round(base_cal * ratio, 1),
        protein_g=round(recipe["base_protein"] * ratio, 1),
        carbs_g=round(recipe["base_carbs"] * ratio, 1),
        fat_g=round(recipe["base_fat"] * ratio, 1),
        ingredients=scaled_ingredients,
        instructions=recipe["instructions"]
    )


def select_recipes_for_plan(
    meal_type: str,
    goal_type: str,
    dietary_exclusions: List[str],
    count: int = 7
) -> List[Dict[str, Any]]:
    """Selects suitable recipes for a given meal type matching goal and avoiding exclusions."""
    candidates = []

    for r in RECIPE_DATABASE:
        if r["meal_type"] != meal_type:
            continue

        # Check exclusions
        excluded = False
        r_name_lower = r["name"].lower()
        ing_names_lower = [i["name"].lower() for i in r["ingredients"]]

        for exc in dietary_exclusions:
            exc_clean = exc.lower().strip()
            if exc_clean in r_name_lower or any(exc_clean in ing for ing in ing_names_lower):
                excluded = True
                break

        if excluded:
            continue

        # Score matching
        score = 1
        tags = r.get("tags", [])
        if goal_type in tags:
            score += 3
        if "high-protein" in tags and goal_type in ["muscle_gain", "weight_loss"]:
            score += 2
        if "keto" in tags and goal_type == "keto":
            score += 4
        if "vegan" in tags and "vegan" in dietary_exclusions: # handled above
            score += 1

        candidates.append((score, r))

    candidates.sort(key=lambda x: x[0], reverse=True)
    raw_selected = [c[1] for c in candidates]

    if not raw_selected:
        # Fallback to any matching meal_type recipe if strict fit not available
        raw_selected = [r for r in RECIPE_DATABASE if r["meal_type"] == meal_type]

    # Cycle if count > len(raw_selected)
    result = []
    for i in range(count):
        result.append(raw_selected[i % len(raw_selected)])

    return result

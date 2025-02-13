import openai

class RecipeGenerator:
    def __init__(self, api_key):
        openai.api_key = api_key

    def generate_recipe(self, ingredients):
        if not isinstance(ingredients, list):
            ingredients = ingredients.split(',')

        prompt = (
            f"Create a detailed recipe using the following ingredients: {', '.join(ingredients)}.\n\n"
            "The recipe should include the following sections:\n"
            "1. Title: The name of the recipe.\n"
            "2. Ingredients: A list of ingredients.\n"
            "3. Recipe: Step-by-step instructions on how to prepare the dish.\n\n"
            "Format:\n"
            "Title: <Recipe Title>\n\n"
            "Ingredients:\n"
            "- <Ingredient 1>\n"
            "- <Ingredient 2>\n"
            "...\n\n"
            "Recipe:\n"
            "1. <Step 1>\n"
            "2. <Step 2>\n"
            "...\n"
        )

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            n=1,
            stop=None,
            temperature=0.7,
        )

        recipe_text = response['choices'][0]['message']['content'].strip()
        lines = recipe_text.split('\n')

        if 'Recipe:' not in lines:
            raise ValueError("'Recipe:' is not in the response")

        title = lines[0].replace('Title: ', '').strip()
        ingredients_list = lines[2:lines.index('Recipe:')]
        recipe_steps = lines[lines.index('Recipe:') + 1:]

        return title, '\n'.join(ingredients_list), '\n'.join(recipe_steps)
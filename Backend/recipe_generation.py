from transformers import GPT2LMHeadModel, GPT2Tokenizer

class RecipeGenerator:
    def __init__(self, model_name='gpt2'):
        self.tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        self.model = GPT2LMHeadModel.from_pretrained(model_name)

    def generate_recipe(self, ingredients):
        prompt = f"Create a recipe using the following ingredients: {', '.join(ingredients)}"
        inputs = self.tokenizer.encode(prompt, return_tensors='pt')
        outputs = self.model.generate(inputs, max_length=150, num_return_sequences=1)
        recipe = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        recipe_name = f"{ingredients[0].capitalize()} Recipe"
        
        return recipe_name, recipe
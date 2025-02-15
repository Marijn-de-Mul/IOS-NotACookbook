import SwiftUI
import UIKit
import Combine

struct ContentView: View {
    @EnvironmentObject var userManager: UserManager
    @State private var recipes: [Recipe] = []
    @State private var selectedRecipe: Recipe?
    @State private var showImagePicker = false
    @State private var inputImage: UIImage?
    @State private var analyzedIngredients: String?
    @State private var isLoading = false
    @State private var showConfirmation = false

    var body: some View {
        NavigationView {
            if userManager.isAuthenticated {
                List {
                    ForEach(recipes) { recipe in
                        NavigationLink(destination: RecipeDetailView(recipe: recipe)) {
                            HStack {
                                if let imagePath = recipe.imagePath, let url = URL(string: imagePath) {
                                    AsyncImage(url: url) { image in
                                        image.resizable()
                                            .scaledToFill()
                                            .frame(width: 50, height: 50)
                                            .clipShape(Circle())
                                    } placeholder: {
                                        ProgressView()
                                    }
                                }
                                VStack(alignment: .leading) {
                                    Text(recipe.name)
                                        .font(.headline)
                                    Text(recipe.ingredients)
                                        .font(.subheadline)
                                        .foregroundColor(.secondary)
                                        .lineLimit(1)
                                }
                            }
                        }
                    }
                    .onDelete(perform: deleteRecipe)
                }
                .navigationTitle("Recipes")
                .toolbar {
                    ToolbarItem(placement: .navigationBarLeading) {
                        Button(action: {
                            userManager.logout()
                        }) {
                            Text("Logout")
                        }
                    }
                    ToolbarItem(placement: .navigationBarTrailing) {
                        Button(action: {
                            showImagePicker = true
                        }) {
                            Image(systemName: "camera")
                        }
                    }
                }
                .onAppear {
                    fetchRecipes()
                    Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { _ in
                        fetchRecipes()
                    }
                }
                .sheet(isPresented: $showImagePicker, onDismiss: analyzeImage) {
                    ImagePicker(image: $inputImage)
                }
                .overlay {
                    if isLoading {
                        CustomLoadingView()
                    }
                }
                .alert(isPresented: $showConfirmation) {
                    Alert(
                        title: Text("Add Recipe"),
                        message: Text("Ingredients: \(analyzedIngredients ?? "Unknown")"),
                        primaryButton: .default(Text("Add")) {
                            addRecipe()
                        },
                        secondaryButton: .cancel()
                    )
                }
            } else {
                LoginView()
            }
        }
    }

    func fetchRecipes() {
        guard let token = userManager.token else { return }
        NetworkManager.shared.fetchRecipes(token: token) { recipes in
            if let recipes = recipes {
                DispatchQueue.main.async {
                    self.recipes = recipes
                }
            }
        }
    }

    func analyzeImage() {
        guard let inputImage = inputImage, let token = userManager.token else { return }
        isLoading = true
        NetworkManager.shared.analyzeImage(inputImage, token: token) { ingredients in
            DispatchQueue.main.async {
                self.isLoading = false
                self.analyzedIngredients = ingredients
                self.showConfirmation = true
            }
        }
    }

    func addRecipe() {
        guard let ingredients = analyzedIngredients else { return }
        let newRecipe = Recipe(id: recipes.count + 1, name: "New Recipe", ingredients: ingredients, imagePath: nil)
        recipes.append(newRecipe)
        fetchRecipes()
    }

    func deleteRecipe(at offsets: IndexSet) {
        guard let token = userManager.token else { return }
        offsets.forEach { index in
            let recipe = recipes[index]
            NetworkManager.shared.deleteRecipe(id: recipe.id, token: token) { success in
                if success {
                    DispatchQueue.main.async {
                        recipes.remove(at: index)
                    }
                }
            }
        }
    }
}

#Preview {
    ContentView()
}

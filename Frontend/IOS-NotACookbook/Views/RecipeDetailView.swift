import SwiftUI

struct RecipeDetailView: View {
    var recipe: Recipe

    var body: some View {
        ScrollView {
            VStack {
                if let imagePath = recipe.imagePath, let url = URL(string: imagePath) {
                    AsyncImage(url: url) { image in
                        image.resizable()
                            .scaledToFit()
                    } placeholder: {
                        ProgressView()
                    }
                }
                Text(recipe.ingredients)
                    .padding()
            }
        }
        .navigationTitle(recipe.name)
        .navigationBarTitleDisplayMode(.inline)
    }
}

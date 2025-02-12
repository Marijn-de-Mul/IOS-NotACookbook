import SwiftUI
import UIKit

struct ContentView: View {
    @State private var recipes: [Recipe] = []
    @State private var selectedRecipe: Recipe?
    @State private var showImagePicker = false
    @State private var inputImage: UIImage?
    @State private var analyzedIngredients: String?
    @State private var isLoading = false
    @State private var showConfirmation = false

    var body: some View {
        NavigationView {
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
        }
    }

    func fetchRecipes() {
        NetworkManager.shared.fetchRecipes { recipes in
            if let recipes = recipes {
                DispatchQueue.main.async {
                    self.recipes = recipes
                }
            }
        }
    }

    func analyzeImage() {
        guard let inputImage = inputImage else { return }
        isLoading = true
        NetworkManager.shared.analyzeImage(inputImage) { ingredients in
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
        offsets.forEach { index in
            let recipe = recipes[index]
            NetworkManager.shared.deleteRecipe(id: recipe.id) { success in
                if success {
                    DispatchQueue.main.async {
                        recipes.remove(at: index)
                    }
                }
            }
        }
    }
}

struct RecipeDetailView: View {
    var recipe: Recipe

    var body: some View {
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
        .navigationTitle(recipe.name)
    }
}

struct ImagePicker: UIViewControllerRepresentable {
    class Coordinator: NSObject, UINavigationControllerDelegate, UIImagePickerControllerDelegate {
        var parent: ImagePicker

        init(parent: ImagePicker) {
            self.parent = parent
        }

        func imagePickerController(_ picker: UIImagePickerController, didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey : Any]) {
            if let uiImage = info[.originalImage] as? UIImage {
                parent.image = uiImage
            }
            parent.presentationMode.wrappedValue.dismiss()
        }
    }

    @Environment(\.presentationMode) var presentationMode
    @Binding var image: UIImage?

    func makeCoordinator() -> Coordinator {
        Coordinator(parent: self)
    }

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.delegate = context.coordinator
        picker.sourceType = .camera
        return picker
    }

    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}
}

struct Recipe: Identifiable, Codable {
    let id: Int
    let name: String
    let ingredients: String
    let imagePath: String?
}

struct AnalyzeImageResponse: Codable {
    let class_name: String
    let confidence: Double
}

class NetworkManager {
    static let shared = NetworkManager()
    private let baseURL = "http://192.168.178.236:5000"

    func fetchRecipes(completion: @escaping ([Recipe]?) -> Void) {
        let url = URL(string: "\(baseURL)/recipes")!
        URLSession.shared.dataTask(with: url) { data, response, error in
            guard let data = data, error == nil else {
                completion(nil)
                return
            }
            let recipes = try? JSONDecoder().decode([Recipe].self, from: data)
            completion(recipes)
        }.resume()
    }

    func analyzeImage(_ image: UIImage, completion: @escaping (String?) -> Void) {
        let url = URL(string: "\(baseURL)/analyze_image")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        let imageData = image.jpegData(compressionQuality: 0.7)!
        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"image\"; filename=\"image.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        URLSession.shared.dataTask(with: request) { data, response, error in
            guard let data = data, error == nil else {
                completion(nil)
                return
            }
            let result = try? JSONDecoder().decode(AnalyzeImageResponse.self, from: data)
            completion(result?.class_name)
        }.resume()
    }

    func deleteRecipe(id: Int, completion: @escaping (Bool) -> Void) {
        let url = URL(string: "\(baseURL)/recipes/\(id)")!
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"

        URLSession.shared.dataTask(with: request) { data, response, error in
            guard error == nil else {
                completion(false)
                return
            }
            completion(true)
        }.resume()
    }
}

struct CustomLoadingView: View {
    @State private var isAnimating = false

    var body: some View {
        ZStack {
            Color.black.opacity(0.4)
                .edgesIgnoringSafeArea(.all)
            VStack {
                Circle()
                    .trim(from: 0, to: 0.7)
                    .stroke(AngularGradient(gradient: Gradient(colors: [.blue, .purple, .pink, .blue]), center: .center), style: StrokeStyle(lineWidth: 8, lineCap: .round))
                    .frame(width: 100, height: 100)
                    .rotationEffect(Angle(degrees: isAnimating ? 360 : 0))
                    .animation(Animation.linear(duration: 1).repeatForever(autoreverses: false))
                    .onAppear {
                        self.isAnimating = true
                    }
                Text("Analyzing image...")
                    .foregroundColor(.white)
                    .font(.headline)
                    .padding(.top, 20)
            }
        }
    }
}

#Preview {
    ContentView()
}

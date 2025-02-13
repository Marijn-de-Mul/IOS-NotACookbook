import SwiftUI
import UIKit
import Combine

class UserManager: ObservableObject {
    @Published var isAuthenticated = false
    @Published var token: String? {
        didSet {
            if let token = token {
                UserDefaults.standard.set(token, forKey: "authToken")
            } else {
                UserDefaults.standard.removeObject(forKey: "authToken")
            }
        }
    }

    init() {
        self.token = UserDefaults.standard.string(forKey: "authToken")
        self.isAuthenticated = token != nil
    }

    func login(username: String, password: String, completion: @escaping (Bool) -> Void) {
        NetworkManager.shared.login(username: username, password: password) { token in
            DispatchQueue.main.async {
                if let token = token {
                    self.token = token
                    self.isAuthenticated = true
                    completion(true)
                } else {
                    completion(false)
                }
            }
        }
    }

    func register(username: String, password: String, completion: @escaping (Bool) -> Void) {
        NetworkManager.shared.register(username: username, password: password) { success in
            DispatchQueue.main.async {
                completion(success)
            }
        }
    }

    func logout() {
        self.token = nil
        self.isAuthenticated = false
    }
}

class NetworkManager {
    static let shared = NetworkManager()
    private let baseURL = "https://backend.inack.marijndemul.nl"

    func fetchRecipes(token: String, completion: @escaping ([Recipe]?) -> Void) {
        let url = URL(string: "\(baseURL)/recipes")!
        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        URLSession.shared.dataTask(with: request) { data, response, error in
            guard let data = data, error == nil else {
                completion(nil)
                return
            }
            let recipes = try? JSONDecoder().decode([Recipe].self, from: data)
            completion(recipes)
        }.resume()
    }

    func analyzeImage(_ image: UIImage, token: String, completion: @escaping (String?) -> Void) {
        let url = URL(string: "\(baseURL)/analyze_image")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
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

    func deleteRecipe(id: Int, token: String, completion: @escaping (Bool) -> Void) {
        let url = URL(string: "\(baseURL)/recipes/\(id)")!
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

        URLSession.shared.dataTask(with: request) { data, response, error in
            guard error == nil else {
                completion(false)
                return
            }
            completion(true)
        }.resume()
    }

    func login(username: String, password: String, completion: @escaping (String?) -> Void) {
        let url = URL(string: "\(baseURL)/login")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = ["username": username, "password": password]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body, options: [])

        URLSession.shared.dataTask(with: request) { data, response, error in
            guard let data = data, error == nil else {
                completion(nil)
                return
            }
            let result = try? JSONDecoder().decode([String: String].self, from: data)
            completion(result?["access_token"])
        }.resume()
    }

    func register(username: String, password: String, completion: @escaping (Bool) -> Void) {
        let url = URL(string: "\(baseURL)/register")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = ["username": username, "password": password]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body, options: [])

        URLSession.shared.dataTask(with: request) { data, response, error in
            guard let data = data, error == nil else {
                completion(false)
                return
            }
            let result = try? JSONDecoder().decode([String: String].self, from: data)
            completion(result?["message"] == "User registered successfully")
        }.resume()
    }
}

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

struct LoginView: View {
    @EnvironmentObject var userManager: UserManager
    @State private var username = ""
    @State private var password = ""
    @State private var showError = false

    var body: some View {
        VStack {
            TextField("Username", text: $username)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .padding()
            SecureField("Password", text: $password)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .padding()
            Button(action: {
                userManager.login(username: username, password: password) { success in
                    if !success {
                        showError = true
                    }
                }
            }) {
                Text("Login")
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(8)
            }
            .padding()
            .alert(isPresented: $showError) {
                Alert(title: Text("Login Failed"), message: Text("Invalid username or password"), dismissButton: .default(Text("OK")))
            }
            NavigationLink("Register", destination: RegisterView())
                .padding()
        }
        .navigationTitle("Login")
    }
}

struct RegisterView: View {
    @EnvironmentObject var userManager: UserManager
    @State private var username = ""
    @State private var password = ""
    @State private var showError = false
    @State private var showSuccess = false

    var body: some View {
        VStack {
            TextField("Username", text: $username)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .padding()
            SecureField("Password", text: $password)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .padding()
            Button(action: {
                userManager.register(username: username, password: password) { success in
                    if success {
                        showSuccess = true
                    } else {
                        showError = true
                    }
                }
            }) {
                Text("Register")
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(8)
            }
            .padding()
            .alert(isPresented: $showError) {
                Alert(title: Text("Registration Failed"), message: Text("Username already exists"), dismissButton: .default(Text("OK")))
            }
            .alert(isPresented: $showSuccess) {
                Alert(title: Text("Registration Successful"), message: Text("You can now log in"), dismissButton: .default(Text("OK")))
            }
        }
        .navigationTitle("Register")
    }
}

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

@main
struct IOS_NotACookbookApp: App {
    @StateObject private var userManager = UserManager()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(userManager)
        }
    }
}

#Preview {
    ContentView()
}

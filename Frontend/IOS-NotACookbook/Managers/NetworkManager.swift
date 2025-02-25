import Foundation
import UIKit

class NetworkManager {
    static let shared = NetworkManager()
    private let baseURL = "https://backend.inack.marijndemul.nl"

    private init() {}

    func fetchRecipes(token: String, completion: @escaping ([Recipe]?) -> Void) {
        let url = URL(string: "\(baseURL)/recipes")!
        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        performDataTask(with: request, completion: completion)
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

        performDataTask(with: request) { (result: AnalyzeImageResponse?) in
            completion(result?.class_name)
        }
    }

    func deleteRecipe(id: Int, token: String, completion: @escaping (Bool) -> Void) {
        let url = URL(string: "\(baseURL)/recipes/\(id)")!
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

        performDataTask(with: request) { (result: [String: String]?) in
            completion(result != nil)
        }
    }

    func login(username: String, password: String, completion: @escaping (String?) -> Void) {
        let url = URL(string: "\(baseURL)/login")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = ["username": username, "password": password]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body, options: [])

        performDataTask(with: request) { (result: [String: String]?) in
            completion(result?["access_token"])
        }
    }

    func register(username: String, password: String, completion: @escaping (Bool) -> Void) {
        let url = URL(string: "\(baseURL)/register")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = ["username": username, "password": password]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body, options: [])

        performDataTask(with: request) { (result: [String: String]?) in
            completion(result?["message"] == "User registered successfully")
        }
    }

    private func performDataTask<T: Decodable>(with request: URLRequest, completion: @escaping (T?) -> Void) {
        URLSession.shared.dataTask(with: request) { data, response, error in
            guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                UserManager.shared.logout()
                completion(nil)
                return
            }
            guard let data = data, error == nil else {
                completion(nil)
                return
            }
            let result = try? JSONDecoder().decode(T.self, from: data)
            completion(result)
        }.resume()
    }
}

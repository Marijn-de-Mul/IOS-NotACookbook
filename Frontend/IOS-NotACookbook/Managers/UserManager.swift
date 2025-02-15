import Foundation

class UserManager: ObservableObject {
    static let shared = UserManager()
    
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

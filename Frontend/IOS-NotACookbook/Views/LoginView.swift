import SwiftUI

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

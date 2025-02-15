import SwiftUI

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

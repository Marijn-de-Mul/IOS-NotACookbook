import Foundation
import SwiftUI

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

import SwiftUI

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
                    .onAppear {
                        withAnimation(Animation.linear(duration: 1).repeatForever(autoreverses: false)) {
                            self.isAnimating = true
                        }
                    }
                Text("Analyzing image...")
                    .foregroundColor(.white)
                    .font(.headline)
                    .padding(.top, 20)
            }
        }
    }
}

import Foundation

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

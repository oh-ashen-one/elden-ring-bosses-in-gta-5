import SwiftUI
import AppKit

struct Component: Decodable, Identifiable {
    let id: String
    let title: String
    let path: String?
    let ready: Bool
    let detail: String
}
struct SetupReport: Decodable {
    let platform: String
    let mw2_ready: Bool
    let crossover_mission_ready: Bool
    let components: [Component]
}
final class SetupModel: ObservableObject {
    @Published var report: SetupReport?
    @Published var message = "Checking your game folders…"
    @Published var working = false
    @Published var running = false
    var gameProcess: Process?
    var tool: URL { Bundle.main.resourceURL!.appendingPathComponent("mw2ai") }
    var runtime: URL { Bundle.main.resourceURL!.appendingPathComponent("runtime/iw4l") }
    var dataDirectory: URL {
        if let override = ProcessInfo.processInfo.environment["MW2AI_HOME"] { return URL(fileURLWithPath: override) }
        return FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Application Support/Modern Warfare 2 AI")
    }
    func call(_ arguments: [String]) {
        guard !working else { return }
        working = true
        let executable = tool
        DispatchQueue.global(qos: .userInitiated).async {
            let process = Process()
            let output = Pipe()
            process.executableURL = executable
            process.arguments = arguments
            process.standardOutput = output
            process.standardError = output
            do {
                try process.run()
                let data = output.fileHandleForReading.readDataToEndOfFile()
                process.waitUntilExit()
                let decoded = process.terminationStatus == 0 ? try? JSONDecoder().decode(SetupReport.self, from: data) : nil
                let text = String(data: data, encoding: .utf8) ?? "The setup check returned no text."
                DispatchQueue.main.async {
                    self.working = false
                    if let decoded = decoded {
                        self.report = decoded
                        self.message = decoded.mw2_ready
                            ? "MW2 files found. You can try the base Terminal runtime."
                            : "Connect your MW2 game files to unlock Terminal."
                    } else { self.message = text }
                }
            } catch {
                DispatchQueue.main.async { self.working = false; self.message = error.localizedDescription }
            }
        }
    }
    func select(_ component: Component) {
        let panel = NSOpenPanel()
        panel.title = component.title
        panel.message = "Choose your local game-data folder. The original files stay read-only."
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        if panel.runModal() == .OK, let path = panel.url?.path {
            call(["configure", "--" + component.id, path])
        }
    }
    func launch() {
        guard report?.mw2_ready == true, !running else { return }
        do {
            try FileManager.default.createDirectory(at: dataDirectory, withIntermediateDirectories: true)
            let log = dataDirectory.appendingPathComponent("launcher.log")
            FileManager.default.createFile(atPath: log.path, contents: nil)
            let file = try FileHandle(forWritingTo: log)
            let process = Process()
            process.executableURL = tool
            process.arguments = ["launch", "--runtime", runtime.path, "--map", "mp_terminal"]
            process.standardOutput = file
            process.standardError = file
            process.terminationHandler = { finished in
                try? file.close()
                DispatchQueue.main.async {
                    self.running = false
                    self.gameProcess = nil
                    self.message = finished.terminationStatus == 0
                        ? "The game has closed." : "The runtime stopped. Open the data folder to inspect launcher.log."
                }
            }
            try process.run()
            gameProcess = process
            running = true
            message = "The base runtime is starting. The crossover mission is still in development."
        } catch { message = error.localizedDescription }
    }
}

@main struct ModernWarfareAI: App {
    @StateObject private var model = SetupModel()
    var body: some Scene {
        WindowGroup {
            VStack(alignment: .leading, spacing: 18) {
                HStack(alignment: .top, spacing: 20) {
                    Image(systemName: "airplane.circle.fill")
                        .font(.system(size: 55)).foregroundStyle(.mint)
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Terminal, remixed.").font(.system(size: 32, weight: .bold))
                        Text("MODERN WARFARE 2 AI  ·  MAC PROTOTYPE")
                            .font(.system(size: 11, weight: .semibold, design: .monospaced)).foregroundStyle(.secondary)
                    }
                    Spacer()
                    Text("SETUP PREVIEW").font(.system(size: 10, weight: .bold, design: .monospaced))
                        .padding(8).background(.mint.opacity(0.14), in: Capsule())
                }
                Text("Connect your game files. The original installations stay read-only.")
                    .foregroundStyle(.secondary)
                ScrollView {
                    VStack(spacing: 10) {
                        if let report = model.report {
                            ForEach(report.components) { component in
                                HStack(alignment: .top, spacing: 12) {
                                    Image(systemName: component.ready ? "checkmark.circle.fill" : "folder.badge.plus")
                                        .foregroundStyle(component.ready ? .green : .secondary).font(.title3)
                                    VStack(alignment: .leading, spacing: 5) {
                                        Text(component.title).fontWeight(.semibold)
                                        Text(component.detail).font(.system(size: 12)).foregroundStyle(.secondary)
                                            .fixedSize(horizontal: false, vertical: true)
                                        if let path = component.path {
                                            Text(path).font(.system(size: 10, design: .monospaced))
                                                .foregroundStyle(.secondary).lineLimit(1).truncationMode(.middle)
                                        }
                                    }
                                    Spacer(minLength: 8)
                                    Button(component.path == nil ? "Choose folder" : "Change") { model.select(component) }
                                        .disabled(model.working || model.running)
                                }
                                .padding(14).frame(maxWidth: .infinity, alignment: .leading)
                                .background(Color.primary.opacity(0.045), in: RoundedRectangle(cornerRadius: 12))
                            }
                        }
                    }.padding(.trailing, 4)
                }
                VStack(alignment: .leading, spacing: 7) {
                    Label("The four-game mission is in development.", systemImage: "hammer")
                        .font(.system(size: 12, weight: .semibold))
                    Text("This preview includes the Mac runtime and setup. The builder, dragon and ten-minute mission are not playable yet. No game data is bundled or downloaded automatically.")
                        .font(.system(size: 11)).foregroundStyle(.secondary)
                }.padding(12).frame(maxWidth: .infinity, alignment: .leading)
                    .background(.orange.opacity(0.08), in: RoundedRectangle(cornerRadius: 10))
                Text(model.message).font(.system(size: 12)).foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading).lineLimit(3)
                HStack {
                    Button("Check setup") { model.call(["doctor", "--json"]) }.disabled(model.working)
                    Button("Data folder") {
                        try? FileManager.default.createDirectory(at: model.dataDirectory, withIntermediateDirectories: true)
                        NSWorkspace.shared.open(model.dataDirectory)
                    }
                    Link("Source & guide", destination: URL(string: "https://github.com/oh-ashen-one/modern-warfare-2-ai/blob/v0.1.0-mac-setup/docs/MAC-SETUP.md")!)
                    Spacer()
                    Button(model.running ? "Runtime running" : "Launch Terminal") { model.launch() }
                        .buttonStyle(.borderedProminent).tint(.mint)
                        .disabled(model.report?.mw2_ready != true || model.working || model.running)
                }
            }
            .padding(26).frame(minWidth: 720, idealWidth: 800, maxWidth: 1000, minHeight: 710, idealHeight: 780)
            .preferredColorScheme(.dark)
            .task { model.call(["doctor", "--json"]) }
        }.windowStyle(.titleBar).defaultSize(width: 800, height: 780)
    }
}

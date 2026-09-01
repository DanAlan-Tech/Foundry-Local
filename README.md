# Microsoft Foundry Local

> Run optimized small language models (SLMs) and generative AI entirely on-device with zero cloud dependencies, zero network latency, and no per-token costs.

[![License: MIT](https://shields.io)](https://opensource.org)
[![Platform Support](https://shields.io)](https://github.com/microsoft/foundry-local)

## 🧠 What is Foundry Local?

**Microsoft Foundry Local** is a cross-platform local AI runtime and SDK designed for production-grade applications. Unlike general-purpose experimentation tools or basic local web daemons, Foundry Local integrates directly into your application process. It handles hardware abstraction automatically—seamlessly targeting your CPU, dedicated GPU, or NPU via optimized runtimes like ONNX Runtime and WinML.

## ✨ Key Features

* **In-Process Inference:** Executes directly inside your application footprint without external service dependencies.
* **Automatic Hardware Acceleration:** Dynamically routes execution to the best available hardware (CPU, GPU, NPU, Apple Silicon Metal).
* **OpenAI-Compatible APIs:** Standard endpoints allow integration with existing SDKs and frameworks.
* **Portable Architecture:** Share code seamlessly between local on-device models and the cloud-based [Microsoft Foundry](https://foundrylocal.ai/).
* **Multi-Language Support:** First-party SDKs for Python, JavaScript/TypeScript, C#, and Rust.

---

## 🚀 Quick Start

### 1. Install the CLI Tool (Development Preview)
* **Windows (via winget):**
  ```bash
  winget install Microsoft.FoundryLocal
  ```
* **macOS (via Homebrew):**
  ```bash
  brew tap microsoft/foundrylocal && brew install foundrylocal
  ```

### 2. Download and Run a Model
```bash
foundry service start
foundry model download qwen2.5-0.5b
foundry run qwen2.5-0.5b
```

### 3. Use the SDK in Your Code (JavaScript Example)
```javascript
import { FoundryLocalManager } from "foundry-local-sdk";

const mgr = FoundryLocalManager.create({ appName: "my-local-ai-app" });
const model = await mgr.catalog.getModel("qwen2.5-0.5b");
await model.download();
await model.load();

const chatClient = model.createChatClient();
const response = await chatClient.completeChat([{ role: "user", content: "Hello local AI!" }]);
console.log(response);
```

---

## 📂 Project Structure & Ecosystem

* **[microsoft/foundry-local](https://github.com/microsoft/foundry-local):** Core CLI and development repository.
* **[foundry-samples](https://github.com/microsoft-foundry/foundry-samples):** Official implementation examples for C#, Python, and JS.
* **[Microsoft Foundry Toolkit](https://github.com/microsoft/foundry-toolkit):** VS Code extension for discovering and testing local models alongside agents and GitHub Copilot.

## 📄 License

Distributed under the MIT License. See [LICENSE](https://github.com) for more details.


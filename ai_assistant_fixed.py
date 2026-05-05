#!/usr/bin/env python3
"""
Complete Automated AI Assistant with Caching Support - Updated Working Version
Uses public model from second-state repository
"""

import sys
import os
import platform
import subprocess
import json
import time
from pathlib import Path

class SystemChecker:
    """সিস্টেম কনফিগারেশন চেক করার জন্য ক্লাস"""
    
    def __init__(self):
        self.system_info = {}
        self.requirements_met = True
        
    def check_all(self):
        """সব সিস্টেম প্যারামিটার চেক করা"""
        print("=" * 60)
        print("🔍 SYSTEM CONFIGURATION CHECK")
        print("=" * 60)
        
        self.check_os()
        self.check_cpu()
        self.check_ram()
        self.check_storage()
        self.check_python()
        self.check_gpu()
        
        return self.requirements_met
    
    def check_os(self):
        os_name = platform.system()
        print(f"\n📌 Operating System: {os_name} {platform.release()}")
        self.system_info['os'] = os_name.lower()
        
    def check_cpu(self):
        cpu_count = os.cpu_count()
        print(f"📌 CPU Cores: {cpu_count}")
        if cpu_count and cpu_count >= 4:
            print("✅ CPU: Sufficient (4+ cores)")
        else:
            print("⚠️ CPU: May be slow (less than 4 cores)")
        self.system_info['cpu_cores'] = cpu_count
        
    def check_ram(self):
        try:
            import psutil
            ram = psutil.virtual_memory()
            ram_gb = ram.total / (1024**3)
            print(f"📌 Total RAM: {ram_gb:.1f} GB")
            
            if ram_gb >= 8:
                print("✅ RAM: Sufficient (8+ GB)")
            elif ram_gb >= 4:
                print("⚠️ RAM: Minimum (4-8 GB) - May be slow")
            else:
                print("❌ RAM: Insufficient (need 8+ GB)")
                self.requirements_met = False
                
            self.system_info['ram_gb'] = ram_gb
            
        except ImportError:
            print("⚠️ psutil not installed - installing now...")
            self.install_psutil()
            self.check_ram()
            
    def install_psutil(self):
        """psutil ইনস্টল করা"""
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil", "-q"])
            print("✅ psutil installed")
        except:
            print("⚠️ Could not install psutil")
            
    def check_storage(self):
        try:
            import psutil
            disk = psutil.disk_usage(os.getcwd())
            free_gb = disk.free / (1024**3)
            print(f"📌 Free Storage (current drive): {free_gb:.1f} GB")
            
            if free_gb >= 10:
                print("✅ Storage: Sufficient")
            elif free_gb >= 5:
                print("⚠️ Storage: Minimum")
            else:
                print("❌ Storage: Insufficient")
                self.requirements_met = False
                
            self.system_info['free_storage_gb'] = free_gb
            
        except ImportError:
            pass
            
    def check_python(self):
        python_version = sys.version_info
        print(f"📌 Python Version: {python_version.major}.{python_version.minor}")
        
        if python_version.major >= 3 and python_version.minor >= 8:
            print("✅ Python: Sufficient")
        else:
            print("❌ Python: Need 3.8+")
            self.requirements_met = False
            
    def check_gpu(self):
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ NVIDIA GPU: Detected")
                self.system_info['gpu'] = 'nvidia'
                return
        except:
            pass
        
        print("ℹ️ No dedicated GPU detected - Will use CPU (slower but works)")
        self.system_info['gpu'] = 'none'
        
    def save_report(self):
        """সিস্টেম রিপোর্ট সেভ করা"""
        try:
            desktop = Path.home() / "Desktop"
            if desktop.exists():
                report_file = desktop / f"system_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
            else:
                report_file = Path(f"system_report_{time.strftime('%Y%m%d_%H%M%S')}.json")
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.system_info, f, indent=2)
            print(f"\n📄 System report saved: {report_file}")
            return str(report_file)
        except PermissionError:
            try:
                report_file = f"system_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(self.system_info, f, indent=2)
                print(f"\n📄 System report saved: {report_file}")
                return report_file
            except:
                print("\n⚠️ Could not save system report (permission issue)")
                return None


class AICache:
    """ফাইল ক্যাশিং ম্যানেজ করার জন্য ক্লাস"""
    
    def __init__(self):
        self.cache_dir = Path(os.getcwd()) / "ai_cache"
        self.models_dir = self.cache_dir / "models"
        
        try:
            self.models_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            self.cache_dir = Path.home() / "Desktop" / "ai_cache"
            self.models_dir = self.cache_dir / "models"
            self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_index_file = self.cache_dir / "cache_index.json"
        self.cache_index = self.load_cache_index()
        
    def load_cache_index(self):
        if self.cache_index_file.exists():
            try:
                with open(self.cache_index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_cache_index(self):
        try:
            with open(self.cache_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f, indent=2)
        except:
            pass
    
    def is_model_cached(self, model_name):
        if model_name in self.cache_index:
            model_path = Path(self.cache_index[model_name])
            if model_path.exists():
                return True, model_path
        return False, None
    
    def cache_model(self, model_name, model_path):
        self.cache_index[model_name] = str(model_path)
        self.save_cache_index()
        print(f"✅ Model cached: {model_name}")
    
    def get_cached_models(self):
        models = []
        for name, path in self.cache_index.items():
            if Path(path).exists():
                models.append((name, path))
        return models
    
    def list_cached_files(self):
        print("\n" + "=" * 60)
        print("📦 CACHED FILES")
        print("=" * 60)
        print(f"Cache location: {self.cache_dir}")
        print("-" * 60)
        
        if not self.cache_index:
            print("No cached files found")
            return
        
        for name, path in self.cache_index.items():
            file_path = Path(path)
            if file_path.exists():
                size_mb = file_path.stat().st_size / (1024**2)
                print(f"✅ {name}: {size_mb:.1f} MB")
            else:
                print(f"⚠️ {name}: File missing (cached reference exists)")


class AISetup:
    """AI মডেল সেটআপ এবং রান করার জন্য ক্লাস"""
    
    def __init__(self):
        self.cache = AICache()
        self.model_path = None
        
    def check_existing_installation(self):
        print("\n" + "=" * 60)
        print("🔍 CHECKING FOR EXISTING INSTALLATION")
        print("=" * 60)
        
        cached_models = self.cache.get_cached_models()
        
        if cached_models:
            print(f"\n✅ Found {len(cached_models)} cached model(s):")
            for i, (name, path) in enumerate(cached_models, 1):
                try:
                    size_mb = Path(path).stat().st_size / (1024**2)
                    print(f"   {i}. {name} ({size_mb:.1f} MB)")
                except:
                    print(f"   {i}. {name}")
            
            print("\nDo you want to use an existing model?")
            print("1. Yes, use existing model")
            print("2. No, download a new model")
            choice = input("\nEnter choice (1/2): ").strip()
            
            if choice == "1":
                print("\nSelect model to use:")
                for i, (name, _) in enumerate(cached_models, 1):
                    print(f"{i}. {name}")
                
                model_choice = input(f"Enter choice (1-{len(cached_models)}): ").strip()
                try:
                    idx = int(model_choice) - 1
                    if 0 <= idx < len(cached_models):
                        self.model_path = cached_models[idx][1]
                        print(f"✅ Using cached model: {cached_models[idx][0]}")
                        return True
                except:
                    pass
            
            print("⚠️ Invalid choice. Will download new model if needed.")
        
        return False
    
    def install_dependencies(self):
        print("\n" + "=" * 60)
        print("📦 CHECKING DEPENDENCIES")
        print("=" * 60)
        
        packages = ['llama-cpp-python', 'huggingface-hub', 'psutil', 'requests']
        missing = []
        
        for package in packages:
            package_name = package.replace('-', '_')
            try:
                if package == 'llama-cpp-python':
                    __import__('llama_cpp')
                else:
                    __import__(package_name)
                print(f"✅ {package} already installed")
            except ImportError:
                missing.append(package)
                print(f"❌ {package} not installed")
        
        if missing:
            print(f"\n📦 Installing missing packages: {', '.join(missing)}")
            for package in missing:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--user", "-q"])
                    print(f"✅ {package} installed")
                except Exception as e:
                    print(f"❌ Failed to install {package}: {e}")
                    return False
        
        return True
    
    def download_model_if_needed(self):
        """মডেল ডাউনলোড করা - updated with working public repository"""
        
        if self.model_path:
            print(f"\n✅ Using existing model: {self.model_path}")
            return self.model_path
        
        print("\n" + "=" * 60)
        print("📥 MODEL DOWNLOAD (Only if not cached)")
        print("=" * 60)
        
        # Updated model configuration with working public repository
        models_config = [
            {
                "name": "tinyllama-1.1b-chat-q4_k_m",
                "repo": "second-state/TinyLlama-1.1B-Chat-v1.0-GGUF",
                "file": "tinyllama-1.1b-chat-v1.0-q4_k_m.gguf",
                "size": "~700 MB",
                "ram_required": 2,
                "direct_url": "https://huggingface.co/second-state/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0-q4_k_m.gguf"
            },
            {
                "name": "phi-2-q4_k_m",
                "repo": "TheBloke/phi-2-GGUF",
                "file": "phi-2.Q4_K_M.gguf",
                "size": "~800 MB",
                "ram_required": 3,
                "direct_url": "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf"
            }
        ]
        
        # Check if any model is already cached
        for model in models_config:
            cached, cached_path = self.cache.is_model_cached(model["name"])
            if cached:
                print(f"✅ {model['name']} already cached!")
                return cached_path
        
        # Show model selection menu
        print("\n🌟 Available models:")
        for i, model in enumerate(models_config, 1):
            print(f"  {i}. {model['name']} ({model['size']})")
        
        print("\n0. Cancel and manually download later")
        
        choice = input(f"\nSelect model to download (1-{len(models_config)}): ").strip()
        
        if choice == "0":
            return None
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(models_config):
                selected = models_config[idx]
                
                print(f"\n📥 Downloading {selected['name']} ({selected['size']})...")
                print("This may take 5-10 minutes depending on your internet speed...")
                print("Please wait, this will only happen once...")
                
                # Try with wget/curl first (more reliable)
                import urllib.request
                import ssl
                
                # Create a custom SSL context (bypasses some certificate issues)
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                target_path = self.cache.models_dir / selected["file"]
                
                if target_path.exists():
                    print(f"✅ File already exists: {target_path}")
                    self.cache.cache_model(selected["name"], str(target_path))
                    return str(target_path)
                
                print(f"Downloading from: {selected['direct_url']}")
                print(f"Saving to: {target_path}")
                
                # Download with progress reporting
                def report_progress(block_num, block_size, total_size):
                    downloaded = block_num * block_size
                    percent = min(100, int(downloaded * 100 / total_size)) if total_size > 0 else 0
                    if total_size > 0:
                        mb_downloaded = downloaded / (1024**2)
                        mb_total = total_size / (1024**2)
                        print(f"\rProgress: {percent}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end="", flush=True)
                
                # Download the file
                opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context))
                urllib.request.install_opener(opener)
                
                urllib.request.urlretrieve(
                    selected["direct_url"],
                    str(target_path),
                    reporthook=report_progress
                )
                print("\n✅ Download complete!")
                
                # Verify file size
                if target_path.exists() and target_path.stat().st_size > 100_000_000:  # At least 100MB
                    self.cache.cache_model(selected["name"], str(target_path))
                    return str(target_path)
                else:
                    print("❌ Downloaded file appears to be corrupted or incomplete")
                    target_path.unlink(missing_ok=True)
                    return None
                    
            else:
                print("❌ Invalid selection")
                return None
                
        except Exception as e:
            print(f"\n❌ Download failed: {e}")
            print("\n💡 Manual download option:")
            for model in models_config:
                print(f"  • {model['name']}: {model['direct_url']}")
            print(f"\nPlace downloaded file in: {self.cache.models_dir}/")
            return None
    
    def run_assistant(self, model_path):
        """AI অ্যাসিস্ট্যান্ট রান করা"""
        print("\n" + "=" * 60)
        print("🤖 STARTING AI ASSISTANT")
        print("=" * 60)
        
        try:
            from llama_cpp import Llama
            
            print("\n🔄 Loading model into memory (this may take 10-30 seconds)...")
            print("⏳ First response may take longer, please be patient...")
            
            llm = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_threads=os.cpu_count(),
                n_gpu_layers=0,
                verbose=False
            )
            
            print("\n" + "=" * 60)
            print("✅ AI Assistant ready!")
            print("=" * 60)
            print("Commands:")
            print("  /exit - Exit the assistant")
            print("  /clear - Clear conversation history")
            print("  /cache - Show cached files")
            print("=" * 60)
            print("\n💡 Tip: Type your question in English or Bengali")
            print("=" * 60)
            
            # Conversation history for context
            conversation_history = []
            
            while True:
                try:
                    user_input = input("\n🙋 You: ").strip()
                    
                    if not user_input:
                        continue
                    
                    if user_input.lower() in ['/exit', '/quit', 'exit', 'quit']:
                        print("\n👋 Goodbye! Have a great day!")
                        break
                    elif user_input.lower() == '/clear':
                        conversation_history = []
                        print("✅ Conversation history cleared")
                        continue
                    elif user_input.lower() == '/cache':
                        self.cache.list_cached_files()
                        continue
                    
                    # Add context from conversation history
                    context = ""
                    if conversation_history:
                        recent = conversation_history[-4:]  # Last 2 exchanges
                        context = "\n".join(recent) + "\n"
                    
                    full_prompt = f"{context}User: {user_input}\nAssistant: "
                    
                    print("🤖 Assistant: ", end="", flush=True)
                    
                    response = llm(
                        full_prompt,
                        max_tokens=256,
                        temperature=0.7,
                        top_p=0.95,
                        repeat_penalty=1.1,
                        stop=["User:", "\n\n", "</s>"],
                        echo=False
                    )
                    
                    answer = response['choices'][0]['text'].strip()
                    print(answer)
                    
                    # Store in history
                    conversation_history.append(f"User: {user_input}")
                    conversation_history.append(f"Assistant: {answer}")
                    
                    # Keep history manageable
                    if len(conversation_history) > 20:
                        conversation_history = conversation_history[-20:]
                    
                except KeyboardInterrupt:
                    print("\n\n👋 Goodbye!")
                    break
                    
        except ImportError:
            print("❌ llama_cpp module not found")
            print("Please run: pip install llama-cpp-python --user")
        except Exception as e:
            print(f"❌ Error: {e}")
            print("\nTroubleshooting tips:")
            print("1. Make sure the model file is not corrupted")
            print("2. Try running: pip install --upgrade llama-cpp-python")
            print("3. Check if you have enough RAM (at least 4GB free)")


def main():
    print("\n" + "=" * 60)
    print("🤖 AI ASSISTANT - CACHED VERSION (UPDATED)")
    print("=" * 60)
    print("\n✨ Features:")
    print("   • Downloads files only ONCE")
    print("   • Reuses cached models")
    print("   • Works offline after first run")
    print("   • Optimized for your system (7.9 GB RAM)")
    print("   • Uses public, verified models")
    print("=" * 60)
    
    # System check
    checker = SystemChecker()
    checker.check_all()
    checker.save_report()
    
    # AI Setup
    setup = AISetup()
    
    # Dependencies check
    if not setup.install_dependencies():
        print("❌ Failed to setup dependencies")
        input("\nPress Enter to exit...")
        return
    
    # Check existing installation
    setup.check_existing_installation()
    
    # Download or use cached model
    model_path = setup.download_model_if_needed()
    if not model_path:
        print("\n❌ No model available")
        print("\nPlease manually download one of these models:")
        print("1. https://huggingface.co/second-state/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0-q4_k_m.gguf")
        print("2. https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf")
        print(f"\nPlace the downloaded file in: {setup.cache.models_dir}/")
        print("\nThen run this script again.")
        input("\nPress Enter to exit...")
        return
    
    # Run the assistant
    setup.run_assistant(model_path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        input("\nPress Enter to exit...")
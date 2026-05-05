#!/usr/bin/env python3
"""
Complete Automated AI Assistant with Caching Support
Downloads files only once, then reuses them
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
            print("⚠️ psutil not installed")
            
    def check_storage(self):
        try:
            import psutil
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024**3)
            print(f"📌 Free Storage: {free_gb:.1f} GB")
            
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
        
        print("ℹ️ No dedicated GPU detected - Will use CPU")
        self.system_info['gpu'] = 'none'
        
    def save_report(self):
        report_file = f"system_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.system_info, f, indent=2)
        print(f"\n📄 System report saved: {report_file}")
        return report_file


class AICache:
    """ফাইল ক্যাশিং ম্যানেজ করার জন্য ক্লাস"""
    
    def __init__(self):
        self.cache_dir = Path("./ai_cache")
        self.models_dir = self.cache_dir / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # ক্যাশে ফাইল ট্র্যাক করার জন্য
        self.cache_index_file = self.cache_dir / "cache_index.json"
        self.cache_index = self.load_cache_index()
        
    def load_cache_index(self):
        """ক্যাশে ইনডেক্স লোড করা"""
        if self.cache_index_file.exists():
            with open(self.cache_index_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_cache_index(self):
        """ক্যাশে ইনডেক্স সেভ করা"""
        with open(self.cache_index_file, 'w') as f:
            json.dump(self.cache_index, f, indent=2)
    
    def is_model_cached(self, model_name):
        """মডেল আগে ডাউনলোড করা আছে কিনা চেক"""
        if model_name in self.cache_index:
            model_path = Path(self.cache_index[model_name])
            if model_path.exists():
                return True, model_path
        return False, None
    
    def cache_model(self, model_name, model_path):
        """মডেল ক্যাশে রেজিস্টার করা"""
        self.cache_index[model_name] = str(model_path)
        self.save_cache_index()
        print(f"✅ Model cached: {model_name}")
    
    def get_cached_models(self):
        """ক্যাশে থাকা সব মডেলের তালিকা"""
        models = []
        for name, path in self.cache_index.items():
            if Path(path).exists():
                models.append((name, path))
        return models
    
    def list_cached_files(self):
        """ক্যাশে থাকা ফাইল দেখানো"""
        print("\n" + "=" * 60)
        print("📦 CACHED FILES")
        print("=" * 60)
        
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
        """পূর্বের ইনস্টলেশন চেক করা"""
        print("\n" + "=" * 60)
        print("🔍 CHECKING FOR EXISTING INSTALLATION")
        print("=" * 60)
        
        # চেক করা আগে থেকে কোন মডেল ডাউনলোড করা আছে কিনা
        cached_models = self.cache.get_cached_models()
        
        if cached_models:
            print(f"\n✅ Found {len(cached_models)} cached model(s):")
            for i, (name, path) in enumerate(cached_models, 1):
                size_mb = Path(path).stat().st_size / (1024**2)
                print(f"   {i}. {name} ({size_mb:.1f} MB)")
            
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
        """প্রয়োজনীয় প্যাকেজ চেক এবং ইনস্টল"""
        print("\n" + "=" * 60)
        print("📦 CHECKING DEPENDENCIES")
        print("=" * 60)
        
        # চেক করা প্যাকেজগুলো আগে থেকে ইনস্টল আছে কিনা
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
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])
                    print(f"✅ {package} installed")
                except Exception as e:
                    print(f"❌ Failed to install {package}: {e}")
                    return False
        
        return True
    
    def download_model_if_needed(self):
        """মডেল ডাউনলোড করা (যদি প্রয়োজন হয়)"""
        
        # আগে থেকে ডাউনলোড করা আছে কিনা চেক
        if self.model_path:
            print(f"\n✅ Using existing model: {self.model_path}")
            return self.model_path
        
        print("\n" + "=" * 60)
        print("📥 MODEL DOWNLOAD (Only if not cached)")
        print("=" * 60)
        
        # বিভিন্ন মডেলের কনফিগারেশন
        models_config = [
            {
                "name": "qwen2.5-3b-instruct-q4_k_m",
                "repo": "Qwen/Qwen2.5-3B-Instruct-GGUF",
                "file": "qwen2.5-3b-instruct-q4_k_m.gguf",
                "size": "~2.5 GB",
                "ram_required": 4
            },
            {
                "name": "qwen2-1.5b-instruct-q4_k_m",
                "repo": "Qwen/Qwen2-1.5B-Instruct-GGUF",
                "file": "qwen2-1_5b-instruct-q4_k_m.gguf",
                "size": "~1.2 GB",
                "ram_required": 3
            },
            {
                "name": "tinyllama-1.1b-q4_k_m",
                "repo": "TheBloke/TinyLlama-1.1B-GGUF",
                "file": "tinyllama-1.1b-q4_k_m.gguf",
                "size": "~700 MB",
                "ram_required": 2
            }
        ]
        
        # সিস্টেমের RAM অনুযায়ী মডেল সুপারিশ
        recommended_models = []
        for model in models_config:
            if self.cache.is_model_cached(model["name"])[0]:
                print(f"✅ {model['name']} already cached!")
                return self.cache.is_model_cached(model["name"])[1]
        
        print("\nSelect model to download (or use cached):")
        for i, model in enumerate(models_config, 1):
            cached, _ = self.cache.is_model_cached(model["name"])
            status = "✅ CACHED" if cached else f"📥 Need download ({model['size']})"
            print(f"{i}. {model['name']} - {status}")
        
        print("\n0. Cancel")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == "0":
            return None
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(models_config):
                selected_model = models_config[idx]
                
                # চেক করা আগে থেকে ক্যাশে আছে কিনা
                cached, cached_path = self.cache.is_model_cached(selected_model["name"])
                if cached:
                    print(f"✅ Using cached model: {selected_model['name']}")
                    return cached_path
                
                # ডাউনলোড করা
                print(f"\n📥 Downloading {selected_model['name']} ({selected_model['size']})...")
                print("This will take a few minutes...")
                
                from huggingface_hub import hf_hub_download
                
                model_path = hf_hub_download(
                    repo_id=selected_model["repo"],
                    filename=selected_model["file"],
                    resume=True,
                    local_dir=str(self.cache.models_dir)
                )
                
                # ক্যাশে রেজিস্টার
                self.cache.cache_model(selected_model["name"], model_path)
                
                return model_path
                
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
        
        return None
    
    def run_assistant(self, model_path):
        """AI অ্যাসিস্ট্যান্ট রান করা"""
        print("\n" + "=" * 60)
        print("🤖 STARTING AI ASSISTANT")
        print("=" * 60)
        
        try:
            from llama_cpp import Llama
            
            # GPU সেটআপ
            n_gpu_layers = 0
            if platform.system() == "Windows":
                try:
                    subprocess.run(['nvidia-smi'], capture_output=True, check=True)
                    n_gpu_layers = -1
                    print("✅ GPU acceleration: ENABLED")
                except:
                    print("ℹ️ GPU acceleration: DISABLED (CPU mode)")
            
            print("\n🔄 Loading model into memory...")
            llm = Llama(
                model_path=model_path,
                n_ctx=4096,
                n_threads=os.cpu_count(),
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )
            
            print("\n✅ AI Assistant ready!")
            print("=" * 60)
            print("Commands:")
            print("  /exit - Exit")
            print("  /clear - Clear history")
            print("  /cache - Show cached files")
            print("=" * 60)
            
            # চ্যাট লুপ
            conversation_history = []
            
            while True:
                try:
                    user_input = input("\n🙋 You: ").strip()
                    
                    if not user_input:
                        continue
                    
                    if user_input.lower() in ['/exit', '/quit']:
                        print("\n👋 Goodbye!")
                        break
                    elif user_input.lower() == '/clear':
                        conversation_history = []
                        print("✅ History cleared")
                        continue
                    elif user_input.lower() == '/cache':
                        self.cache.list_cached_files()
                        continue
                    
                    # মেসেজ ফরম্যাট
                    messages = [{"role": "user", "content": user_input}]
                    
                    print("🤖 Assistant: ", end="", flush=True)
                    
                    response = llm.create_chat_completion(
                        messages=messages,
                        max_tokens=512,
                        temperature=0.7,
                        top_p=0.95,
                        stop=["</s>", "<|im_end|>"]
                    )
                    
                    answer = response['choices'][0]['message']['content']
                    print(answer)
                    
                    conversation_history.append({"role": "user", "content": user_input})
                    conversation_history.append({"role": "assistant", "content": answer})
                    
                except KeyboardInterrupt:
                    print("\n\n👋 Goodbye!")
                    break
                    
        except ImportError:
            print("❌ llama_cpp module not found")
            print("Please run: pip install llama-cpp-python")
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    print("\n" + "=" * 60)
    print("🤖 AI ASSISTANT - CACHED VERSION")
    print("=" * 60)
    print("\n✨ Features:")
    print("   • Downloads files only ONCE")
    print("   • Reuses cached models")
    print("   • Works offline after first run")
    print("=" * 60)
    
    # সিস্টেম চেক
    checker = SystemChecker()
    if not checker.check_all():
        print("\n⚠️ System check warnings detected")
        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            return
    
    checker.save_report()
    
    # AI সেটআপ
    setup = AISetup()
    
    # ডিপেন্ডেন্সি চেক
    if not setup.install_dependencies():
        print("❌ Failed to setup dependencies")
        return
    
    # পূর্বের ইনস্টলেশন চেক
    if setup.check_existing_installation():
        print("✅ Using existing installation")
    
    # মডেল ডাউনলোড (যদি প্রয়োজন হয়)
    model_path = setup.download_model_if_needed()
    if not model_path:
        print("❌ No model available")
        print("Please check your internet connection and try again")
        return
    
    # অ্যাসিস্ট্যান্ট রান
    setup.run_assistant(model_path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Run: pip install llama-cpp-python huggingface-hub psutil")
        print("2. Check internet connection")
        input("\nPress Enter to exit...")
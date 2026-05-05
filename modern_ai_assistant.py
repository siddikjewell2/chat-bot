#!/usr/bin/env python3
"""
Modern AI Assistant - Working Model (404 Error Fixed)
রান করতে শুধু টাইপ করুন: python ai_assistant_fixed.py
"""

import sys
import os
import threading
import time
import json
from pathlib import Path

# Tkinter (Python এর সাথে built-in আসে)
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# AI imports
try:
    import llama_cpp
except ImportError:
    import subprocess
    print("📦 Installing llama-cpp-python...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "llama-cpp-python", "--quiet"])
    import llama_cpp

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "--quiet"])
    import requests

try:
    import psutil
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil", "--quiet"])
    import psutil

# ==================== Configuration ====================

# নিশ্চিতভাবে কাজ করে এমন মডেল লিংক (Direct Download)
MODELS = {
    "TinyLlama-1.1B (Fast ~700MB)": {
        "url": "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "filename": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "size": "~700 MB",
        "ram": "2-3 GB"
    },
    "Phi-2 (Smart ~800MB)": {
        "url": "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf",
        "filename": "phi-2.Q4_K_M.gguf", 
        "size": "~800 MB",
        "ram": "3-4 GB"
    },
    "Gemma-2B (Google ~1.5GB)": {
        "url": "https://huggingface.co/TheBloke/gemma-2b-it-GGUF/resolve/main/gemma-2b-it-q4_k_m.gguf",
        "filename": "gemma-2b-it-q4_k_m.gguf",
        "size": "~1.5 GB",
        "ram": "4-5 GB"
    }
}

# ==================== Main Application ====================

class ModernAIAssistant:
    def __init__(self):
        self.model = None
        self.model_path = None
        self.is_downloading = False
        self.is_loading = False
        self.current_model = "TinyLlama-1.1B (Fast ~700MB)"
        
        # Setup cache directory
        self.cache_dir = Path(os.getcwd()) / "ai_cache"
        self.models_dir = self.cache_dir / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Create GUI
        self.create_gui()
        
        # Check for existing models
        self.check_existing_models()
        
        # Start RAM monitor
        self.update_ram_info()
        
    def create_gui(self):
        """Create main window"""
        self.root = tk.Tk()
        self.root.title("🤖 Modern AI Assistant")
        self.root.geometry("950x750")
        self.root.configure(bg='#1a1a2e')
        
        # Header
        self.create_header()
        
        # Chat area
        self.create_chat_area()
        
        # Input panel
        self.create_input_panel()
        
        # Welcome message
        self.add_welcome_message()
        
    def create_header(self):
        """Create header frame"""
        header = tk.Frame(self.root, bg='#0f3460', height=70)
        header.pack(fill=tk.X, padx=10, pady=(10,5))
        header.pack_propagate(False)
        
        title = tk.Label(header, text="🤖 MODERN AI ASSISTANT", 
                         font=('Segoe UI', 18, 'bold'),
                         fg='white', bg='#0f3460')
        title.pack(side=tk.LEFT, padx=20, pady=15)
        
        self.status_label = tk.Label(header, text="● No Model Loaded",
                                     font=('Segoe UI', 11),
                                     fg='#FF6B6B', bg='#0f3460')
        self.status_label.pack(side=tk.RIGHT, padx=20, pady=15)
        
    def create_chat_area(self):
        """Create chat display area"""
        # Main frame
        chat_frame = tk.Frame(self.root, bg='#1a1a2e')
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Canvas for custom scrolling
        self.canvas = tk.Canvas(chat_frame, bg='#1a1a2e', highlightthickness=0)
        scrollbar = tk.Scrollbar(chat_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg='#1a1a2e')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mouse wheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self.message_frames = []
        
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def create_input_panel(self):
        """Create input area"""
        input_frame = tk.Frame(self.root, bg='#16213e')
        input_frame.pack(fill=tk.X, padx=10, pady=(5,10))
        
        # Controls row
        controls = tk.Frame(input_frame, bg='#16213e')
        controls.pack(fill=tk.X, padx=10, pady=(10,5))
        
        # Model selection
        tk.Label(controls, text="🧠 Model:", fg='#CCCCCC', bg='#16213e',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        
        self.model_var = tk.StringVar(value=self.current_model)
        model_menu = ttk.Combobox(controls, textvariable=self.model_var,
                                   values=list(MODELS.keys()),
                                   state="readonly", width=30)
        model_menu.pack(side=tk.LEFT, padx=5)
        model_menu.bind('<<ComboboxSelected>>', self.on_model_change)
        
        # Temperature
        tk.Label(controls, text="🌡️ Temp:", fg='#CCCCCC', bg='#16213e',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(20,5))
        
        self.temp_var = tk.DoubleVar(value=0.7)
        temp_scale = tk.Scale(controls, from_=0.0, to=1.0, resolution=0.05,
                              orient=tk.HORIZONTAL, variable=self.temp_var,
                              length=120, bg='#16213e', fg='#CCCCCC',
                              highlightthickness=0)
        temp_scale.pack(side=tk.LEFT, padx=5)
        temp_scale.configure(command=self.update_temp_label)
        
        self.temp_label = tk.Label(controls, text="0.70", fg='#CCCCCC',
                                   bg='#16213e', font=('Segoe UI', 10))
        self.temp_label.pack(side=tk.LEFT, padx=5)
        
        # RAM info
        tk.Label(controls, text="💾 RAM:", fg='#CCCCCC', bg='#16213e',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(20,5))
        
        self.ram_label = tk.Label(controls, text="0/0 GB", fg='#CCCCCC',
                                  bg='#16213e', font=('Segoe UI', 10))
        self.ram_label.pack(side=tk.LEFT, padx=5)
        
        # Input area
        tk.Label(input_frame, text="💬 Your Message:", fg='#CCCCCC',
                bg='#16213e', font=('Segoe UI', 10)).pack(anchor=tk.W, padx=15, pady=(10,0))
        
        self.input_text = scrolledtext.ScrolledText(input_frame, height=4,
                                                     bg='#2d2d44', fg='white',
                                                     insertbackground='white',
                                                     font=('Segoe UI', 11),
                                                     relief=tk.FLAT, wrap=tk.WORD)
        self.input_text.pack(fill=tk.X, padx=15, pady=5)
        self.input_text.bind('<Control-Return>', lambda e: self.send_message())
        
        # Buttons
        buttons = tk.Frame(input_frame, bg='#16213e')
        buttons.pack(fill=tk.X, padx=15, pady=(0,15))
        
        self.send_btn = tk.Button(buttons, text="🚀 Send Message",
                                  command=self.send_message,
                                  bg='#1a53a0', fg='white',
                                  font=('Segoe UI', 11, 'bold'),
                                  relief=tk.FLAT, padx=20, pady=8,
                                  state=tk.DISABLED)
        self.send_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = tk.Button(buttons, text="🗑️ Clear Chat",
                                   command=self.clear_chat,
                                   bg='#1a53a0', fg='white',
                                   font=('Segoe UI', 11, 'bold'),
                                   relief=tk.FLAT, padx=20, pady=8)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.download_btn = tk.Button(buttons, text="📥 Download Model",
                                      command=self.download_model,
                                      bg='#1a53a0', fg='white',
                                      font=('Segoe UI', 11, 'bold'),
                                      relief=tk.FLAT, padx=20, pady=8)
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(buttons, variable=self.progress_var,
                                             length=250, mode='determinate')
        
    def update_temp_label(self, value):
        self.temp_label.config(text=f"{float(value):.2f}")
        
    def on_model_change(self, event=None):
        self.current_model = self.model_var.get()
        self.add_system_message(f"Selected model: {self.current_model}")
        
    def add_message(self, sender, message, msg_type):
        """Add message to chat"""
        msg_frame = tk.Frame(self.scrollable_frame, bg='#1a1a2e')
        msg_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Sender
        icon = "🙋" if msg_type == "user" else "🤖" if msg_type == "assistant" else "ℹ️"
        color = "#AAAAAA"
        sender_label = tk.Label(msg_frame, text=f"{icon} {sender}",
                                fg=color, bg='#1a1a2e',
                                font=('Segoe UI', 9, 'bold'))
        sender_label.pack(anchor=tk.W if msg_type != "user" else tk.E, padx=5)
        
        # Message bubble
        if msg_type == "user":
            bg_color = "#0f3460"
            anchor = tk.E
        elif msg_type == "assistant":
            bg_color = "#2d2d44"
            anchor = tk.W
        else:
            bg_color = "#363656"
            anchor = tk.W
        
        msg_label = tk.Label(msg_frame, text=message,
                             fg='white', bg=bg_color,
                             font=('Segoe UI', 11),
                             wraplength=550, justify=tk.LEFT,
                             padx=12, pady=8)
        msg_label.pack(anchor=anchor, padx=5)
        
        self.message_frames.append(msg_frame)
        self.canvas.yview_moveto(1.0)
        
    def add_system_message(self, message):
        self.add_message("System", message, "system")
        
    def add_welcome_message(self):
        welcome = """🌟 Welcome to Modern AI Assistant!

✨ **Working Models Available:**
• TinyLlama-1.1B (Fastest, ~700MB)
• Phi-2 (Smart, ~800MB)  
• Gemma-2B (Google, ~1.5GB)

🚀 **Quick Start:**
1. Select a model from the dropdown
2. Click "Download Model"
3. Wait for download (5-10 minutes)
4. Start chatting!

💡 **Note:** Model downloads only once. After that, it works offline."""
        
        self.add_message("Assistant", welcome, "assistant")
        
    def check_existing_models(self):
        """Check for already downloaded models"""
        found = False
        for model_name, info in MODELS.items():
            model_path = self.models_dir / info["filename"]
            if model_path.exists():
                found = True
                self.model_path = str(model_path)
                self.current_model = model_name
                self.model_var.set(model_name)
                self.load_model()
                break
        
        if not found:
            self.add_system_message("No model found. Please download a model to start.")
        
    def download_model(self):
        """Download selected model"""
        if self.is_downloading:
            return
            
        model_name = self.model_var.get()
        info = MODELS[model_name]
        target_path = self.models_dir / info["filename"]
        
        # Check if already exists
        if target_path.exists():
            result = messagebox.askyesno("Model Exists",
                                        f"Model already downloaded!\n\nDo you want to load it?")
            if result:
                self.model_path = str(target_path)
                self.load_model()
            return
        
        # Confirm download
        result = messagebox.askyesno("Download Model",
                                     f"📥 Download {model_name}\n\n"
                                     f"Size: {info['size']}\n"
                                     f"RAM needed: {info['ram']}\n\n"
                                     f"Estimated time: 5-10 minutes\n\n"
                                     f"Continue?")
        
        if not result:
            return
        
        # Start download
        self.is_downloading = True
        self.download_btn.config(text="Downloading...", state=tk.DISABLED)
        self.progress_bar.pack(side=tk.RIGHT, padx=10)
        self.progress_var.set(0)
        
        thread = threading.Thread(target=self._download_thread, args=(info, target_path))
        thread.daemon = True
        thread.start()
        
    def _download_thread(self, info, target_path):
        """Download model in background"""
        try:
            import urllib.request
            import ssl
            
            def report(block, size, total):
                if total > 0:
                    percent = int(block * size * 100 / total)
                    self.progress_var.set(min(percent, 100))
                    self.root.update_idletasks()
            
            self.add_system_message(f"📥 Downloading {info['filename']}... Please wait...")
            
            # Configure SSL
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # Headers to avoid 403 error
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
            urllib.request.install_opener(opener)
            
            # Download with SSL context
            urllib.request.urlretrieve(info["url"], str(target_path), reporthook=report)
            
            self.progress_bar.pack_forget()
            self.add_system_message("✅ Download complete! Loading model...")
            
            self.model_path = str(target_path)
            self.load_model()
            
        except Exception as e:
            self.progress_bar.pack_forget()
            error_msg = str(e)
            self.add_system_message(f"❌ Download failed: {error_msg[:150]}")
            messagebox.showerror("Download Failed", 
                               f"Failed to download model.\n\nError: {error_msg[:200]}\n\n"
                               f"Please check your internet connection and try again.")
            
        finally:
            self.is_downloading = False
            self.download_btn.config(text="📥 Download Model", state=tk.NORMAL)
            
    def load_model(self):
        """Load AI model"""
        if self.is_loading:
            return
            
        self.is_loading = True
        self.add_system_message("🔄 Loading model into memory (20-30 seconds)...")
        
        def load():
            try:
                self.model = llama_cpp.Llama(
                    model_path=self.model_path,
                    n_ctx=1024,
                    n_threads=4,
                    n_gpu_layers=0,
                    verbose=False
                )
                
                self.status_label.config(text="● Model Ready", fg="#4CAF50")
                self.send_btn.config(state=tk.NORMAL)
                self.download_btn.config(text="✅ Model Loaded", state=tk.DISABLED)
                self.add_system_message("✅ Model ready! You can now start chatting.")
                
            except Exception as e:
                error_msg = str(e)
                self.add_system_message(f"❌ Failed to load model: {error_msg[:150]}")
                messagebox.showerror("Load Failed", 
                                   f"Failed to load model.\n\nError: {error_msg[:200]}\n\n"
                                   f"Try downloading a different model.")
                
            finally:
                self.is_loading = False
                
        threading.Thread(target=load, daemon=True).start()
        
    def send_message(self):
        """Send message to AI"""
        if not self.model:
            messagebox.showwarning("Model Not Loaded",
                                  "Please download and load a model first!\n\n"
                                  "1. Select a model from dropdown\n"
                                  "2. Click 'Download Model'\n"
                                  "3. Wait for loading to complete")
            return
            
        user_input = self.input_text.get("1.0", tk.END).strip()
        if not user_input:
            return
            
        self.add_message("You", user_input, "user")
        self.input_text.delete("1.0", tk.END)
        
        self.send_btn.config(text="Thinking...", state=tk.DISABLED)
        
        def process():
            try:
                temp = self.temp_var.get()
                
                response = self.model(
                    user_input,
                    max_tokens=256,
                    temperature=temp,
                    top_p=0.95,
                    repeat_penalty=1.1,
                    stop=["User:", "\n\n", "</s>"]
                )
                
                answer = response['choices'][0]['text'].strip()
                if not answer:
                    answer = "I'm not sure how to respond to that. Could you please rephrase?"
                    
                self.add_message("Assistant", answer, "assistant")
                
            except Exception as e:
                self.add_system_message(f"Error: {str(e)[:100]}")
                
            finally:
                self.send_btn.config(text="🚀 Send Message", state=tk.NORMAL)
                
        threading.Thread(target=process, daemon=True).start()
        
    def clear_chat(self):
        """Clear all messages"""
        result = messagebox.askyesno("Clear Chat", "Clear all messages?")
        if result:
            for frame in self.message_frames:
                frame.destroy()
            self.message_frames.clear()
            self.add_welcome_message()
            
    def update_ram_info(self):
        """Update RAM display"""
        try:
            ram = psutil.virtual_memory()
            used = (ram.total - ram.available) / (1024**3)
            total = ram.total / (1024**3)
            self.ram_label.config(text=f"{used:.1f}/{total:.1f} GB")
        except:
            pass
            
        self.root.after(2000, self.update_ram_info)
        
    def run(self):
        self.root.mainloop()


# ==================== Main ====================

if __name__ == "__main__":
    app = ModernAIAssistant()
    app.run()
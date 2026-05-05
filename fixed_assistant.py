#!/usr/bin/env python3
"""
Modern AI Assistant - COMPLETELY FIXED VERSION
প্রপার চ্যাট ফরম্যাট এবং সঠিক রেসপন্স
"""

import sys
import os
import threading
from pathlib import Path

# Tkinter
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# AI Libraries
try:
    import llama_cpp
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "llama-cpp-python", "--quiet"])
    import llama_cpp

try:
    import psutil
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil", "--quiet"])
    import psutil

# ==================== WORKING MODELS ====================

MODELS = {
    "TinyLlama-1.1B (Fast ~700MB)": {
        "url": "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "filename": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "size": "~700 MB"
    }
}

# ==================== MAIN CLASS ====================

class FixedAIAssistant:
    def __init__(self):
        self.model = None
        self.model_path = None
        self.is_downloading = False
        
        # Cache directory
        self.cache_dir = Path(os.getcwd()) / "ai_cache"
        self.models_dir = self.cache_dir / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Create GUI
        self.create_gui()
        
        # Check for existing model
        self.check_existing_model()
        
    def create_gui(self):
        self.root = tk.Tk()
        self.root.title("🤖 RootTOP Assistant - Fixed Version")
        self.root.geometry("900x650")
        self.root.configure(bg='#1a1a2e')
        
        # Header
        header = tk.Frame(self.root, bg='#0f3460', height=60)
        header.pack(fill=tk.X, padx=10, pady=(10,5))
        header.pack_propagate(False)
        
        title = tk.Label(header, text="🤖 AI ASSISTANT", 
                         font=('Segoe UI', 16, 'bold'),
                         fg='white', bg='#0f3460')
        title.pack(side=tk.LEFT, padx=20)
        
        self.status = tk.Label(header, text="● No Model", fg='#FF6B6B', bg='#0f3460')
        self.status.pack(side=tk.RIGHT, padx=20)
        
        # Chat area
        self.setup_chat_area()
        
        # Input panel
        self.setup_input_panel()
        
        # Welcome message
        self.add_message("Assistant", "Hello! I'm your AI assistant. Please download a model using the button below to start chatting.", "assistant")
        
    def setup_chat_area(self):
        """Setup chat display"""
        chat_frame = tk.Frame(self.root, bg='#1a1a2e')
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(chat_frame, bg='#1a1a2e', highlightthickness=0)
        scrollbar = tk.Scrollbar(chat_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg='#1a1a2e')
        
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        self.messages = []
        
    def setup_input_panel(self):
        """Setup input area"""
        input_frame = tk.Frame(self.root, bg='#16213e')
        input_frame.pack(fill=tk.X, padx=10, pady=(5,10))
        
        # Controls
        controls = tk.Frame(input_frame, bg='#16213e')
        controls.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(controls, text="Model:", fg='white', bg='#16213e').pack(side=tk.LEFT, padx=5)
        
        self.model_var = tk.StringVar(value="TinyLlama-1.1B (Fast ~700MB)")
        model_menu = ttk.Combobox(controls, textvariable=self.model_var,
                                   values=list(MODELS.keys()),
                                   state="readonly", width=30)
        model_menu.pack(side=tk.LEFT, padx=5)
        
        tk.Label(controls, text="Temperature:", fg='white', bg='#16213e').pack(side=tk.LEFT, padx=(20,5))
        
        self.temp_var = tk.DoubleVar(value=0.7)
        temp_scale = tk.Scale(controls, from_=0.0, to=1.0, resolution=0.05,
                              orient=tk.HORIZONTAL, variable=self.temp_var,
                              length=100, bg='#16213e', fg='white',
                              highlightthickness=0)
        temp_scale.pack(side=tk.LEFT, padx=5)
        
        # Input text
        tk.Label(input_frame, text="Your message:", fg='white', bg='#16213e').pack(anchor=tk.W, padx=15)
        
        self.input_text = scrolledtext.ScrolledText(input_frame, height=3,
                                                     bg='#2d2d44', fg='white',
                                                     insertbackground='white',
                                                     font=('Segoe UI', 11),
                                                     relief=tk.FLAT)
        self.input_text.pack(fill=tk.X, padx=15, pady=5)
        self.input_text.bind('<Control-Return>', lambda e: self.send_message())
        
        # Buttons
        buttons = tk.Frame(input_frame, bg='#16213e')
        buttons.pack(fill=tk.X, padx=15, pady=10)
        
        self.send_btn = tk.Button(buttons, text="Send", command=self.send_message,
                                   bg='#1a53a0', fg='white', font=('Segoe UI', 11, 'bold'),
                                   relief=tk.FLAT, padx=20, pady=5, state=tk.DISABLED)
        self.send_btn.pack(side=tk.LEFT, padx=5)
        
        self.download_btn = tk.Button(buttons, text="Download Model", command=self.download_model,
                                       bg='#1a53a0', fg='white', font=('Segoe UI', 11, 'bold'),
                                       relief=tk.FLAT, padx=20, pady=5)
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = tk.Button(buttons, text="Clear Chat", command=self.clear_chat,
                                    bg='#1a53a0', fg='white', font=('Segoe UI', 11, 'bold'),
                                    relief=tk.FLAT, padx=20, pady=5)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.progress = ttk.Progressbar(buttons, length=200, mode='determinate')
        
    def add_message(self, sender, message, msg_type):
        """Add message to chat"""
        frame = tk.Frame(self.scroll_frame, bg='#1a1a2e')
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Sender
        icon = "🙋" if msg_type == "user" else "🤖"
        name = tk.Label(frame, text=f"{icon} {sender}", fg='#AAAAAA', bg='#1a1a2e', font=('Segoe UI', 9))
        name.pack(anchor=tk.W if msg_type == "assistant" else tk.E)
        
        # Message bubble
        bg_color = "#0f3460" if msg_type == "user" else "#2d2d44"
        anchor = tk.E if msg_type == "user" else tk.W
        
        text_widget = tk.Text(frame, bg=bg_color, fg='white', font=('Segoe UI', 11),
                               wrap=tk.WORD, height=1, relief=tk.FLAT, padx=10, pady=8)
        text_widget.insert('1.0', message)
        text_widget.configure(state=tk.DISABLED)
        text_widget.pack(anchor=anchor, padx=5, pady=2, fill=tk.X)
        
        # Auto-resize height
        lines = message.count('\n') + 1
        text_widget.configure(height=min(lines + 1, 15))
        
        self.messages.append(frame)
        self.canvas.yview_moveto(1.0)
        
    def check_existing_model(self):
        """Check if model already exists"""
        for info in MODELS.values():
            path = self.models_dir / info["filename"]
            if path.exists():
                self.model_path = str(path)
                self.load_model()
                return True
        return False
        
    def download_model(self):
        """Download model"""
        if self.is_downloading:
            return
            
        model_name = self.model_var.get()
        info = MODELS[model_name]
        target = self.models_dir / info["filename"]
        
        if target.exists():
            reply = messagebox.askyesno("Model Exists", "Model already downloaded. Load it?")
            if reply:
                self.model_path = str(target)
                self.load_model()
            return
        
        reply = messagebox.askyesno("Download", f"Download {model_name} ({info['size']})?\nThis takes 5-10 minutes.")
        if not reply:
            return
            
        self.is_downloading = True
        self.download_btn.config(text="Downloading...", state=tk.DISABLED)
        self.progress.pack(side=tk.RIGHT, padx=10)
        self.progress['value'] = 0
        
        thread = threading.Thread(target=self._download_thread, args=(info, target))
        thread.daemon = True
        thread.start()
        
    def _download_thread(self, info, target):
        """Download in background"""
        try:
            import urllib.request
            
            def report(block, size, total):
                if total > 0:
                    percent = int(block * size * 100 / total)
                    self.progress['value'] = min(percent, 100)
            
            self.add_message("System", "Downloading model... Please wait...", "assistant")
            
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
            urllib.request.install_opener(opener)
            
            urllib.request.urlretrieve(info["url"], str(target), reporthook=report)
            
            self.progress.pack_forget()
            self.add_message("System", "Download complete! Loading model...", "assistant")
            
            self.model_path = str(target)
            self.load_model()
            
        except Exception as e:
            self.progress.pack_forget()
            self.add_message("System", f"Download failed: {e}", "assistant")
            messagebox.showerror("Error", f"Download failed:\n{e}")
        finally:
            self.is_downloading = False
            self.download_btn.config(text="Download Model", state=tk.NORMAL)
            
    def load_model(self):
        """Load AI model with proper chat format"""
        self.add_message("System", "Loading model (20-30 seconds)...", "assistant")
        
        def load():
            try:
                # Load model
                self.model = llama_cpp.Llama(
                    model_path=self.model_path,
                    n_ctx=2048,
                    n_threads=4,
                    n_gpu_layers=0,
                    verbose=False
                )
                
                self.status.config(text="● Ready", fg="#4CAF50")
                self.send_btn.config(state=tk.NORMAL)
                self.download_btn.config(state=tk.DISABLED, text="Model Loaded")
                self.add_message("System", "✅ Model ready! You can now chat.", "assistant")
                
            except Exception as e:
                self.add_message("System", f"Load failed: {e}", "assistant")
                messagebox.showerror("Error", f"Failed to load model:\n{e}")
                
        threading.Thread(target=load, daemon=True).start()
        
    def send_message(self):
        """Send message to AI with proper prompt format"""
        if not self.model:
            messagebox.showwarning("Warning", "Please download a model first!")
            return
            
        user_input = self.input_text.get("1.0", tk.END).strip()
        if not user_input:
            return
            
        self.add_message("You", user_input, "user")
        self.input_text.delete("1.0", tk.END)
        
        self.send_btn.config(text="Thinking...", state=tk.DISABLED)
        
        def process():
            try:
                # PROPER PROMPT FORMAT - This fixes the weird responses!
                prompt = f"### Human: {user_input}\n### Assistant:"
                
                response = self.model(
                    prompt,
                    max_tokens=256,
                    temperature=self.temp_var.get(),
                    top_p=0.9,
                    repeat_penalty=1.1,
                    stop=["### Human:", "\n\n"],
                    echo=False
                )
                
                answer = response['choices'][0]['text'].strip()
                
                # Clean up response
                if answer:
                    # Remove any remaining prompt artifacts
                    answer = answer.replace("### Assistant:", "").strip()
                    if answer:
                        self.add_message("Assistant", answer, "assistant")
                    else:
                        self.add_message("Assistant", "I'm not sure how to respond to that.", "assistant")
                else:
                    self.add_message("Assistant", "I'm not sure how to respond to that.", "assistant")
                    
            except Exception as e:
                self.add_message("System", f"Error: {e}", "assistant")
            finally:
                self.send_btn.config(text="Send", state=tk.NORMAL)
                
        threading.Thread(target=process, daemon=True).start()
        
    def clear_chat(self):
        """Clear all messages"""
        if messagebox.askyesno("Clear", "Clear all messages?"):
            for msg in self.messages:
                msg.destroy()
            self.messages.clear()
            self.add_message("Assistant", "Chat cleared! How can I help you?", "assistant")
            
    def run(self):
        self.root.mainloop()


# ==================== MAIN ====================

if __name__ == "__main__":
    app = FixedAIAssistant()
    app.run()
#!/usr/bin/env python3
"""
RootTOP Assistant - Complete Fixed Version
Features: Copy text, Edit messages, Logo support
"""

import sys
import os
import threading
import urllib.request
import ssl
from pathlib import Path

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# PIL for image support
try:
    from PIL import Image, ImageTk
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "--quiet"])
    from PIL import Image, ImageTk

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

# ==================== CONFIGURATION ====================

ASSISTANT_NAME = "RootTOP Assistant"
COMPANY_NAME = "ROOTTOP LIMITED"

# Logo path - আপনার লোগো এখানে রাখুন
LOGO_PATH = "logo.jpg"
LOGO_FOLDER = "logo"

def find_logo():
    """Find logo in multiple locations"""
    possible_paths = [
        LOGO_PATH,
        os.path.join(LOGO_FOLDER, "logo.jpg"),
        os.path.join(LOGO_FOLDER, "logo.jpeg"),
        os.path.join(LOGO_FOLDER, "logo.png"),
        "logo.png",
        "icon.jpg",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

# Force English/Bengali language
SYSTEM_PROMPT = """You are RootTOP Assistant, a helpful AI assistant.
IMPORTANT RULES:
1. ALWAYS respond in English or Bengali (Bangla) language only
2. NEVER respond in Vietnamese, Chinese, Japanese, Korean, or any other language
3. Keep responses short, clear, and helpful

Example responses:
- User: "hi" → Assistant: "Hello! How can I help you today?"
- User: "কেমন আছেন?" → Assistant: "আমি ভালো আছি! আপনাকে কিভাবে সাহায্য করতে পারি?"
"""

# Working model
MODELS = {
    "TinyLlama (English/Bengali)": {
        "url": "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "filename": "tinyllama_model.gguf",
        "size": "700 MB"
    }
}

# ==================== Message Widget with Copy Support ====================

class MessageWidget(tk.Frame):
    """Message widget with copy and edit functionality"""
    
    def __init__(self, parent, sender, message, is_user=False, on_edit=None):
        super().__init__(parent, bg='#1a1a2e')
        self.is_user = is_user
        self.message_text = message
        self.on_edit = on_edit
        
        self.pack(fill=tk.X, padx=10, pady=5)
        
        # Sender label
        icon = "→" if is_user else "™"
        name = f"{icon} {sender}"
        name_label = tk.Label(self, text=name, fg='#FFD700' if not is_user else '#AAAAAA',
                              bg='#1a1a2e', font=('Segoe UI', 9, 'bold'))
        name_label.pack(anchor=tk.W if not is_user else tk.E, padx=5)
        
        # Message container frame
        msg_container = tk.Frame(self, bg='#1a1a2e')
        msg_container.pack(anchor=tk.E if is_user else tk.W, padx=5, pady=2)
        
        # Message text with copy support
        self.text_widget = tk.Text(msg_container, bg='#0f3460' if is_user else '#2d2d44',
                                    fg='white', font=('Segoe UI', 11),
                                    wrap=tk.WORD, relief=tk.FLAT,
                                    padx=12, pady=8, width=60, height=1)
        self.text_widget.insert('1.0', message)
        self.text_widget.configure(state=tk.DISABLED)
        self.text_widget.pack()
        
        # Auto adjust height
        lines = message.count('\n') + 1
        self.text_widget.configure(height=min(lines + 1, 20))
        
        # Right-click menu for copy
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="📋 Copy", command=self.copy_message)
        if is_user:
            self.menu.add_command(label="✏️ Edit", command=self.edit_message)
        
        self.text_widget.bind("<Button-3>", self.show_menu)
        
    def show_menu(self, event):
        """Show right-click menu"""
        self.menu.post(event.x_root, event.y_root)
        
    def copy_message(self):
        """Copy message to clipboard"""
        self.clipboard_clear()
        self.clipboard_append(self.message_text)
        # Show feedback (optional)
        
    def edit_message(self):
        """Edit user message"""
        if self.on_edit:
            self.on_edit(self.message_text, self)
            
    def update_message(self, new_message):
        """Update message text"""
        self.message_text = new_message
        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.delete('1.0', tk.END)
        self.text_widget.insert('1.0', new_message)
        self.text_widget.configure(state=tk.DISABLED)
        
        lines = new_message.count('\n') + 1
        self.text_widget.configure(height=min(lines + 1, 20))

# ==================== Main Assistant Class ====================

class RootTOPAssistant:
    def __init__(self):
        self.model = None
        self.model_path = None
        self.downloading = False
        self.is_loading = False
        self.message_widgets = []
        
        self.base_dir = Path(os.getcwd())
        self.models_dir = self.base_dir / "models"
        self.models_dir.mkdir(exist_ok=True)
        
        self.create_gui()
        self.check_existing_models()
        
    def create_gui(self):
        self.root = tk.Tk()
        self.root.title(f"{ASSISTANT_NAME} - {COMPANY_NAME}")
        self.root.geometry("1100x750")
        self.root.configure(bg='#1a1a2e')
        self.root.minsize(800, 600)
        
        self.create_header()
        self.create_chat_area()
        self.create_status_bar()
        self.create_input_panel()
        self.show_welcome()
        self.update_ram_display()
        
    def create_header(self):
        """Create header with logo"""
        header = tk.Frame(self.root, bg='#0f3460', height=100)
        header.pack(fill=tk.X, padx=15, pady=(10,5))
        header.pack_propagate(False)
        
        logo_frame = tk.Frame(header, bg='#0f3460')
        logo_frame.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Load and display logo
        logo_path = find_logo()
        self.logo_image = None
        
        if logo_path and os.path.exists(logo_path):
            try:
                pil_image = Image.open(logo_path)
                pil_image = pil_image.resize((60, 60), Image.Resampling.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(pil_image)
                logo_label = tk.Label(logo_frame, image=self.logo_image, bg='#0f3460')
                logo_label.pack(side=tk.LEFT, padx=5)
            except Exception as e:
                print(f"Logo load error: {e}")
                self.create_default_logo(logo_frame)
        else:
            self.create_default_logo(logo_frame)
            # Show logo not found message in status
            self.status_bar_message = "Logo not found. Place logo.jpg in app folder."
        
        info_frame = tk.Frame(logo_frame, bg='#0f3460')
        info_frame.pack(side=tk.LEFT, padx=10)
        
        company_label = tk.Label(info_frame, text=COMPANY_NAME,
                                  font=('Segoe UI', 10, 'bold'),
                                  fg='#FFD700', bg='#0f3460')
        company_label.pack(anchor=tk.W)
        
        title = tk.Label(info_frame, text=ASSISTANT_NAME,
                         font=('Segoe UI', 18, 'bold'),
                         fg='white', bg='#0f3460')
        title.pack(anchor=tk.W)
        
        subtitle = tk.Label(info_frame, text="Your Personal AI Assistant | English/Bengali",
                            font=('Segoe UI', 9), fg='#AAAAAA', bg='#0f3460')
        subtitle.pack(anchor=tk.W)
        
        self.status_frame = tk.Frame(header, bg='#0f3460')
        self.status_frame.pack(side=tk.RIGHT, padx=20)
        
        self.status_dot = tk.Label(self.status_frame, text="●",
                                   font=('Segoe UI', 14), fg='#FF6B6B', bg='#0f3460')
        self.status_dot.pack(side=tk.LEFT)
        
        self.status_text = tk.Label(self.status_frame, text="Not Ready",
                                    font=('Segoe UI', 10), fg='#FF6B6B', bg='#0f3460')
        self.status_text.pack(side=tk.LEFT, padx=5)
        
    def create_default_logo(self, parent):
        """Create default text logo"""
        logo_bg = tk.Label(parent, text="™", font=('Segoe UI', 36, 'bold'),
                           fg='#FFD700', bg='#0f3460')
        logo_bg.pack(side=tk.LEFT, padx=5)
        
    def create_chat_area(self):
        """Create chat display area with scroll"""
        chat_container = tk.Frame(self.root, bg='#1a1a2e')
        chat_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(chat_container, bg='#1a1a2e', highlightthickness=0)
        scrollbar = tk.Scrollbar(chat_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg='#1a1a2e')
        
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def create_status_bar(self):
        """Create status bar"""
        status_bar = tk.Frame(self.root, bg='#16213e', height=35)
        status_bar.pack(fill=tk.X, padx=15, pady=(0,5))
        status_bar.pack_propagate(False)
        
        self.model_label = tk.Label(status_bar, text="⚙️ Model: Not loaded",
                                     fg='#AAAAAA', bg='#16213e', font=('Segoe UI', 9))
        self.model_label.pack(side=tk.LEFT, padx=10)
        
        copyright_label = tk.Label(status_bar, text=f"© 2024 {COMPANY_NAME} | Language: English/Bengali | Right-click on messages to copy/edit",
                                    fg='#666666', bg='#16213e', font=('Segoe UI', 8))
        copyright_label.pack(side=tk.LEFT, expand=True)
        
        self.ram_label = tk.Label(status_bar, text="💾 RAM: 0/0 GB",
                                   fg='#AAAAAA', bg='#16213e', font=('Segoe UI', 9))
        self.ram_label.pack(side=tk.RIGHT, padx=10)
        
    def create_input_panel(self):
        """Create input area"""
        input_frame = tk.Frame(self.root, bg='#16213e')
        input_frame.pack(fill=tk.X, padx=15, pady=(0,15))
        
        controls = tk.Frame(input_frame, bg='#16213e')
        controls.pack(fill=tk.X, padx=15, pady=(10,5))
        
        self.download_btn = tk.Button(controls, text="📥 Download Model",
                                       command=self.download_model,
                                       bg='#1a53a0', fg='white',
                                       font=('Segoe UI', 10, 'bold'),
                                       relief=tk.FLAT, padx=15, pady=5,
                                       cursor='hand2')
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Label(controls, text="🌡️ Temp:", fg='white', bg='#16213e',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(20,5))
        
        self.temp_var = tk.DoubleVar(value=0.5)
        temp_scale = tk.Scale(controls, from_=0.0, to=1.0, resolution=0.05,
                              orient=tk.HORIZONTAL, variable=self.temp_var,
                              length=100, bg='#16213e', fg='white',
                              highlightthickness=0)
        temp_scale.pack(side=tk.LEFT, padx=5)
        temp_scale.configure(command=self.update_temp_label)
        
        self.temp_label = tk.Label(controls, text="0.50", fg='white',
                                   bg='#16213e', font=('Segoe UI', 10))
        self.temp_label.pack(side=tk.LEFT, padx=5)
        
        self.thinking_label = tk.Label(controls, text="💡 Ready",
                                        fg='#4CAF50', bg='#16213e', font=('Segoe UI', 10))
        self.thinking_label.pack(side=tk.LEFT, padx=20)
        
        tk.Label(input_frame, text="💬 Your message (English / বাংলা) - Right-click on any message to copy:", 
                fg='white', bg='#16213e', font=('Segoe UI', 9)).pack(anchor=tk.W, padx=15, pady=(10,0))
        
        # Input text with Ctrl+A, Ctrl+C support
        self.input_text = scrolledtext.ScrolledText(input_frame, height=3,
                                                     bg='#2d2d44', fg='white',
                                                     insertbackground='white',
                                                     font=('Segoe UI', 11),
                                                     relief=tk.FLAT, wrap=tk.WORD)
        self.input_text.pack(fill=tk.X, padx=15, pady=5)
        self.input_text.bind('<Control-Return>', lambda e: self.send_message())
        self.input_text.bind('<Control-a>', self.select_all)
        self.input_text.bind('<Control-c>', self.copy_selection)
        
        buttons = tk.Frame(input_frame, bg='#16213e')
        buttons.pack(fill=tk.X, padx=15, pady=(5,15))
        
        self.send_btn = tk.Button(buttons, text="📤 Send Message", command=self.send_message,
                                   bg='#1a53a0', fg='white', font=('Segoe UI', 11, 'bold'),
                                   relief=tk.FLAT, padx=25, pady=8, cursor='hand2',
                                   state=tk.DISABLED)
        self.send_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = tk.Button(buttons, text="🗑️ Clear Chat", command=self.clear_chat,
                                    bg='#1a53a0', fg='white', font=('Segoe UI', 11, 'bold'),
                                    relief=tk.FLAT, padx=25, pady=8, cursor='hand2')
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(buttons, variable=self.progress_var,
                                             length=250, mode='determinate')
        
    def select_all(self, event):
        """Select all text in input"""
        self.input_text.tag_add('sel', '1.0', 'end-1c')
        return 'break'
        
    def copy_selection(self, event):
        """Copy selected text"""
        try:
            selected = self.input_text.get('sel.first', 'sel.last')
            self.root.clipboard_clear()
            self.root.clipboard_append(selected)
        except:
            pass
        return 'break'
        
    def update_temp_label(self, value):
        self.temp_label.config(text=f"{float(value):.2f}")
        
    def update_ram_display(self):
        try:
            ram = psutil.virtual_memory()
            used = (ram.total - ram.available) / (1024**3)
            total = ram.total / (1024**3)
            self.ram_label.config(text=f"💾 RAM: {used:.1f}/{total:.1f} GB")
        except:
            pass
        self.root.after(2000, self.update_ram_display)
        
    def add_message(self, sender, message, is_user=False):
        """Add message to chat with copy support"""
        def edit_callback(old_msg, widget):
            self.edit_user_message(old_msg, widget)
            
        msg_widget = MessageWidget(self.scroll_frame, sender, message, is_user, edit_callback)
        self.message_widgets.append(msg_widget)
        
        # Scroll to bottom
        self.canvas.yview_moveto(1.0)
        
        return msg_widget
        
    def edit_user_message(self, old_message, widget):
        """Edit user message"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Message")
        dialog.geometry("500x300")
        dialog.configure(bg='#1a1a2e')
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Edit your message:", fg='white', bg='#1a1a2e',
                font=('Segoe UI', 11)).pack(pady=10)
        
        text_area = tk.Text(dialog, bg='#2d2d44', fg='white',
                            font=('Segoe UI', 11), wrap=tk.WORD,
                            height=8, width=50)
        text_area.insert('1.0', old_message)
        text_area.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        def save_edit():
            new_message = text_area.get('1.0', tk.END).strip()
            if new_message and new_message != old_message:
                widget.update_message(new_message)
                # Also update in conversation history if needed
            dialog.destroy()
            
        btn_frame = tk.Frame(dialog, bg='#1a1a2e')
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Save", command=save_edit,
                 bg='#4CAF50', fg='white', padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                 bg='#555555', fg='white', padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        
    def show_welcome(self):
        welcome_msg = f"""Welcome to {ASSISTANT_NAME}! 🎉

✨ **Features:**
• Right-click on any message to COPY text
• Right-click on YOUR messages to EDIT them
• Select text with mouse and press Ctrl+C to copy
• Press Ctrl+A to select all text

💡 **How to use:**
1. Click "Download Model" button (first time only)
2. Wait for download (5-10 minutes)
3. Start chatting in English or Bengali!

📋 **Copy/Edit Tips:**
• Right-click on any message → Copy
• Right-click on your message → Edit
• Select text → Ctrl+C to copy

© 2024 {COMPANY_NAME}"""
        
        self.add_message(ASSISTANT_NAME, welcome_msg, is_user=False)
        
    def check_existing_models(self):
        for model_name, info in MODELS.items():
            model_path = self.models_dir / info["filename"]
            if model_path.exists():
                file_size = model_path.stat().st_size / (1024**3)
                if file_size > 0.5:
                    self.model_path = str(model_path)
                    self.load_model()
                    return True
                else:
                    model_path.unlink()
        return False
        
    def download_model(self):
        if self.downloading:
            return
        
        info = MODELS["TinyLlama (English/Bengali)"]
        target_path = self.models_dir / info["filename"]
        
        if target_path.exists():
            file_size = target_path.stat().st_size / (1024**3)
            if file_size < 0.5:
                target_path.unlink()
        
        confirm = messagebox.askyesno("Download Model", 
            f"Download TinyLlama Model ({info['size']})?\n\n"
            f"This will take 5-10 minutes.\n"
            f"Internet connection required.\n\n"
            f"After download, the model will speak English/Bengali.\n\n"
            f"Continue?")
        
        if not confirm:
            return
        
        self.downloading = True
        self.download_btn.config(text="Downloading...", state=tk.DISABLED)
        self.progress_bar.pack(side=tk.RIGHT, padx=10)
        self.progress_var.set(0)
        
        self.add_message(ASSISTANT_NAME, "📥 Downloading model... Please wait (5-10 minutes)", is_user=False)
        
        thread = threading.Thread(target=self._download_thread, args=(info,))
        thread.daemon = True
        thread.start()
        
    def _download_thread(self, info):
        try:
            target_path = self.models_dir / info["filename"]
            
            def report(block, size, total):
                if total > 0:
                    percent = int(block * size * 100 / total)
                    self.progress_var.set(min(percent, 100))
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
            opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
            urllib.request.install_opener(opener)
            
            urllib.request.urlretrieve(info["url"], str(target_path), reporthook=report)
            
            self.progress_bar.pack_forget()
            self.add_message(ASSISTANT_NAME, "✅ Download complete! Loading model...", is_user=False)
            
            self.model_path = str(target_path)
            self.load_model()
            
        except Exception as e:
            self.progress_bar.pack_forget()
            self.add_message(ASSISTANT_NAME, f"❌ Download failed: {str(e)[:150]}", is_user=False)
            messagebox.showerror("Download Failed", str(e))
            
        finally:
            self.downloading = False
            self.download_btn.config(text="📥 Download Model", state=tk.NORMAL)
            
    def load_model(self):
        if self.is_loading:
            return
        
        if not self.model_path or not os.path.exists(self.model_path):
            return
        
        self.is_loading = True
        self.add_message(ASSISTANT_NAME, "🔄 Loading model (30-60 seconds)...", is_user=False)
        
        def load():
            try:
                self.model = llama_cpp.Llama(
                    model_path=self.model_path,
                    n_ctx=1024,
                    n_threads=2,
                    n_gpu_layers=0,
                    verbose=False
                )
                
                self.status_dot.config(fg='#4CAF50')
                self.status_text.config(text="Ready", fg='#4CAF50')
                self.send_btn.config(state=tk.NORMAL)
                self.model_label.config(text="⚙️ Model: TinyLlama")
                self.thinking_label.config(text="💡 Ready to assist", fg='#4CAF50')
                
                self.add_message(ASSISTANT_NAME, "✅ Ready! Right-click on any message to copy text. How can I help you?", is_user=False)
                
            except Exception as e:
                self.add_message(ASSISTANT_NAME, f"❌ Failed to load: {str(e)[:100]}", is_user=False)
                messagebox.showerror("Load Failed", str(e))
                
            finally:
                self.is_loading = False
                
        threading.Thread(target=load, daemon=True).start()
        
    def send_message(self):
        if not self.model:
            messagebox.showwarning("Model Required", "Please download the model first!")
            return
            
        user_input = self.input_text.get("1.0", tk.END).strip()
        if not user_input:
            return
            
        self.add_message("You", user_input, is_user=True)
        self.input_text.delete("1.0", tk.END)
        
        self.send_btn.config(text="🤔 Thinking...", state=tk.DISABLED)
        self.thinking_label.config(text="🤔 Thinking...", fg='#FF9800')
        
        def process():
            try:
                prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_input}\nAssistant: "
                
                response = self.model(
                    prompt,
                    max_tokens=256,
                    temperature=self.temp_var.get(),
                    top_p=0.9,
                    repeat_penalty=1.1,
                    stop=["User:", "\n\n", "Assistant:"],
                    echo=False
                )
                
                answer = response['choices'][0]['text'].strip()
                
                if not answer or len(answer) < 2:
                    answer = "I'm here to help! Please ask your question in English or Bengali."
                
                # Filter non-English/Bengali
                import re
                clean_answer = re.sub(r'[^\u0000-\u007F\u0980-\u09FF\s\.\,\!\?\'\"]+', '', answer)
                if clean_answer.strip():
                    answer = clean_answer
                
                self.add_message(ASSISTANT_NAME, answer, is_user=False)
                
            except Exception as e:
                self.add_message(ASSISTANT_NAME, f"Error: {str(e)[:100]}", is_user=False)
                
            finally:
                self.send_btn.config(text="📤 Send Message", state=tk.NORMAL)
                self.thinking_label.config(text="💡 Ready", fg='#4CAF50')
                
        threading.Thread(target=process, daemon=True).start()
        
    def clear_chat(self):
        if messagebox.askyesno("Clear Chat", "Clear all messages?"):
            for widget in self.message_widgets:
                widget.destroy()
            self.message_widgets.clear()
            self.add_message(ASSISTANT_NAME, "Chat cleared! Right-click on messages to copy text.", is_user=False)
            
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = RootTOPAssistant()
    app.run()
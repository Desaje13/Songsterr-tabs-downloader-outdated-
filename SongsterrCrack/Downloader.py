import warnings
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import json
import time
import requests
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import threading

warnings.filterwarnings("ignore")
threads = []
MAX_LINK_LENGTH = 300

def log_message(message, tag="info", clear=False):
    if clear:
        output_text.config(state=tk.NORMAL)
        output_text.delete(1.0, tk.END)
    output_text.config(state=tk.NORMAL)
    output_text.insert(tk.END, message + "\n", tag)
    output_text.see(tk.END)
    output_text.config(state=tk.DISABLED)

def _onKeyRelease(event):
    ctrl = (event.state & 0x4) != 0
    if event.keycode == 88 and ctrl and event.keysym.lower() != "x":
        event.widget.event_generate("<<Cut>>")
    if event.keycode == 86 and ctrl and event.keysym.lower() != "v":
        handle_paste(event)
    if event.keycode == 67 and ctrl and event.keysym.lower() != "c":
        event.widget.event_generate("<<Copy>>")
    if event.keycode == 65 and ctrl and event.keysym.lower() != "a":
        event.widget.event_generate("<<SelectAll>>")
        return "break"

def handle_paste(event):
    try:
        clipboard_text = root.clipboard_get()
        if len(clipboard_text) > MAX_LINK_LENGTH:
            log_message(f"Error: Link is too long. Max length is {MAX_LINK_LENGTH} characters.", tag="error")
            return "break"
        input_field.insert(tk.INSERT, clipboard_text)
    except tk.TclError:
        pass
    return "break"

def process_link():
    driver = None
    try:
        url = input_field.get().strip()
        if not url:
            log_message("Error: Please enter a Songsterr link!", tag="error", clear=True)
            return
        if len(url) > MAX_LINK_LENGTH:
            log_message(f"Error: Link is too long. Max length is {MAX_LINK_LENGTH} characters.", tag="error", clear=True)
            return
        log_message(f"Processing link: {url}", tag="info", clear=True)
        capabilities = DesiredCapabilities.CHROME.copy()
        capabilities["goog:loggingPrefs"] = {"performance": "ALL"}
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('--ignore-certificate-errors')
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        driver = webdriver.Chrome(options=options)
        log_message("Loading website...", tag="info")
        driver.get(url)
        time.sleep(3)
        performance_logs = driver.get_log("performance")
        log_message("Extracting logs...", tag="info")
        file_url = None
        for log in performance_logs:
            message = json.loads(log["message"])
            log_data = message["message"]
            if log_data["method"] == "Network.responseReceived":
                response_url = log_data["params"]["response"]["url"]
                if "revisions" in response_url:
                    file_url = response_url
                    break
        if file_url:
            response = requests.get(file_url, verify=False)
            if response.status_code == 200:
                response_data = list((response.text[2:-2]).split(","))
                for item in response_data:
                    if ".gp" in item:
                        download_url = item.split(":", 1)[1].strip('"')
                        log_message("File successfully processed.", tag="success")
                        webbrowser.open(download_url, new=0, autoraise=True)
                        return
            else:
                log_message(f"Error: Failed to load file: {response.status_code}", tag="error")
        else:
            log_message("Error: 'revisions' file not found!", tag="error")
    except Exception as e:
        log_message(f"Error: {e}", tag="error")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                log_message("Error: Failed to properly close the driver.", tag="error")
        log_message("Processing complete.", tag="success")

def start_processing():
    thread = threading.Thread(target=process_link)
    threads.append(thread)
    thread.start()

def on_exit():
    active_threads = [t for t in threads if t.is_alive()]
    if active_threads:
        messagebox.showwarning("Warning", "Please wait for all tasks to complete before closing the application.")
    else:
        root.destroy()

root = tk.Tk()
root.title("Songsterr Downloader")
root.geometry("800x500")
root.resizable(False, False)
root.config(bg="#1d1f27")
root.wm_attributes("-topmost", True)

root.bind_all("<Key>", _onKeyRelease, "+")

style = ttk.Style()
style.configure("TLabel", font=("Courier", 12), foreground="#9A6CFF", background="#1d1f27")
style.configure("TButton", font=("Courier", 12, "bold"), foreground="#FFFFFF", background="#282a36")

header_label = ttk.Label(
    root, text="🎶 Songsterr Downloader 🎶", font=("Courier", 20, "bold"), foreground="#9A6CFF", background="#1d1f27"
)
header_label.pack(pady=10)

frame = tk.Frame(root, bg="#1d1f27")
frame.pack(pady=10)
label = tk.Label(frame, text="Enter the link:", font=("Courier", 12), fg="#9A6CFF", bg="#1d1f27")
label.grid(row=0, column=0, padx=5, pady=5)

input_field = tk.Entry(
    frame,
    width=50,
    font=("Courier", 10),
    fg="#FFFFFF",
    bg="#282a36",
    insertbackground="#FFFFFF",
)
input_field.grid(row=0, column=1, padx=5, pady=5)

button_frame = tk.Frame(root, bg="#1d1f27")
button_frame.pack(pady=10)
download_button = tk.Button(
    button_frame,
    text="Download",
    command=start_processing,
    font=("Courier", 12, "bold"),
    fg="#FFFFFF",
    bg="#44475a",
    activebackground="#6272a4",
    activeforeground="#FFFFFF",
)
download_button.grid(row=0, column=0, padx=10)
quit_button = tk.Button(
    button_frame,
    text="Quit",
    command=on_exit,
    font=("Courier", 12, "bold"),
    fg="#FFFFFF",
    bg="#44475a",
    activebackground="#6272a4",
    activeforeground="#FFFFFF",
)
quit_button.grid(row=0, column=1, padx=10)

output_text = tk.Text(root, wrap=tk.WORD, height=12, state=tk.DISABLED, font=("Courier", 10))
output_text.pack(pady=10, padx=10, fill=tk.BOTH)
output_text.config(
    bg="#282a36", fg="#f8f8f2", highlightbackground="#9A6CFF", highlightthickness=2
)

output_text.tag_configure("success", foreground="#00FF00")
output_text.tag_configure("error", foreground="#FF0000")
output_text.tag_configure("info", foreground="#9A6CFF")

footer_label = ttk.Label(
    root, text="Made by Desaje (2024) v1.0.0", font=("Courier", 10, "italic"), foreground="#9A6CFF", background="#1d1f27"
)
footer_label.pack(side=tk.BOTTOM, pady=5)

root.protocol("WM_DELETE_WINDOW", on_exit)
root.mainloop()

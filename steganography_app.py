import tkinter as tk
from tkinterdnd2 import TkinterDnD, DND_FILES
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from lsb_steganography import encode_image_lsb, decode_image_lsb, encode_audio_lsb, decode_audio_lsb

class SteganographyApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("LSB Steganography")

         # Frame for file selection
        self.frame = tk.Frame(self)
        self.frame.pack(pady=20)

        self.cover_label = tk.Label(self.frame, text="Cover Object (Image/Audio):")
        self.cover_label.grid(row=0, column=0, padx=10)

        self.cover_entry = tk.Entry(self.frame, width=40)  # Text field for drag-and-drop
        self.cover_entry.grid(row=0, column=1)

        self.cover_browse_button = tk.Button(self.frame, text="Browse", command=self.load_cover_file)
        self.cover_browse_button.grid(row=0, column=2)

        self.payload_label = tk.Label(self.frame, text="Payload (Text):")
        self.payload_label.grid(row=1, column=0, padx=10)

        self.payload_entry = tk.Entry(self.frame, width=40)  # Text field for drag-and-drop
        self.payload_entry.grid(row=1, column=1)

        self.payload_browse_button = tk.Button(self.frame, text="Browse", command=self.load_payload_file)
        self.payload_browse_button.grid(row=1, column=2)

        self.lsb_label = tk.Label(self.frame, text="Number of LSBs:")
        self.lsb_label.grid(row=2, column=0, padx=10)

        self.lsb_var = tk.IntVar(value=1)
        self.lsb_spinbox = tk.Spinbox(self.frame, from_=1, to=8, textvariable=self.lsb_var)
        self.lsb_spinbox.grid(row=2, column=1)

        self.encode_button = tk.Button(self.frame, text="Encode", command=self.encode)
        self.encode_button.grid(row=3, column=0, pady=20)

        self.decode_button = tk.Button(self.frame, text="Decode", command=self.decode)
        self.decode_button.grid(row=3, column=1, pady=20)

        # Placeholder for displaying the cover image
        self.image_label = tk.Label(self)
        self.image_label.pack()

        # Variables for storing paths
        self.cover_file_path = None
        self.payload_file_path = None

        # Bind drag-and-drop events
        self.cover_entry.drop_target_register(DND_FILES)
        self.cover_entry.dnd_bind('<<Drop>>', self.on_drop_cover)

        self.payload_entry.drop_target_register(DND_FILES)
        self.payload_entry.dnd_bind('<<Drop>>', self.on_drop_payload)

    def on_drop_cover(self, event):
        self.cover_file_path = event.data
        self.cover_entry.delete(0, tk.END)
        self.cover_entry.insert(0, self.cover_file_path)

        if self.cover_file_path.endswith(('.png', '.bmp')):
            img = Image.open(self.cover_file_path)
            img.thumbnail((300, 300))
            img_tk = ImageTk.PhotoImage(img)
            self.image_label.config(image=img_tk)
            self.image_label.image = img_tk  # Keep a reference

        elif self.cover_file_path.endswith('.wav'):
            messagebox.showinfo("Cover Object", "Audio file selected as cover object.")

    def on_drop_payload(self, event):
        self.payload_file_path = event.data
        self.payload_entry.delete(0, tk.END)
        self.payload_entry.insert(0, self.payload_file_path)

    def load_cover_file(self):
        self.cover_file_path = filedialog.askopenfilename(
            title="Select Cover Object (Image/Audio)",
            filetypes=[("Image/Audio files", "*.png;*.bmp;*.wav")]
        )
        if self.cover_file_path:
            self.cover_entry.delete(0, tk.END)
            self.cover_entry.insert(0, self.cover_file_path)

            if self.cover_file_path.endswith(('.png', '.bmp')):
                img = Image.open(self.cover_file_path)
                img.thumbnail((300, 300))
                img_tk = ImageTk.PhotoImage(img)
                self.image_label.config(image=img_tk)
                self.image_label.image = img_tk  # Keep a reference

            elif self.cover_file_path.endswith('.wav'):
                messagebox.showinfo("Cover Object", "Audio file selected as cover object.")

    def load_payload_file(self):
        self.payload_file_path = filedialog.askopenfilename(
            title="Select Payload (Text File)",
            filetypes=[("Text files", "*.txt")]
        )
        if self.payload_file_path:
            self.payload_entry.delete(0, tk.END)
            self.payload_entry.insert(0, self.payload_file_path)

    def encode(self):
        if self.cover_file_path and self.payload_file_path:
            lsb_bits = self.lsb_var.get()
            if self.cover_file_path.endswith('.png') or self.cover_file_path.endswith('.bmp'):
                output_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
            if self.cover_file_path.endswith('.wav'):
                output_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV files", "*.wav")])
                if output_path:
                    encode_audio_lsb(self.cover_file_path, self.payload_file_path, output_path)
                    messagebox.showinfo("Success", f"Encoded stego audio saved as {output_path}")
            else:
                if output_path:
                    encode_image_lsb(self.cover_file_path, self.payload_file_path, output_path, lsb_bits)
                    messagebox.showinfo("Success", f"Encoded stego image saved as {output_path}")
        else:
            messagebox.showwarning("Error", "Please select both cover object and payload")

    def decode(self):
        if self.cover_file_path:
            if self.cover_file_path.endswith('.wav'):
                decoded_message = decode_audio_lsb(self.cover_file_path)
            else:
                decoded_message = decode_image_lsb(self.cover_file_path, self.lsb_var.get())
            messagebox.showinfo("Decoded Message", decoded_message)
        else:
            messagebox.showwarning("Error", "Please select a cover object first")


if __name__ == "__main__":
    app = SteganographyApp()
    app.mainloop()
import numpy as np
import os
import base64
import struct
import tkinter as tk
from tkinter import messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD

def convert_to_exact_mzxml(input_path, output_path):
    try:
        #Parse raw data from Autof ms1000 text file
        data = np.loadtxt(input_path, delimiter=None, skiprows=2)
        mz = data[:, 0].astype(np.float32)
        intensity = data[:, 1].astype(np.float32)

        #Calculate metrics (required for mzXML header)
        peaks_count = len(mz)
        #highest intensity peak is the base peak
        bp_idx = np.argmax(intensity)
        base_peak_mz = mz[bp_idx]
        base_peak_intensity = intensity[bp_idx]
        #sum of all intensities is the total ion current
        tot_ion_current = np.sum(intensity)
        low_mz, high_mz = np.min(mz), np.max(mz)

        #Encode Peaks to Base64 to allow software like MicrobeMS to read them correctly
        peak_data = []
        for m, i in zip(mz, intensity):
            peak_data.append(m)
            peak_data.append(i)
        
        # '>' forces Big Endian, 'f' is 32-bit float
        binary_data = struct.pack('>' + 'f' * len(peak_data), *peak_data)
        encoded_peaks = base64.b64encode(binary_data).decode('ascii')

        #XML Template to work with MicrobeMS
        xml_content = f'''<?xml version="1.0" encoding="ISO-8859-1"?>
<mzXML xmlns="http://sashimi.sourceforge.net/schema_revision/mzXML_2.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://sashimi.sourceforge.net/schema_revision/mzXML_2.1 http://sashimi.sourceforge.net/schema_revision/mzXML_2.1/mzXML_idx_2.1.xsd">
<msRun scanCount="1">
<parentFile fileName="" fileType="processedData" fileSha1="0000000000000000000000000000000000000000"/>
<msInstrument>
<msManufacturer category="msManufacturer" value="Autobio Diagnostics"/>
<msModel category="msModel" value="ms1000"/>
<msIonisation category="msIonisation" value="MALDI"/>
<msMassAnalyzer category="msMassAnalyzer" value="TOF"/>
<msDetector category="msDetector" value=""/>
<software type="acquisition" name="" version=""/>
<operator first="Manuel" last="Escalera"/>
</msInstrument>
<dataProcessing>
<software type="processing" name="" version=""/>
</dataProcessing>
<scan num="1" msLevel="1" peaksCount="{peaks_count}" polarity="+" lowMz="{low_mz:.6f}" highMz="{high_mz:.6f}" basePeakMz="{base_peak_mz:.6f}" basePeakIntensity="{base_peak_intensity:.6f}" tot_ion_current="{tot_ion_current:.6f}">
<peaks precision="32" byteOrder="network" contentType="m/z-int" compressionType="none" compressedLen="0">{encoded_peaks}</peaks>
</scan>
</msRun>
</mzXML>'''

        #Save with ISO-8859-1 encoding and Windows line endings
        with open(output_path, 'w', encoding='ISO-8859-1', newline='\r\n') as f:
            f.write(xml_content)
            
        return True
    except Exception as e:
        print(f"Error converting {input_path}: {e}")
        return False

#drag and drop event handler
def handle_drop(event):
    files = root.tk.splitlist(event.data)
    success_count = 0
    
    for file_path in files:
        clean_path = file_path.strip('{}')
        if clean_path.lower().endswith('.txt'):
            output_path = os.path.splitext(clean_path)[0] + ".mzXML"
            if convert_to_exact_mzxml(clean_path, output_path):
                success_count += 1
                listbox.insert(tk.END, f"SUCCESS: {os.path.basename(clean_path)}")
            else:
                listbox.insert(tk.END, f"FAILED: {os.path.basename(clean_path)}")
        else:
            listbox.insert(tk.END, f"SKIPPED (Not .txt): {os.path.basename(clean_path)}")
    
    listbox.yview(tk.END)
    messagebox.showinfo("Done", f"Converted {success_count} of {len(files)} files.")

#GUI Construction
root = TkinterDnD.Tk()
root.title("Autof ms1000 .txt to mzXML Converter (for MicrobeMS)")
root.geometry("600x400")

label = tk.Label(root, text="Drag & Drop Autof ms1000 .txt files", pady=15, font=("Arial", 12, "bold"))
type_label = tk.Label(root, text="You are converting to .mzXML format", pady=5, font=("Arial", 12, "bold"))
instruction = tk.Label(root, text="Files will be converted and saved into the same directory as the original", pady=15, font=("Arial", 9, "bold"))
label.pack()
type_label.pack()
instruction.pack()

listbox = tk.Listbox(root, width=80, height=12, font=("Consolas", 9))
listbox.pack(padx=20, pady=10)

clear_btn = tk.Button(root, text="Clear List", command=lambda: listbox.delete(0, tk.END))
clear_btn.pack()

# Setup Drag and Drop
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', handle_drop)

root.mainloop()
import numpy as np
import os
import uuid
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD

def convert_to_msp_match_xml(input_path, output_path):
    try:
        #Parse raw data from Autof ms1000 text file
        #Skips 2 header lines; reads M/Z (mass) and Intensity
        data = np.loadtxt(input_path, delimiter=None, skiprows=2)
        mass = data[:, 0]
        intensity = data[:, 1]

        #Normalize Intensity (max intensity of 1.0 for the schema)
        max_val = np.max(intensity)
        if max_val > 0:
            norm_intensity = intensity / max_val
        else:
            norm_intensity = intensity

        # 3. Generate Metadata
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        project_name = datetime.now().strftime("%y%m%d-%H%M") + "-1123456789"
        file_uuid = str(uuid.uuid4())
        analyte_id = f"ID-xml-{datetime.now().strftime('%d-%b-%Y-%H-%M-%S.%f')[:-3]}"
        
        #Build Peak List XML tags
        peak_entries = []
        for m, i in zip(mass, norm_intensity):
            # Using attributes seen in lwelshmeri.xml: mass, intensity, profile, sigma
            entry = f'      <Peak intensity="{i:.6g}" mass="{m:.8g}" profile="1.0" sigma="10.0"/>'
            peak_entries.append(entry)
        
        peaks_xml = "\n".join(peak_entries)

        #Construct the MspMatchResult XML Template for use with MicrobeMS
        xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<MspMatchResult>
  <ProjectInfo name="{project_name}" timestamp="{timestamp}" instrumentId="000000.00000" externalTargetId="1123456789" uuid="{str(uuid.uuid4())}" validationPosition="not available" validationResult="true" projectTypeName="MicrobeMSconversion" creator="Manuel Escalera" totalSampleNumber="1" comment=""/>
  <Analytes>
    <Analyte name="{analyte_id}" internId="{str(uuid.uuid4())}" externId="{os.path.basename(input_path)}" description="XML file created by Custom Converter" typeName="Sample" timestamp="{timestamp}" targetChip="0" targetPosition="A1">
      <Peaklist intensityScale="{max_val:.7g}" userCrafted="true" uuid="{file_uuid}">
        <Peaks>
{peaks_xml}
        </Peaks>
      </Peaklist>
    </Analyte>
  </Analytes>
</MspMatchResult>'''

        # 6. Save with UTF-8 encoding
        with open(output_path, 'w', encoding='UTF-8', newline='\n') as f:
            f.write(xml_content)
            
        return True
    except Exception as e:
        print(f"Conversion failed: {e}")
        return False

#Drag and Drop event handler
def handle_drop(event):
    files = root.tk.splitlist(event.data)
    success_count = 0
    
    for file_path in files:
        clean_path = file_path.strip('{}')
        if clean_path.lower().endswith('.txt'):
            output_path = os.path.splitext(clean_path)[0] + ".xml"
            if convert_to_msp_match_xml(clean_path, output_path):
                success_count += 1
                listbox.insert(tk.END, f"SUCCESS: {os.path.basename(output_path)}")
            else:
                listbox.insert(tk.END, f"FAILED: {os.path.basename(clean_path)}")
        else:
            listbox.insert(tk.END, f"SKIPPED: {os.path.basename(clean_path)}")
    
    listbox.yview(tk.END)
    messagebox.showinfo("Done", f"Converted {success_count} files to MspMatchResult schema.")

#GUI Construction
root = TkinterDnD.Tk()
root.title("Autof ms100 .txt to .XML Converter (for CDC MicrobeNet)")
root.geometry("600x400")

tk.Label(root, text="Drag & Drop Autof ms1000 .txt files", font=("Arial", 12, "bold"), pady=10).pack()
tk.Label(root, text="You are converting to .XML format", font=("Arial", 12, "bold"), pady=10).pack()
tk.Label(root, text="Files will be converted and saved into the same directory as the original", font=("Arial", 9)).pack()

listbox = tk.Listbox(root, width=80, height=12, font=("Consolas", 9))
listbox.pack(padx=20, pady=10)

tk.Button(root, text="Clear List", command=lambda: listbox.delete(0, tk.END)).pack()

root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', handle_drop)

root.mainloop()
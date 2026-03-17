import numpy as np
import os
import uuid
import base64
import zlib
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD

def encode_data(array, use_compression=True):
    # Ensure float64 for m/z and float32 for intensity (common mzML practice)
    binary_data = array.tobytes()
    if use_compression:
        binary_data = zlib.compress(binary_data)
    return base64.b64encode(binary_data).decode('ascii')

def convert_to_mzml(input_path, output_path):
    try:
        #Parse raw data
        data = np.loadtxt(input_path, delimiter=None, skiprows=2)
        mass = data[:, 0].astype(np.float64)
        intensity = data[:, 1].astype(np.float32)
        
        peak_count = len(mass)
        mz_encoded = encode_data(mass)
        int_encoded = encode_data(intensity)
        
        # 2. Metadata Generation
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        file_id = os.path.basename(input_path)
        
        # 3. Construct mzML Template
        # Note: Accessions (MS:1000XXX) are standard PSI-MS controlled vocabulary
        mzml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<mzML xmlns="http://psi.hupo.org/ms/mzml" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://psi.hupo.org/ms/mzml http://psidev.info/files/ms/mzML/xsd/mzML1.1.0.xsd" id="{file_id}" version="1.1.0">
  <cvList count="2">
    <cv id="MS" fullName="Proteomics Standards Initiative Mass Spectrometry Ontology" version="4.1.129" URI="https://raw.githubusercontent.com/HUPO-PSI/psi-ms-CV/master/psi-ms.obo"/>
    <cv id="UO" fullName="Unit Ontology" version="releases/2020-03-10" URI="https://raw.githubusercontent.com/bio-ontology-research-group/unit-ontology/master/unit.obo"/>
  </cvList>
  <fileDescription>
    <fileContent>
      <cvParam cvRef="MS" accession="MS:1000294" name="mass spectrum" value=""/>
    </fileContent>
  </fileDescription>
  <run id="run_1" defaultInstrumentConfigurationRef="IC1" startTimeStamp="{timestamp}">
    <spectrumList count="1" defaultDataProcessingRef="DP1">
      <spectrum index="0" id="scan=1" defaultArrayLength="{peak_count}">
        <cvParam cvRef="MS" accession="MS:1000511" name="ms level" value="1"/>
        <cvParam cvRef="MS" accession="MS:1000128" name="profile spectrum" value=""/>
        <cvParam cvRef="MS" accession="MS:1000528" name="lowest observed m/z" value="{np.min(mass)}"/>
        <cvParam cvRef="MS" accession="MS:1000527" name="highest observed m/z" value="{np.max(mass)}"/>
        <binaryDataArrayList count="2">
          <binaryDataArray encodedLength="{len(mz_encoded)}">
            <cvParam cvRef="MS" accession="MS:1000523" name="64-bit float" value=""/>
            <cvParam cvRef="MS" accession="MS:1000574" name="zlib compression" value=""/>
            <cvParam cvRef="MS" accession="MS:1000514" name="m/z array" value="" unitCvRef="MS" unitAccession="MS:1000040" unitName="m/z"/>
            <binary>{mz_encoded}</binary>
          </binaryDataArray>
          <binaryDataArray encodedLength="{len(int_encoded)}">
            <cvParam cvRef="MS" accession="MS:1000521" name="32-bit float" value=""/>
            <cvParam cvRef="MS" accession="MS:1000574" name="zlib compression" value=""/>
            <cvParam cvRef="MS" accession="MS:1000515" name="intensity array" value="" unitCvRef="MS" unitAccession="MS:1000131" unitName="number of detector counts"/>
            <binary>{int_encoded}</binary>
          </binaryDataArray>
        </binaryDataArrayList>
      </spectrum>
    </spectrumList>
  </run>
</mzML>'''

        with open(output_path, 'w', encoding='UTF-8', newline='\n') as f:
            f.write(mzml_content)
        return True
    except Exception as e:
        print(f"Conversion failed: {e}")
        return False

#handle drag and drop events
def handle_drop(event):
    files = root.tk.splitlist(event.data)
    success_count = 0
    for file_path in files:
        clean_path = file_path.strip('{}')
        if clean_path.lower().endswith('.txt'):
            output_path = os.path.splitext(clean_path)[0] + ".mzML"
            if convert_to_mzml(clean_path, output_path):
                success_count += 1
                listbox.insert(tk.END, f"SUCCESS: {os.path.basename(output_path)}")
            else:
                listbox.insert(tk.END, f"FAILED: {os.path.basename(clean_path)}")
    messagebox.showinfo("Done", f"Converted {success_count} files to .mzML format.")

root = TkinterDnD.Tk()
root.title("Autof ms1000 .txt to .mzML Converter")
root.geometry("600x400")

tk.Label(root, text="Drag & Drop Autof ms1000 .txt files", font=("Arial", 12, "bold"), pady=10).pack()
tk.Label(root, text="You are converting to .mzML format", font=("Arial", 12, "bold"), pady=10).pack()
tk.Label(root, text="Files will be converted and saved into the same directory as the original", font=("Arial", 9)).pack()

listbox = tk.Listbox(root, width=80, height=12, font=("Consolas", 9))
listbox.pack(padx=20, pady=10)
tk.Button(root, text="Clear List", command=lambda: listbox.delete(0, tk.END)).pack()

root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', handle_drop)
root.mainloop()
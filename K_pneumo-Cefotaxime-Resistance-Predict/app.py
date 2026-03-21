import gradio as gr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import subprocess
import tempfile
import os
import joblib
import json

# Load model
model = joblib.load('amr_model.pkl')
with open('model_params.json') as f:
    params = json.load(f)


def run_r_preprocessing(input_path):
    """Call R preprocessing script, return path to output CSV"""
    output_csv = tempfile.mktemp(suffix='.csv')
    
    result = subprocess.run(
        ['Rscript', 'PreProcess.R', input_path, output_csv],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    if result.returncode != 0:
        raise RuntimeError(
            f"R preprocessing failed:\n"
            f"{result.stderr}"
        )
    
    return output_csv


def bin_spectrum(mz, intensity):
    bins    = np.zeros(params['n_bins'], dtype=np.float32)
    indices = ((mz - params['mz_min']) / params['bin_size']).astype(int)
    valid   = (indices >= 0) & (indices < params['n_bins'])
    np.add.at(bins, indices[valid], intensity[valid])
    return bins


def process_spectrum_file(file):
    try:
        # 1. R preprocessing
        preprocessed_csv = run_r_preprocessing(file.name)
        
        # 2. Load output
        df        = pd.read_csv(preprocessed_csv)
        mz        = df['mz'].values.astype(np.float32)
        intensity = df['intensity'].values.astype(np.float32)
        os.remove(preprocessed_csv)
        
        # 3. Bin
        features = bin_spectrum(mz, intensity).reshape(1, -1)
        
        # 4. Predict
        probs            = model.predict_proba(features)[0]
        prob_resistant   = float(probs[1])
        prob_susceptible = float(probs[0])
        prediction       = 'Resistant' if prob_resistant >= 0.5 else 'Susceptible'
        confidence       = 'High' if abs(prob_resistant - 0.5) > 0.3 else 'Low'
        
        output = f"""
        ═══════════════════════════════════════════
        K. PNEUMO CEFOTAXIME PREDICTION RESULT
        ═══════════════════════════════════════════
        Prediction:              {prediction}

        Probability Resistant:   {prob_resistant:.1%}
        Probability Susceptible: {prob_susceptible:.1%}
        Confidence:              {confidence}
        ═══════════════════════════════════════════
        NOTE: Research tool only.
        Clinical decisions require confirmed
        phenotypic susceptibility testing.
        ═══════════════════════════════════════════
        """
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 4))
        
        color = 'firebrick' if prediction == 'Resistant' else 'steelblue'
        axes[0].plot(mz, intensity, linewidth=0.5, color=color)
        axes[0].set_title(f'Preprocessed Spectrum — {prediction}')
        axes[0].set_xlabel('m/z (Da)')
        axes[0].set_ylabel('Intensity')
        axes[0].set_xlim(2000, 20000)
        
        axes[1].bar(
            ['Susceptible', 'Resistant'],
            [prob_susceptible, prob_resistant],
            color=['steelblue', 'firebrick'],
            alpha=0.7
        )
        axes[1].set_ylabel('Probability')
        axes[1].set_title('Prediction Probabilities')
        axes[1].set_ylim(0, 1)
        axes[1].axhline(y=0.5, color='black', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        
        return output, fig
    
    except Exception as e:
        return f"Error: {str(e)}", None

def debug_feature_vector(file):
    """Temporary debug function — remove after diagnosis"""
    try:
        # R preprocessing
        preprocessed_csv = run_r_preprocessing(file.name)
        df        = pd.read_csv(preprocessed_csv)
        mz        = df['mz'].values.astype(np.float32)
        intensity = df['intensity'].values.astype(np.float32)
        os.remove(preprocessed_csv)
        
        # Bin
        features = bin_spectrum(mz, intensity)
        
        # Stats
        stats = f"""
        PREPROCESSING STATS
        ═══════════════════════════════════
        mz range:        {mz.min():.1f} - {mz.max():.1f} Da
        intensity sum:   {intensity.sum():.6f}
        intensity max:   {intensity.max():.8f}
        
        FEATURE VECTOR STATS
        ═══════════════════════════════════
        non-zero bins:   {(features > 0).sum()} / 6000
        feature sum:     {features.sum():.6f}
        feature max:     {features.max():.6f}
        feature mean:    {features[features > 0].mean():.6f}
        
        RAW PREDICTION
        ═══════════════════════════════════
        prob susceptible: {model.predict_proba(features.reshape(1,-1))[0][0]:.4f}
        prob resistant:   {model.predict_proba(features.reshape(1,-1))[0][1]:.4f}
        """
        
        return stats
    
    except Exception as e:
        return f"Error: {str(e)}"


# Add a second tab to your interface temporarily
with gr.Blocks() as demo:
    with gr.Tab("Predict"):
        gr.Interface(
            fn=process_spectrum_file,
            inputs=gr.File(label="Upload .mzXML"),
            outputs=[
                gr.Textbox(label="Result", lines=14),
                gr.Plot(label="Spectrum")
            ]
        )
    with gr.Tab("Debug"):
        gr.Interface(
            fn=debug_feature_vector,
            inputs=gr.File(label="Upload .mzXML for debugging"),
            outputs=gr.Textbox(label="Feature Vector Stats", lines=20)
        )

demo.launch(server_name="0.0.0.0", server_port=7860)


interface = gr.Interface(
    fn=process_spectrum_file,
    inputs=gr.File(label="Upload MALDI-TOF spectrum (.mzXML)"),
    outputs=[
        gr.Textbox(label="Prediction Result", lines=14),
        gr.Plot(label="Spectrum and Probabilities")
    ],
    title="K. pneumo Cefotaxime Resistance Predictor",
    description="Upload a raw mzXML file for your strain of Klebsiella pneumoniae. R preprocessing runs automatically."
)

# Must use 0.0.0.0 inside Docker
interface.launch(server_name="0.0.0.0", server_port=7860)
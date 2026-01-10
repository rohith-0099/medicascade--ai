#!/bin/bash
# Setup MedSAM for medical image analysis

echo "🔬 Setting up MedSAM Medical Image Analyzer"
echo "============================================"
echo ""

cd /home/rohith/medicascade-ai/backend

# Create models directory
mkdir -p models
cd models

# Check if model already exists
if [ -f "medsam_vit_b.pth" ]; then
    echo "✅ MedSAM model already downloaded"
else
    echo "📥 Downloading MedSAM model weights (~2.4GB)..."
    echo "   This may take 5-10 minutes depending on your connection..."
    
    # Download from Zenodo
    wget https://zenodo.org/record/8014138/files/medsam_vit_b.pth \
        -O medsam_vit_b.pth \
        --progress=bar:force:noscroll
    
    if [ $? -eq 0 ]; then
        echo "✅ Model downloaded successfully!"
    else
        echo "❌ Download failed. Try manual download:"
        echo "   https://zenodo.org/record/8014138/files/medsam_vit_b.pth"
        exit 1
    fi
fi

# Install dependencies
echo ""
echo "📦 Installing MedSAM dependencies..."
cd /home/rohith/medicascade-ai/backend
source venv/bin/activate

pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install git+https://github.com/facebookresearch/segment-anything.git
pip install monai

echo ""
echo "============================================"
echo "✅ MedSAM setup complete!"
echo ""
echo "Model location: $(pwd)/models/medsam_vit_b.pth"
echo ""
echo "Test it:"
echo "  python -c 'from utils.medsam_analyzer import get_medsam_analyzer; get_medsam_analyzer()'"
echo "============================================"

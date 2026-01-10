#!/bin/bash
# Test if image detection is working

cd /home/rohith/medicascade-ai/backend
source venv/bin/activate

echo "🧪 Testing Medical Image Detection System"
echo "=========================================="
echo ""

# Test the analyzer directly
python -c "
from utils.medsam_analyzer import get_medsam_analyzer
import os

analyzer = get_medsam_analyzer()
print(f'✅ Analyzer loaded: {analyzer}')

# Test with stroke CT if it exists
test_image = '../demo/stroke_patient.pdf'
if os.path.exists(test_image):
    print(f'📄 Test file found: {test_image}')
else:
    print(f'⚠️  Test file not found')

print('')
print('If you see this, the detection system is loaded!')
"

echo ""
echo "=========================================="
echo "Now restart backend:"
echo "  ./start.sh"
echo "=========================================="

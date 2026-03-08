# 🚀 5-MINUTE DEPLOYMENT GUIDE

## Complete MediCascade 3D Setup - Copy & Paste Commands

---

## ✅ BACKEND (2 minutes)

```bash
# 1. Go to your backend folder
cd medicascade-backend

# 2. Install dependencies
pip install fastapi uvicorn python-multipart nibabel numpy scipy scikit-image

# 3. Place backend_3d_api.py in this folder

# 4. Start server
python backend_3d_api.py

# ✅ Should see: "Starting server on http://localhost:8000"
```

---

## ✅ FRONTEND - THREE.JS VERSION (2 minutes)

```bash
# 1. Go to your React app
cd medicascade-frontend

# 2. Install Three.js
npm install three

# 3. Place Brain3DViewer.jsx in src/components/

# 4. Add to your app (edit src/App.jsx):
```

```jsx
import Brain3DViewer from './components/Brain3DViewer';

export default function App() {
  return <Brain3DViewer />;
}
```

```bash
# 5. Start app
npm start

# ✅ Should open: http://localhost:3000
```

---

## ✅ TEST (1 minute)

1. Click "Choose Files" button
2. Upload BOTH files:
   - `*_flair.nii.gz`
   - `*_seg.nii.gz`
3. Wait 60-90 seconds
4. **BOOM!** 3D brain appears!

**Controls:**
- Drag = Rotate 360°
- Scroll = Zoom
- Right-drag = Pan

---

## 🎯 EXPECTED RESULT

```
🧠 Blue brain shell (translucent)
   ├─ 🟡 Yellow edema inside
   ├─ 🔴 Red necrotic core
   └─ 🟠 Orange enhancing tumor

📊 Volume stats panel (bottom-right)
🎮 Control panel (top-right)
```

---

## 🔧 QUICK FIXES

### CORS Error?
```python
# In backend_3d_api.py:
allow_origins=["http://localhost:3000"]  # Add your port
```

### Missing Dependencies?
```bash
pip install nibabel scipy scikit-image numpy
```

### Still Bumpy?
```python
# In backend_3d_api.py, line 265:
gaussian_sigma = 5.0,         # Increase
laplacian_iterations = 25,    # Increase
```

---

## ✅ SUCCESS CHECKLIST

- [ ] Backend shows "server running" message
- [ ] Frontend loads without errors
- [ ] Upload works
- [ ] 3D brain renders
- [ ] Can rotate smoothly
- [ ] Volumes display

**DONE!** 🎉 Your 3D brain viewer is live!

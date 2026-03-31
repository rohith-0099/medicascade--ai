I have hidden the "3D Brain MRI Viewer" from the sidebar by commenting it out in the frontend code.

How to re-enable the MRI option:
Open the file: 

frontend/src/App.jsx
Find the commented-out block near line 205 (inside the <aside className="sidebar"> section):
javascript
{/* 
<div style={{ borderTop: '1px solid var(--border)', marginTop: 14, paddingTop: 14 }}>
  <div className="sidebar-section">Viewers</div>
  <div className="sidebar-item" onClick={() => setViewMode('mri')} style={{ cursor: 'pointer' }}>
    <span style={{ color: 'var(--accent)' }}>&#9672;</span>
    <span>3D Brain MRI Viewer</span>
  </div>
</div>
*/}
Remove the {/* and */} markers to un-comment the block.
Save the file, and the MRI option will reappear in the sidebar.
import React, { useState, useRef, useCallback } from "react";
import {
  Box, Button, Chip, CircularProgress, Grid, Paper, Stack,
  Typography, Alert,
} from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import SearchIcon from "@mui/icons-material/Search";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CancelIcon from "@mui/icons-material/Cancel";
import WarningIcon from "@mui/icons-material/Warning";
import { analyzeDefects } from "../services/defectApi";

const STATUS_CONFIG = {
  PASS: { color: "success", icon: <CheckCircleIcon /> },
  FAIL: { color: "error", icon: <CancelIcon /> },
  REVIEW: { color: "warning", icon: <WarningIcon /> },
};

export default function AnalyzePage() {
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);
  const fileRef = useRef(null);

  const handleFile = useCallback((file) => {
    if (!file) return;
    setError(null); setResult(null);
    fileRef.current = file;
    setPreview(URL.createObjectURL(file));
  }, []);

  const handleDrop = (e) => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files?.[0]); };

  const handleAnalyze = async () => {
    if (!fileRef.current) return;
    setLoading(true); setError(null);
    try {
      const fd = new FormData();
      fd.append("file", fileRef.current);
      const { data } = await analyzeDefects(fd);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Analysis failed.");
    } finally {
      setLoading(false);
    }
  };

  const statusCfg = result ? STATUS_CONFIG[result.quality_status] || STATUS_CONFIG.REVIEW : null;

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={5}>
        <Paper elevation={3} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>Upload Product Image</Typography>
          <Box
            onDrop={handleDrop} onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)} onClick={() => inputRef.current?.click()}
            sx={{
              border: "2px dashed", borderColor: dragging ? "error.main" : "grey.400",
              borderRadius: 2, p: 4, textAlign: "center", cursor: "pointer",
              bgcolor: dragging ? "error.50" : "grey.50", minHeight: 160,
              display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
            }}
          >
            <CloudUploadIcon sx={{ fontSize: 48, color: "error.main", mb: 1 }} />
            <Typography variant="body1" fontWeight={500}>Drag & drop or click to upload</Typography>
            <Typography variant="caption" color="text.disabled" mt={1}>JPG, PNG, BMP, WebP</Typography>
          </Box>
          <input ref={inputRef} type="file" accept="image/*" style={{ display: "none" }} onChange={(e) => handleFile(e.target.files?.[0])} />
          {preview && (
            <Box mt={2} textAlign="center">
              <img src={preview} alt="preview" style={{ maxWidth: "100%", maxHeight: 200, borderRadius: 8, border: "1px solid #e0e0e0" }} />
            </Box>
          )}
          {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
          <Stack direction="row" spacing={1.5} mt={2}>
            <Button variant="contained" color="error" fullWidth onClick={handleAnalyze} disabled={!preview || loading}
              startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <SearchIcon />}>
              {loading ? "Analyzing…" : "Analyze Defects"}
            </Button>
            <Button variant="outlined" onClick={() => { setPreview(null); setResult(null); fileRef.current = null; }} disabled={loading}>Reset</Button>
          </Stack>
        </Paper>
      </Grid>
      <Grid item xs={12} md={7}>
        <Paper elevation={3} sx={{ p: 3, minHeight: 300 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>Analysis Results</Typography>
          {!result && !loading && (
            <Box display="flex" alignItems="center" justifyContent="center" minHeight={240} color="text.disabled">
              <Typography variant="body2">Upload an image and click "Analyze Defects".</Typography>
            </Box>
          )}
          {loading && (
            <Box display="flex" alignItems="center" justifyContent="center" minHeight={240}>
              <Stack alignItems="center" spacing={2}>
                <CircularProgress size={48} color="error" />
                <Typography variant="body2" color="text.secondary">Scanning for defects…</Typography>
              </Stack>
            </Box>
          )}
          {result && !loading && (
            <>
              <Stack direction="row" flexWrap="wrap" gap={1} mb={2}>
                <Chip icon={statusCfg.icon} label={`Quality: ${result.quality_status}`} color={statusCfg.color} variant="filled" sx={{ fontWeight: 700 }} />
                <Chip label={`Defects: ${result.total}`} color="default" variant="outlined" />
                {Object.entries(result.severity_summary || {}).map(([sev, cnt]) => (
                  <Chip key={sev} label={`${sev}: ${cnt}`} variant="outlined" size="small" />
                ))}
              </Stack>
              {result.annotated_image && (
                <Box textAlign="center">
                  <img src={`data:image/jpeg;base64,${result.annotated_image}`} alt="annotated"
                    style={{ maxWidth: "100%", borderRadius: 8, border: "1px solid #e0e0e0" }} />
                  <Typography variant="caption" display="block" color="text.secondary" mt={0.5}>
                    {result.image_width} × {result.image_height} px
                  </Typography>
                </Box>
              )}
            </>
          )}
        </Paper>
      </Grid>
    </Grid>
  );
}

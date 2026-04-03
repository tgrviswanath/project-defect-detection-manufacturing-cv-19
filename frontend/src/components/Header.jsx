import React from "react";
import { AppBar, Toolbar, Typography } from "@mui/material";
import PrecisionManufacturingIcon from "@mui/icons-material/PrecisionManufacturing";

export default function Header() {
  return (
    <AppBar position="static" color="error">
      <Toolbar>
        <PrecisionManufacturingIcon sx={{ mr: 1 }} />
        <Typography variant="h6" fontWeight="bold">Manufacturing Defect Detection</Typography>
      </Toolbar>
    </AppBar>
  );
}

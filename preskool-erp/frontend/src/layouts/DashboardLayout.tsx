import { PropsWithChildren } from "react";
import { AppBar, Box, CssBaseline, Drawer, List, ListItemButton, ListItemText, Toolbar, Typography } from "@mui/material";
import { Link, useLocation } from "react-router-dom";

export interface NavItem {
  label: string;
  path: string;
}

export default function DashboardLayout({ children, items, title }: PropsWithChildren<{ items: NavItem[]; title: string }>) {
  const location = useLocation();
  return (
    <Box sx={{ display: "flex", minHeight: "100vh", bgcolor: "#f4f7fb" }}>
      <CssBaseline />
      <AppBar position="fixed" sx={{ bgcolor: "#3D5EE1", backgroundImage: "linear-gradient(90deg, #3D5EE1, #10b981)" }}>
        <Toolbar>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>{title}</Typography>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: 260,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: 260, boxSizing: "border-box", mt: 8, borderRight: 0, bgcolor: "#0f172a", color: "#fff" },
        }}
      >
        <List>
          {items.map((item) => (
            <ListItemButton
              component={Link}
              to={item.path}
              selected={location.pathname === item.path}
              key={item.path}
              sx={{ borderRadius: 2, mx: 1, my: 0.5 }}
            >
              <ListItemText primary={item.label} />
            </ListItemButton>
          ))}
        </List>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 4, mt: 8, ml: "260px" }}>
        {children}
      </Box>
    </Box>
  );
}

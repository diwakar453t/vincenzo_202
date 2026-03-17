import { FormEvent, useState } from "react";
import { Alert, Box, Button, Card, CardContent, Stack, TextField, Typography } from "@mui/material";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { roleDashboard } from "../components/auth/RoleProtectedRoute";
import { login } from "../store/slices/authSlice";
import type { AppDispatch, RootState } from "../store/store";

export default function LoginPage() {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@preskool.com");
  const [password, setPassword] = useState("Admin@1234");
  const auth = useSelector((state: RootState) => state.auth);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const result = await dispatch(login({ email, password }));
    if (login.fulfilled.match(result)) {
      navigate(roleDashboard(result.payload.role));
    }
  }

  return (
    <Box sx={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "radial-gradient(circle at top, #dbeafe, #f8fafc 55%)" }}>
      <Card sx={{ width: 420, borderRadius: 4, boxShadow: "0 25px 60px rgba(15,23,42,0.12)" }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>PreSkool ERP</Typography>
          <Typography color="text.secondary" sx={{ mb: 3 }}>Production-ready multi-tenant school operations</Typography>
          <Box component="form" onSubmit={handleSubmit}>
            <Stack spacing={2}>
              {auth.error && <Alert severity="error">{auth.error}</Alert>}
              <TextField label="Email" value={email} onChange={(event) => setEmail(event.target.value)} />
              <TextField label="Password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
              <Button type="submit" variant="contained" size="large">Sign in</Button>
            </Stack>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}

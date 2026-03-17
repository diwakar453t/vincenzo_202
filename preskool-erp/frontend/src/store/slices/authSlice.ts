import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import api from "../../services/api";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  tenant_id: string;
}

interface AuthState {
  user: User | null;
  status: "idle" | "loading" | "failed";
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  status: "idle",
  error: null,
};

export const login = createAsyncThunk("auth/login", async (payload: { email: string; password: string }) => {
  const response = await api.post("/auth/login", payload);
  localStorage.setItem("access_token", response.data.access_token);
  localStorage.setItem("refresh_token", response.data.refresh_token);
  localStorage.setItem("user", JSON.stringify(response.data.user));
  return response.data.user as User;
});

export const register = createAsyncThunk("auth/register", async (payload: Record<string, unknown>) => {
  const response = await api.post("/auth/register", payload);
  return response.data as User;
});

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    hydrateUser: (state) => {
      const raw = localStorage.getItem("user");
      state.user = raw ? JSON.parse(raw) : null;
    },
    logout: (state) => {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user");
      state.user = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.status = "loading";
      })
      .addCase(login.fulfilled, (state, action) => {
        state.status = "idle";
        state.user = action.payload;
      })
      .addCase(login.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message ?? "Login failed";
      });
  },
});

export const { hydrateUser, logout } = authSlice.actions;
export default authSlice.reducer;

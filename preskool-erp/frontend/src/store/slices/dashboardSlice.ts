import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import api from "../../services/api";

export const fetchDashboardStatistics = createAsyncThunk("dashboard/fetchStatistics", async () => {
  const response = await api.get("/dashboard/statistics");
  return response.data;
});

const dashboardSlice = createSlice({
  name: "dashboard",
  initialState: { stats: null as Record<string, number> | null, status: "idle" as string },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboardStatistics.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchDashboardStatistics.fulfilled, (state, action) => {
        state.status = "idle";
        state.stats = action.payload;
      })
      .addCase(fetchDashboardStatistics.rejected, (state) => {
        state.status = "failed";
      });
  },
});

export default dashboardSlice.reducer;
